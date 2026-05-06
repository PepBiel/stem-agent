from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from stem_agent.core.config import load_yaml
from stem_agent.core.genome import validate_genome_files


@dataclass(frozen=True)
class EvolutionProposalInput:
    run_dir: Path
    base_genome_path: Path
    schema_path: Path
    output_dir: Path
    candidate_id: str | None = None
    dry_run: bool = False


def propose_evolution(input_data: EvolutionProposalInput) -> dict[str, Any]:
    """Create a controlled next-genome proposal from saved evaluation artifacts.

    The proposal is intentionally deterministic and human-in-the-loop. It reads
    prior traces, judge outputs, and heuristic scores, then writes:

    - a Markdown diagnosis and proposed evolution round
    - a candidate YAML genome proposal that still must be reviewed, validated,
      and evaluated before acceptance
    """

    run_dir = input_data.run_dir
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing run summary: {summary_path}")

    summary = load_json(summary_path)
    base_genome = load_yaml(input_data.base_genome_path)
    question_rows = collect_question_rows(summary, run_dir)
    diagnosis = diagnose(question_rows, summary)
    candidate = build_candidate_genome(
        base_genome=base_genome,
        base_genome_path=input_data.base_genome_path,
        schema_path=input_data.schema_path,
        run_dir=run_dir,
        diagnosis=diagnosis,
        candidate_id=input_data.candidate_id,
    )

    validation = validate_candidate(
        candidate=candidate,
        output_dir=input_data.output_dir,
        schema_path=input_data.schema_path,
        dry_run=input_data.dry_run,
    )
    proposal_markdown = render_proposal_markdown(
        summary=summary,
        base_genome_path=input_data.base_genome_path,
        schema_path=input_data.schema_path,
        run_dir=run_dir,
        output_dir=input_data.output_dir,
        candidate=candidate,
        diagnosis=diagnosis,
        question_rows=question_rows,
        validation=validation,
        dry_run=input_data.dry_run,
    )

    proposal_path = input_data.output_dir / "proposal.md"
    candidate_path = input_data.output_dir / "candidate_genome.yaml"

    if not input_data.dry_run:
        input_data.output_dir.mkdir(parents=True, exist_ok=True)
        proposal_path.write_text(proposal_markdown, encoding="utf-8")
        candidate_path.write_text(
            yaml.safe_dump(candidate, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
        )

    return {
        "run_id": summary.get("run_id"),
        "base_genome": str(input_data.base_genome_path),
        "candidate_id": candidate["genome"]["id"],
        "output_dir": str(input_data.output_dir),
        "proposal_path": str(proposal_path),
        "candidate_path": str(candidate_path),
        "dry_run": input_data.dry_run,
        "diagnosis": diagnosis,
        "validation": validation,
    }


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def collect_question_rows(
    summary: dict[str, Any],
    run_dir: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for item in summary.get("questions", []):
        if not isinstance(item, dict):
            continue

        question_id = str(item.get("question_id", "unknown"))
        judge_path = run_dir / "judge" / f"{question_id}.json"
        heuristic_path = run_dir / "heuristic" / f"{question_id}.json"
        trace_path = run_dir / "traces" / f"{question_id}.json"

        judge = load_json(judge_path) if judge_path.exists() else {}
        heuristic = load_json(heuristic_path) if heuristic_path.exists() else {}
        trace = load_json(trace_path) if trace_path.exists() else {}

        judge_eval = mapping(judge.get("judge_evaluation"))
        heuristic_eval = mapping(judge.get("heuristic_evaluation")) or heuristic
        metrics = mapping(heuristic_eval.get("metrics"))

        row = {
            "question_id": question_id,
            "final_score": float_or_none(item.get("final_score")),
            "judge_score": float_or_none(item.get("judge_score")),
            "heuristic_score": float_or_none(item.get("heuristic_score")),
            "summary": str(item.get("summary") or judge_eval.get("summary") or ""),
            "recommended_fix": str(
                item.get("recommended_fix") or judge_eval.get("recommended_fix") or ""
            ),
            "judge_failure_tags": string_list(judge_eval.get("failure_tags")),
            "heuristic_failure_tags": string_list(heuristic_eval.get("failure_tags")),
            "coverage_score": float_or_none(metrics.get("coverage_score")),
            "citation_support_score": float_or_none(
                metrics.get("citation_support_score")
            ),
            "source_quality_score": float_or_none(metrics.get("source_quality_score")),
            "unsupported_claim_count": int_or_zero(
                metrics.get("unsupported_claim_count")
            ),
            "status": trace.get("status"),
            "citation_contract_warnings": string_list(
                trace.get("citation_contract_warnings")
            ),
            "parse_warning": trace.get("status") == "complete_with_parse_warning"
            or any(
                mapping(event).get("name") == "parse_warning"
                for event in list_value(trace.get("events"))
            ),
        }
        rows.append(row)

    return rows


def diagnose(
    question_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    tag_counts: Counter[str] = Counter()
    recommendation_counts: Counter[str] = Counter()
    recurring_themes: set[str] = set()

    low_judge = []
    low_source_quality = []
    unsupported = []
    parse_warnings = []
    citation_warnings = []

    for row in question_rows:
        tag_counts.update(row["judge_failure_tags"])
        tag_counts.update(row["heuristic_failure_tags"])

        text = f"{row['summary']} {row['recommended_fix']}".lower()
        for theme, patterns in THEME_PATTERNS.items():
            if any(pattern in text for pattern in patterns):
                recurring_themes.add(theme)
                recommendation_counts[theme] += 1

        if (row["judge_score"] or 0.0) < 0.8:
            low_judge.append(row["question_id"])
        if (row["source_quality_score"] or 0.0) < 0.7:
            low_source_quality.append(row["question_id"])
        if row["unsupported_claim_count"] > 0:
            unsupported.append(row["question_id"])
        if row["parse_warning"]:
            parse_warnings.append(row["question_id"])
        if row["citation_contract_warnings"]:
            citation_warnings.append(row["question_id"])

    aggregate = mapping(summary.get("aggregate"))
    usage_totals = mapping(summary.get("usage_totals"))
    combined_usage = mapping(usage_totals.get("combined"))

    recommendations = select_recommendations(
        themes=recurring_themes,
        tag_counts=tag_counts,
        low_source_quality=low_source_quality,
        unsupported=unsupported,
        parse_warnings=parse_warnings,
        citation_warnings=citation_warnings,
    )

    return {
        "aggregate": {
            "heuristic_score_avg": aggregate.get("heuristic_score_avg"),
            "judge_score_avg": aggregate.get("judge_score_avg"),
            "final_score_avg": aggregate.get("final_score_avg"),
            "combined_total_tokens": combined_usage.get("total_tokens"),
        },
        "failure_tag_counts": dict(sorted(tag_counts.items())),
        "theme_counts": dict(sorted(recommendation_counts.items())),
        "low_judge_questions": low_judge,
        "low_source_quality_questions": low_source_quality,
        "unsupported_claim_questions": unsupported,
        "parse_warning_questions": parse_warnings,
        "citation_warning_questions": citation_warnings,
        "recommendations": recommendations,
    }


THEME_PATTERNS = {
    "source_specificity": [
        "source-specific",
        "specific source",
        "specific passage",
        "specific finding",
        "directly relevant",
        "directly supported",
    ],
    "inference_labeling": [
        "inference",
        "inferred",
        "recommendation",
        "synthesis",
        "directly supported facts",
    ],
    "weak_source_discipline": [
        "weak source",
        "vendor documentation",
        "blog source",
        "generic",
        "source mix",
    ],
    "cost_grounding": [
        "cost",
        "latency",
        "token",
        "cheaper",
        "workflow can be cheaper",
    ],
    "citation_contract": [
        "citation",
        "unsupported",
        "raw url",
        "claim",
    ],
    "failure_examples": [
        "failure mode",
        "concrete example",
        "trade-off",
        "tradeoff",
    ],
}


def select_recommendations(
    *,
    themes: set[str],
    tag_counts: Counter[str],
    low_source_quality: list[str],
    unsupported: list[str],
    parse_warnings: list[str],
    citation_warnings: list[str],
) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []

    if "source_specificity" in themes or low_source_quality:
        recommendations.append(
            {
                "id": "source_specificity_gate",
                "title": "Add a source-specific evidence gate",
                "change": (
                    "Require each evidence-table item to name the exact source "
                    "finding, metric, or documented behavior it supports."
                ),
            }
        )

    if "inference_labeling" in themes:
        recommendations.append(
            {
                "id": "inference_budget",
                "title": "Separate direct evidence from engineering inference",
                "change": (
                    "Limit recommendation-style claims unless they explicitly "
                    "cite the source facts they are inferred from."
                ),
            }
        )

    if "weak_source_discipline" in themes or tag_counts.get("weak_source", 0) > 0:
        recommendations.append(
            {
                "id": "authoritative_source_floor",
                "title": "Raise the authoritative-source floor",
                "change": (
                    "Prefer papers, official docs, and benchmark pages; allow "
                    "vendor/blog sources only when no primary source covers the "
                    "same claim."
                ),
            }
        )

    if "cost_grounding" in themes:
        recommendations.append(
            {
                "id": "cost_claim_support",
                "title": "Require direct support for cost and latency claims",
                "change": (
                    "Treat cost, latency, and token-efficiency claims as "
                    "high-risk claims requiring a directly cited metric or a "
                    "clearly labeled mechanism-level inference."
                ),
            }
        )

    if "failure_examples" in themes:
        recommendations.append(
            {
                "id": "failure_mode_examples",
                "title": "Ground failure modes in concrete examples",
                "change": (
                    "Ask the answer to provide one sourced example for each "
                    "named failure mode or explicitly label it as a hypothetical "
                    "engineering risk."
                ),
            }
        )

    if unsupported or citation_warnings:
        recommendations.append(
            {
                "id": "citation_contract_repair",
                "title": "Keep the raw-URL citation contract as a rejection gate",
                "change": (
                    "Reject candidate answers with unsupported claim lines, "
                    "provider citation markers, or rejected-source leakage."
                ),
            }
        )

    if parse_warnings:
        recommendations.append(
            {
                "id": "structured_output_repair",
                "title": "Keep tolerant JSON recovery and structured-output checks",
                "change": (
                    "Recover valid leading JSON objects, then warn when the "
                    "model output still violates the citation contract."
                ),
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "id": "freeze_candidate",
                "title": "Freeze the current genome",
                "change": (
                    "No recurring blocking failure was detected. Keep the "
                    "current genome and move to held-out evaluation or manual "
                    "review instead of another live tuning loop."
                ),
            }
        )

    return recommendations


def build_candidate_genome(
    *,
    base_genome: dict[str, Any],
    base_genome_path: Path,
    schema_path: Path,
    run_dir: Path,
    diagnosis: dict[str, Any],
    candidate_id: str | None,
) -> dict[str, Any]:
    candidate = json.loads(json.dumps(base_genome))
    genome_meta = mapping(candidate.setdefault("genome", {}))
    old_id = str(genome_meta.get("id", "evolved_deep_research"))
    old_version = int_or_zero(genome_meta.get("version"))
    next_version = old_version + 1 if old_version else 1
    new_id = candidate_id or re.sub(r"_v\d+$", f"_v{next_version}", old_id)
    if new_id == old_id:
        new_id = f"{old_id}_proposal"

    genome_meta.update(
        {
            "id": new_id,
            "version": next_version,
            "parent": relative_to_project(base_genome_path),
            "schema": relative_to_project(schema_path),
            "evolution_stage": "auto_proposed_candidate",
            "hypothesis": build_hypothesis(diagnosis),
            "tuning_notes": (
                "Generated by `python -m stem_agent evolve` from saved run "
                "artifacts. This is a proposal only: it must pass schema "
                "validation, smoke testing, and fixed-set evaluation before "
                "being accepted."
            ),
            "derived_from_failure_modes": [
                item["id"] for item in diagnosis["recommendations"]
            ],
        }
    )

    agent = mapping(candidate.setdefault("agent", {}))
    agent["type"] = new_id
    agent["description"] = (
        "Auto-proposed next genome candidate generated from prior evaluation "
        "traces. It tightens evidence grounding while preserving the same tool "
        "boundary and safety constraints."
    )

    source_policy = mapping(candidate.setdefault("source_quality_policy", {}))
    require_direct_support = source_policy.setdefault("require_direct_support_for", [])
    if isinstance(require_direct_support, list):
        append_unique(require_direct_support, "synthesis and recommendation claims")
        append_unique(require_direct_support, "cost and latency mechanism claims")
        append_unique(require_direct_support, "named failure-mode examples")
    source_policy["minimum_authoritative_sources"] = max(
        int_or_zero(source_policy.get("minimum_authoritative_sources")),
        5,
    )
    source_policy["proposal_source_specificity_gate"] = (
        "Each evidence row should identify the exact finding, metric, or "
        "documented behavior that supports the claim. Broad topical relevance "
        "is not enough."
    )

    output_contract = mapping(candidate.setdefault("output_contract", {}))
    required_props = output_contract.setdefault("required_answer_properties", [])
    if isinstance(required_props, list):
        append_unique(required_props, "source_specific_evidence_for_recommendations")
        append_unique(required_props, "cost_latency_claims_grounded_or_labeled")
        append_unique(required_props, "failure_modes_have_examples_or_uncertainty")

    safeguards = mapping(candidate.setdefault("safeguards", {}))
    safeguards["require_source_specific_evidence"] = True
    safeguards["require_cost_latency_claim_support"] = True
    safeguards["require_failure_mode_examples_or_uncertainty"] = True

    acceptance = mapping(candidate.setdefault("acceptance_criteria", {}))
    accept_if = mapping(acceptance.setdefault("accept_if", {}))
    accept_if["source_quality_score_delta_vs_parent_min"] = 0.0
    accept_if["unsupported_claim_count_delta_vs_parent_max"] = 0
    reject_if = acceptance.setdefault("reject_if", [])
    if isinstance(reject_if, list):
        append_unique(reject_if, "source_specificity_regression")
        append_unique(reject_if, "unlabeled_inference_regression")

    rollback = mapping(candidate.setdefault("rollback", {}))
    rollback["previous_best"] = relative_to_project(base_genome_path)

    return candidate


def build_hypothesis(diagnosis: dict[str, Any]) -> str:
    recommendation_titles = [
        item["title"] for item in diagnosis.get("recommendations", [])
    ]
    if not recommendation_titles:
        return "No material change proposed; keep the current genome."
    joined = "; ".join(recommendation_titles)
    return (
        "Prior evaluation artifacts show remaining weaknesses around "
        f"{joined}. The next genome should preserve the current workflow and "
        "tool boundary while tightening evidence grounding and acceptance gates."
    )


def validate_candidate(
    *,
    candidate: dict[str, Any],
    output_dir: Path,
    schema_path: Path,
    dry_run: bool,
) -> dict[str, Any]:
    candidate_path = output_dir / "candidate_genome.yaml"
    if dry_run:
        return {
            "attempted": False,
            "valid": None,
            "errors": [],
            "warnings": [],
            "reason": "dry_run",
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(
        yaml.safe_dump(candidate, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )
    result = validate_genome_files(genome_path=candidate_path, schema_path=schema_path)
    return {
        "attempted": True,
        "valid": result.valid,
        "errors": result.errors,
        "warnings": result.warnings,
    }


def render_proposal_markdown(
    *,
    summary: dict[str, Any],
    base_genome_path: Path,
    schema_path: Path,
    run_dir: Path,
    output_dir: Path,
    candidate: dict[str, Any],
    diagnosis: dict[str, Any],
    question_rows: list[dict[str, Any]],
    validation: dict[str, Any],
    dry_run: bool,
) -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    candidate_id = candidate["genome"]["id"]
    aggregate = diagnosis["aggregate"]

    lines = [
        f"# Evolution Proposal: {candidate_id}",
        "",
        f"Generated at: `{now}`",
        f"Source run: `{relative_to_project(run_dir)}`",
        f"Base genome: `{relative_to_project(base_genome_path)}`",
        f"Schema: `{relative_to_project(schema_path)}`",
        f"Dry run: `{dry_run}`",
        "",
        "## Aggregate Signals",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Heuristic avg | {aggregate.get('heuristic_score_avg')} |",
        f"| Judge avg | {aggregate.get('judge_score_avg')} |",
        f"| Final avg | {aggregate.get('final_score_avg')} |",
        f"| Combined tokens | {aggregate.get('combined_total_tokens')} |",
        "",
        "## Per-Question Signals",
        "",
        "| Question | Heuristic | Judge | Final | Tags | Recommended fix |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in question_rows:
        tags = sorted(set(row["judge_failure_tags"] + row["heuristic_failure_tags"]))
        lines.append(
            "| {question_id} | {heuristic_score} | {judge_score} | {final_score} | "
            "{tags} | {recommended_fix} |".format(
                question_id=row["question_id"],
                heuristic_score=format_float(row["heuristic_score"]),
                judge_score=format_float(row["judge_score"]),
                final_score=format_float(row["final_score"]),
                tags=", ".join(tags) or "none",
                recommended_fix=escape_table_text(row["recommended_fix"]),
            )
        )

    lines.extend(
        [
            "",
            "## Diagnosed Failure Modes",
            "",
            f"- Failure tag counts: `{diagnosis['failure_tag_counts']}`",
            f"- Theme counts: `{diagnosis['theme_counts']}`",
            f"- Low judge questions: `{diagnosis['low_judge_questions']}`",
            f"- Low source-quality questions: `{diagnosis['low_source_quality_questions']}`",
            f"- Unsupported-claim questions: `{diagnosis['unsupported_claim_questions']}`",
            f"- Parse-warning questions: `{diagnosis['parse_warning_questions']}`",
            f"- Citation-warning questions: `{diagnosis['citation_warning_questions']}`",
            "",
            "## Proposed Genome Changes",
            "",
        ]
    )
    for item in diagnosis["recommendations"]:
        lines.extend(
            [
                f"### {item['title']}",
                "",
                f"- Proposal id: `{item['id']}`",
                f"- Change: {item['change']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Safeguards",
            "",
            "- The proposal preserves the existing tool boundary: web search only.",
            "- It does not apply itself automatically.",
            "- The candidate genome must pass schema validation.",
            "- A smoke run should pass before any live batch.",
            "- Acceptance still depends on fixed-set evaluation against the parent.",
            "",
            "## Validation",
            "",
            f"- Attempted: `{validation['attempted']}`",
            f"- Valid: `{validation['valid']}`",
            f"- Errors: `{validation['errors']}`",
            f"- Warnings: `{validation['warnings']}`",
            "",
            "## Expected Artifacts",
            "",
            f"- Proposal: `{relative_to_project(output_dir / 'proposal.md')}`",
            f"- Candidate genome: `{relative_to_project(output_dir / 'candidate_genome.yaml')}`",
            "",
            "## Next Step",
            "",
            "Review the candidate genome manually. If the proposal is accepted, copy or "
            "promote it into `configs/`, run `validate-genome`, run a dry-run smoke "
            "batch, and only then consider a live evaluation batch.",
            "",
        ]
    )
    return "\n".join(lines)


def mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def list_value(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def string_list(value: Any) -> list[str]:
    return [item for item in list_value(value) if isinstance(item, str)]


def float_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def int_or_zero(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def append_unique(items: list[Any], value: str) -> None:
    if value not in items:
        items.append(value)


def relative_to_project(path: Path) -> str:
    try:
        from stem_agent.core.paths import PROJECT_ROOT

        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def format_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4f}"


def escape_table_text(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()
