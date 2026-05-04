from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from stem_agent.core.settings import Settings
from stem_agent.core.tracing import safe_slug, utc_now_iso
from stem_agent.evaluation.judge import JudgeInput, judge_trace
from stem_agent.evaluation.scoring import (
    EvaluationInput,
    evaluate_trace,
    load_json,
    write_evaluation,
)
from stem_agent.workflows.baseline import run_baseline


@dataclass(frozen=True)
class BatchInput:
    agent: str
    run_id: str
    output_root: Path
    questions_path: Path
    rubric_path: Path
    config_path: Path
    settings: Settings
    judge_model: str
    dry_run: bool
    limit: int | None


def usage_sum(usages: list[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, Any] = {}
    for usage in usages:
        add_usage(totals, usage)
    return totals


def add_usage(target: dict[str, Any], usage: dict[str, Any]) -> None:
    for key, value in usage.items():
        if isinstance(value, (int, float)):
            target[key] = target.get(key, 0) + value
        elif isinstance(value, dict):
            nested = target.setdefault(key, {})
            if isinstance(nested, dict):
                add_usage(nested, value)


def run_dir(output_root: Path, agent: str, run_id: str) -> Path:
    return output_root / "runs" / agent / run_id


def stable_trace_path(trace_path: Path, traces_dir: Path, question_id: str) -> Path:
    target = traces_dir / f"{question_id}.json"
    if target.exists():
        raise FileExistsError(f"Trace already exists and would be overwritten: {target}")
    trace_path.replace(target)
    return target


def load_questions(path: Path, limit: int | None) -> list[dict[str, Any]]:
    payload = load_json(path)
    questions = payload.get("questions", [])
    if not isinstance(questions, list):
        raise ValueError("Expected questions list in evaluation dataset")
    if limit is not None:
        return questions[:limit]
    return questions


def write_summary_markdown(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        f"# Evaluation Run: {summary['run_id']}",
        "",
        f"- Agent: `{summary['agent']}`",
        f"- Dry run: `{summary['dry_run']}`",
        f"- Questions: `{summary['question_count']}`",
        f"- Heuristic average: `{summary['aggregate']['heuristic_score_avg']}`",
        f"- Judge average: `{summary['aggregate']['judge_score_avg']}`",
        f"- Final average: `{summary['aggregate']['final_score_avg']}`",
        "",
        "| Question | Heuristic | Judge | Final | Runtime |",
        "|---|---:|---:|---:|---:|",
    ]

    for item in summary["questions"]:
        lines.append(
            "| {question_id} | {heuristic_score:.4f} | {judge_score:.4f} | "
            "{final_score:.4f} | {runtime_seconds} |".format(**item)
        )

    lines.extend(
        [
            "",
            "## Usage",
            "",
            "```json",
            json.dumps(summary["usage_totals"], indent=2),
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def run_evaluation_batch(batch_input: BatchInput) -> dict[str, Any]:
    if batch_input.agent != "baseline":
        raise ValueError("Only the baseline agent is implemented for batch runs.")

    root = run_dir(batch_input.output_root, batch_input.agent, batch_input.run_id)
    traces_dir = root / "traces"
    heuristic_dir = root / "heuristic"
    judge_dir = root / "judge"
    for path in (traces_dir, heuristic_dir, judge_dir):
        path.mkdir(parents=True, exist_ok=True)

    questions = load_questions(batch_input.questions_path, batch_input.limit)
    started_at = utc_now_iso()
    question_summaries: list[dict[str, Any]] = []
    baseline_usages: list[dict[str, Any]] = []
    judge_usages: list[dict[str, Any]] = []

    for question in questions:
        question_id = str(question["id"])
        result = run_baseline(
            question=str(question["question"]),
            config_path=batch_input.config_path,
            trace_dir=traces_dir,
            settings=batch_input.settings,
            dry_run=batch_input.dry_run,
        )
        trace_path = stable_trace_path(result.trace_path, traces_dir, question_id)
        trace = load_json(trace_path)
        baseline_usages.append(trace.get("usage", {}))

        heuristic = evaluate_trace(
            EvaluationInput(
                trace_path=trace_path,
                questions_path=batch_input.questions_path,
                rubric_path=batch_input.rubric_path,
                question_id=question_id,
            )
        )
        heuristic_path = heuristic_dir / f"{question_id}.json"
        write_evaluation(heuristic_path, heuristic)

        judge_path = judge_dir / f"{question_id}.json"
        judge = judge_trace(
            JudgeInput(
                trace_path=trace_path,
                questions_path=batch_input.questions_path,
                rubric_path=batch_input.rubric_path,
                question_id=question_id,
                output_path=judge_path,
                settings=batch_input.settings,
                judge_model=batch_input.judge_model,
                dry_run=batch_input.dry_run,
            )
        )
        judge_usages.append(judge.get("judge_usage", {}))

        question_summaries.append(
            {
                "question_id": question_id,
                "trace_path": str(trace_path),
                "heuristic_path": str(heuristic_path),
                "judge_path": str(judge_path),
                "heuristic_score": float(judge["heuristic_score"]),
                "judge_score": float(judge["judge_score"]),
                "final_score": float(judge["final_score"]),
                "runtime_seconds": heuristic.get("runtime_seconds"),
                "baseline_usage": trace.get("usage", {}),
                "judge_usage": judge.get("judge_usage", {}),
                "summary": judge["judge_evaluation"].get("summary", ""),
                "recommended_fix": judge["judge_evaluation"].get(
                    "recommended_fix",
                    "",
                ),
            }
        )

    summary = {
        "schema_version": "2026-05-04",
        "run_id": batch_input.run_id,
        "agent": batch_input.agent,
        "dry_run": batch_input.dry_run,
        "started_at": started_at,
        "finished_at": utc_now_iso(),
        "question_count": len(question_summaries),
        "artifact_root": str(root),
        "questions": question_summaries,
        "aggregate": {
            "heuristic_score_avg": average(
                [item["heuristic_score"] for item in question_summaries]
            ),
            "judge_score_avg": average(
                [item["judge_score"] for item in question_summaries]
            ),
            "final_score_avg": average(
                [item["final_score"] for item in question_summaries]
            ),
        },
        "usage_totals": {
            "baseline": usage_sum(baseline_usages),
            "judge": usage_sum(judge_usages),
            "combined": usage_sum([*baseline_usages, *judge_usages]),
        },
    }

    summary_path = root / "summary.json"
    summary_md_path = root / "summary.md"
    write_evaluation(summary_path, summary)
    write_summary_markdown(summary_md_path, summary)
    return summary


def default_run_id(agent: str, dry_run: bool) -> str:
    suffix = "dry-run" if dry_run else "live"
    return f"{safe_slug(agent)}-{safe_slug(utc_now_iso())}-{suffix}"
