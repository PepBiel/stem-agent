from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import AuthenticationError, OpenAI, OpenAIError

from stem_agent.core.config import load_yaml, resolve_model
from stem_agent.core.genome import validate_genome_files
from stem_agent.core.openai_responses import (
    extract_citations,
    extract_output_text,
    extract_usage,
    extract_web_search_calls,
    response_to_dict,
)
from stem_agent.core.settings import Settings
from stem_agent.core.tracing import utc_now_iso, write_trace


@dataclass(frozen=True)
class EvolvedRunResult:
    answer: str
    trace_path: Path
    dry_run: bool


ARTIFACT_KEYS = [
    "decomposition",
    "search_plan",
    "candidate_sources",
    "source_triage",
    "evidence_table",
    "coverage_audit",
    "contradiction_audit",
    "citation_audit",
]

EVENT_ARTIFACTS = {
    "question_received": "question",
    "decomposition_created": "decomposition",
    "search_plan_created": "search_plan",
    "candidate_sources_collected": "candidate_sources",
    "sources_triaged": "source_triage",
    "evidence_extracted": "evidence_table",
    "coverage_checked": "coverage_audit",
    "contradictions_checked": "contradiction_audit",
    "answer_synthesized": "answer",
    "citations_audited": "citation_audit",
    "final_answer_returned": "answer",
}


def build_evolved_prompt(question: str, genome: dict[str, Any]) -> str:
    return build_evolved_prompt_with_context(
        question=question,
        genome=genome,
        required_aspects=[],
        source_expectations=[],
    )


def build_evolved_prompt_with_context(
    *,
    question: str,
    genome: dict[str, Any],
    required_aspects: list[str],
    source_expectations: list[str],
) -> str:
    limits = mapping(genome.get("limits"))
    workflow = string_list(genome.get("workflow"))
    requirements_block = ""
    if required_aspects or source_expectations:
        aspects_text = json.dumps(required_aspects, indent=2)
        source_expectations_text = json.dumps(source_expectations, indent=2)
        requirements_block = f"""
Fixed evaluation requirements:
- Required aspects to cover exactly:
{aspects_text}
- Expected source types:
{source_expectations_text}

Coverage rules:
- Copy every required aspect into `decomposition.required_aspects`.
- In `coverage_audit`, mark each required aspect as covered or missing.
- In the Answer section, include a compact "Required aspect coverage" subsection
  with one bullet for every required aspect.
- Every bullet in "Required aspect coverage" must include an inline URL.
- If an aspect lacks evidence, do not hide it. Put it in
  `coverage_audit.missing_aspects` and mention it in Limitations.
"""

    json_contract = """{
  "decomposition": {
    "subquestions": [],
    "required_aspects": [],
    "expected_source_types": []
  },
  "search_plan": {
    "queries": [],
    "rationale_per_query": []
  },
  "candidate_sources": [],
  "source_triage": {
    "accepted_sources": [],
    "rejected_sources": [],
    "rejection_reasons": []
  },
  "evidence_table": [
    {
      "claim": "",
      "source_url": "",
      "source_type": "",
      "supported_aspect": "",
      "confidence": "low|medium|high"
    }
  ],
  "coverage_audit": {
    "covered_aspects": [],
    "missing_aspects": [],
    "followup_needed": []
  },
  "contradiction_audit": {
    "conflicting_claims": [],
    "resolution": "",
    "uncertainty_notes": []
  },
  "citation_audit": {
    "supported_claims": [],
    "unsupported_claims": [],
    "weak_citations": []
  },
  "answer": "Markdown answer with sections: Answer, Sources, Limitations"
}"""

    return f"""You are executing the evolved_deep_research_v1 genome.

This is a controlled evaluation run. Return only one JSON object matching the
contract. Be concise: the goal is coverage with evidence, not a long survey.

Workflow:
{json.dumps(workflow, indent=2)}

Operational limits:
- Use at most {limits.get("max_search_queries", 4)} focused search queries.
- Use at most {limits.get("max_sources", 6)} accepted sources.
- Stop searching once the required aspects are covered by credible sources.
- Do not perform broad exploratory searches.
- Keep the final answer under 900 words.
- Prefer primary papers, official docs, benchmarks, and repositories.
- Reject weak or irrelevant sources with a reason.
- Do not make source-free key claims.
- Mention uncertainty when evidence is incomplete or conflicting.

{requirements_block}

Return valid JSON only. The `answer` field must be Markdown and must include
exactly these sections: Answer, Sources, Limitations. Important answer claims
must include inline URLs.

JSON contract:
{json_contract}

Question:
{question}
"""


def prompt_role_summary(genome: dict[str, Any]) -> str:
    roles = mapping(genome.get("prompt_roles"))
    lines: list[str] = []
    for name, role in roles.items():
        if not isinstance(role, dict):
            continue
        objective = str(role.get("objective", "")).strip()
        lines.append(f"- {name}: {objective}")
    return "\n".join(lines)


def build_dry_run_artifacts(
    question: str,
    required_aspects: list[str],
    source_expectations: list[str],
) -> dict[str, Any]:
    aspects = required_aspects or ["dry-run coverage placeholder"]
    expected_sources = source_expectations or ["papers", "official docs"]
    return {
        "decomposition": {
            "subquestions": [
                "What does the question require?",
                "Which aspects must be sourced?",
            ],
            "required_aspects": aspects,
            "expected_source_types": expected_sources,
        },
        "search_plan": {
            "queries": ["dry run query"],
            "rationale_per_query": ["Validate evolved runner wiring."],
        },
        "candidate_sources": [],
        "source_triage": {
            "accepted_sources": [],
            "rejected_sources": [],
            "rejection_reasons": [],
        },
        "evidence_table": [],
        "coverage_audit": {
            "covered_aspects": [],
            "missing_aspects": aspects,
            "followup_needed": ["Run without --dry-run for real research."],
        },
        "contradiction_audit": {
            "conflicting_claims": [],
            "resolution": "No live sources were inspected.",
            "uncertainty_notes": ["Dry-run does not validate factual claims."],
        },
        "citation_audit": {
            "supported_claims": [],
            "unsupported_claims": ["Dry-run placeholder answer."],
            "weak_citations": [],
        },
        "answer": f"""Answer
This is a dry-run evolved-agent response for: {question}

Sources
- No external sources were fetched because --dry-run was enabled.

Limitations
- This output validates genome loading, schema validation, workflow tracing, and
  CLI wiring. It is not an evaluated research answer.
""",
    }


def parse_json_object(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None

    for candidate in json_candidates(stripped):
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload

    return None


def json_candidates(text: str) -> list[str]:
    candidates = [text]
    fenced_blocks = re.findall(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    candidates.extend(block.strip() for block in fenced_blocks)

    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        candidates.append(text[first : last + 1])

    return candidates


def normalize_artifacts(payload: dict[str, Any] | None, raw_text: str) -> dict[str, Any]:
    if payload is None:
        return {
            **{key: empty_artifact(key) for key in ARTIFACT_KEYS},
            "answer": raw_text,
            "parse_warning": "Model output was not valid JSON.",
        }

    artifacts: dict[str, Any] = {}
    for key in ARTIFACT_KEYS:
        artifacts[key] = payload.get(key, empty_artifact(key))

    answer = payload.get("answer")
    artifacts["answer"] = answer if isinstance(answer, str) else raw_text
    return artifacts


def empty_artifact(key: str) -> Any:
    if key in {"candidate_sources", "evidence_table"}:
        return []
    return {}


def build_events(
    *,
    required_events: list[str],
    artifacts: dict[str, Any],
    question: str,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for event_name in required_events:
        artifact_key = EVENT_ARTIFACTS.get(event_name)
        if artifact_key == "question":
            artifact_present = bool(question)
        elif artifact_key:
            artifact_present = artifact_key in artifacts
        else:
            artifact_present = False

        events.append(
            {
                "name": event_name,
                "timestamp": utc_now_iso(),
                "artifact": artifact_key,
                "artifact_present": artifact_present,
            }
        )
    return events


def artifact_citations(artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    for url in artifact_urls(artifacts):
        citations.append({"type": "url_citation", "url": url, "title": ""})
    return citations


def artifact_urls(artifacts: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    collect_urls(artifacts, urls)
    return sorted(set(urls))


def collect_urls(value: Any, urls: list[str]) -> None:
    if isinstance(value, str):
        urls.extend(re.findall(r"https?://[^\s\])\",]+", value))
        return
    if isinstance(value, list):
        for item in value:
            collect_urls(item, urls)
        return
    if isinstance(value, dict):
        for item in value.values():
            collect_urls(item, urls)


def merge_citations(*citation_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for group in citation_groups:
        for citation in group:
            url = citation.get("url")
            if not isinstance(url, str) or url in seen:
                continue
            seen.add(url)
            merged.append(citation)
    return merged


def genome_version(genome: dict[str, Any]) -> int:
    raw_version = mapping(genome.get("genome")).get("version", 1)
    try:
        return int(raw_version)
    except (TypeError, ValueError):
        return 1


def run_evolved(
    *,
    question: str,
    genome_path: Path,
    schema_path: Path,
    trace_dir: Path,
    settings: Settings,
    dry_run: bool,
    question_metadata: dict[str, Any] | None = None,
) -> EvolvedRunResult:
    validation = validate_genome_files(genome_path=genome_path, schema_path=schema_path)
    if not validation.valid:
        raise RuntimeError(
            "Genome validation failed before evolved run: "
            + "; ".join(validation.errors)
        )

    genome = load_yaml(genome_path)
    inject_evaluation_requirements = genome_version(genome) >= 2
    if inject_evaluation_requirements:
        required_aspects = string_list(mapping(question_metadata).get("must_cover"))
        source_expectations = string_list(
            mapping(question_metadata).get("source_expectations")
        )
    else:
        required_aspects = []
        source_expectations = []
    model = resolve_model(genome, settings.openai_model)
    prompt = build_evolved_prompt_with_context(
        question=question,
        genome=genome,
        required_aspects=required_aspects,
        source_expectations=source_expectations,
    )
    agent_config = mapping(genome.get("agent"))
    genome_meta = mapping(genome.get("genome"))
    trace_config = mapping(genome.get("trace"))
    required_events = string_list(trace_config.get("required_events"))

    trace: dict[str, Any] = {
        "run_type": "evolved",
        "agent_type": agent_config.get("type"),
        "agent_id": agent_config.get("id"),
        "genome_id": genome_meta.get("id"),
        "genome_version": genome_meta.get("version"),
        "genome_path": str(genome_path),
        "schema_path": str(schema_path),
        "started_at": utc_now_iso(),
        "question": question,
        "model": model,
        "dry_run": dry_run,
        "workflow": genome.get("workflow", []),
        "tools_allowed": string_list(mapping(genome.get("tools")).get("allowed")),
        "limits": genome.get("limits", {}),
        "evaluation_requirements": {
            "required_aspects": required_aspects,
            "source_expectations": source_expectations,
        },
        "validation": {
            "valid": validation.valid,
            "warnings": validation.warnings,
        },
    }

    if dry_run:
        artifacts = build_dry_run_artifacts(
            question,
            required_aspects=required_aspects,
            source_expectations=source_expectations,
        )
        answer = str(artifacts["answer"])
        trace.update(trace_payload(question, required_events, artifacts, answer))
        trace.update(
            {
                "finished_at": utc_now_iso(),
                "citations": [],
                "web_search_calls": [],
                "usage": {},
                "status": "dry_run_complete",
            }
        )
        trace_path = write_trace(trace_dir, "evolved-dry-run", trace)
        return EvolvedRunResult(answer=answer, trace_path=trace_path, dry_run=True)

    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required for live evolved runs. "
            "Use --dry-run to validate the pipeline without calling the API."
        )

    client = OpenAI(api_key=settings.openai_api_key)
    model_config = mapping(genome.get("model"))
    reasoning_effort = model_config.get("reasoning_effort", "medium")

    try:
        response = client.responses.create(
            model=model,
            reasoning={"effort": reasoning_effort},
            tools=[{"type": "web_search"}],
            tool_choice="auto",
            include=["web_search_call.action.sources"],
            input=prompt,
        )
    except AuthenticationError as exc:
        trace.update(
            {
                "finished_at": utc_now_iso(),
                "status": "error",
                "error_type": "openai_authentication_error",
                "error_message": str(exc),
            }
        )
        trace_path = write_trace(trace_dir, "evolved-error", trace)
        raise RuntimeError(
            "OpenAI authentication failed for evolved run. Error trace written "
            f"to: {trace_path}"
        ) from exc
    except OpenAIError as exc:
        trace.update(
            {
                "finished_at": utc_now_iso(),
                "status": "error",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
        )
        trace_path = write_trace(trace_dir, "evolved-error", trace)
        raise RuntimeError(
            f"OpenAI API call failed. Error trace written to: {trace_path}"
        ) from exc

    response_payload = response_to_dict(response)
    raw_text = extract_output_text(response_payload)
    parsed = parse_json_object(raw_text)
    artifacts = normalize_artifacts(parsed, raw_text)
    answer = str(artifacts["answer"])
    response_citations = extract_citations(response_payload)
    citations = merge_citations(response_citations, artifact_citations(artifacts))

    trace.update(trace_payload(question, required_events, artifacts, answer))
    trace.update(
        {
            "finished_at": utc_now_iso(),
            "citations": citations,
            "web_search_calls": extract_web_search_calls(response_payload),
            "usage": extract_usage(response_payload),
            "response_id": response_payload.get("id"),
            "raw_output_text": raw_text,
            "status": "complete" if parsed else "complete_with_parse_warning",
        }
    )
    trace_path = write_trace(trace_dir, "evolved-live", trace)
    return EvolvedRunResult(answer=answer, trace_path=trace_path, dry_run=False)


def trace_payload(
    question: str,
    required_events: list[str],
    artifacts: dict[str, Any],
    answer: str,
) -> dict[str, Any]:
    payload = {
        "events": build_events(
            required_events=required_events,
            artifacts=artifacts,
            question=question,
        ),
        "answer": answer,
    }
    payload.update(
        {key: artifacts.get(key, empty_artifact(key)) for key in ARTIFACT_KEYS}
    )
    if "parse_warning" in artifacts:
        payload["parse_warning"] = artifacts["parse_warning"]
    return payload


def mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]
