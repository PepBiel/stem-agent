from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI, OpenAIError

from stem_agent.core.openai_responses import (
    extract_output_text,
    extract_usage,
    response_to_dict,
)
from stem_agent.core.settings import Settings
from stem_agent.core.tracing import utc_now_iso
from stem_agent.evaluation.scoring import (
    EvaluationInput,
    citation_urls,
    evaluate_trace,
    extract_answer_lines,
    load_json,
    load_json_or_yaml,
    write_evaluation,
)


JUDGE_SCHEMA_VERSION = "2026-05-04"


@dataclass(frozen=True)
class JudgeInput:
    trace_path: Path
    questions_path: Path
    rubric_path: Path
    question_id: str | None
    output_path: Path | None
    settings: Settings
    judge_model: str
    dry_run: bool


def build_judge_prompt(
    *,
    trace: dict[str, Any],
    question: dict[str, Any],
    heuristic_evaluation: dict[str, Any],
) -> str:
    answer = str(trace.get("answer", ""))
    claim_lines = extract_answer_lines(answer)
    citations = trace.get("citations", [])
    urls = sorted(set(citation_urls(trace)))

    return f"""You are a strict evaluator for a deep-research agent benchmark.

Your job is to grade one answer against a fixed rubric. Be conservative. Do not
reward polished prose unless it is grounded, useful, and complete.

Important evaluation rules:
- Coverage requires substantively answering each required aspect, not merely
  mentioning similar words.
- Citation support requires the cited source to plausibly support the specific
  claim. A citation appearing near a claim is not enough.
- Source quality requires relevance to the question, not just a reputable domain.
- Penalize generic limitations, shallow uncertainty handling, and answers that
  miss important engineering trade-offs.
- Do not use web browsing. Judge only from the answer, citation metadata, and
  benchmark expectations below.

Return only valid JSON with this exact top-level shape:
{{
  "schema_version": "{JUDGE_SCHEMA_VERSION}",
  "scores": {{
    "factual_accuracy": <integer 1-5>,
    "coverage": <integer 1-5>,
    "evidence_quality": <integer 1-5>,
    "uncertainty_handling": <integer 1-5>,
    "engineer_usefulness": <integer 1-5>,
    "conciseness_and_structure": <integer 1-5>
  }},
  "coverage_audit": [
    {{
      "aspect": "<required aspect>",
      "score": <integer 1-5>,
      "verdict": "covered|partial|missing",
      "reason": "<brief reason>"
    }}
  ],
  "citation_audit": [
    {{
      "claim": "<important claim or claim line>",
      "support": "supported|weak|unsupported|not_checked",
      "cited_urls": ["<url>"],
      "reason": "<brief reason>"
    }}
  ],
  "source_audit": [
    {{
      "url": "<url>",
      "quality": "strong|acceptable|weak|irrelevant",
      "reason": "<brief reason>"
    }}
  ],
  "failure_tags": ["<tag>"],
  "summary": "<short judgment>",
  "recommended_fix": "<most important improvement>"
}}

Question ID:
{question.get("id")}

Question:
{question.get("question")}

Required aspects:
{json.dumps(question.get("must_cover", []), indent=2)}

Expected source types:
{json.dumps(question.get("source_expectations", []), indent=2)}

Answer:
{answer}

Claim lines extracted by the heuristic scorer:
{json.dumps(claim_lines, indent=2)}

Cited URLs:
{json.dumps(urls, indent=2)}

Citation metadata:
{json.dumps(citations, indent=2)}

Heuristic evaluation, for reference only:
{json.dumps(heuristic_evaluation, indent=2)}
"""


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Judge response did not contain a JSON object")
        payload = json.loads(stripped[start : end + 1])

    if not isinstance(payload, dict):
        raise ValueError("Judge response JSON must be an object")
    return payload


def clamp_score(value: Any) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        return 1
    return max(1, min(5, score))


def normalize_judge_payload(payload: dict[str, Any]) -> dict[str, Any]:
    scores_payload = payload.get("scores", {})
    if not isinstance(scores_payload, dict):
        scores_payload = {}

    dimensions = [
        "factual_accuracy",
        "coverage",
        "evidence_quality",
        "uncertainty_handling",
        "engineer_usefulness",
        "conciseness_and_structure",
    ]
    scores = {name: clamp_score(scores_payload.get(name)) for name in dimensions}
    average = round(sum(scores.values()) / len(scores), 4)

    payload["schema_version"] = str(payload.get("schema_version", JUDGE_SCHEMA_VERSION))
    payload["scores"] = scores
    payload["average_score"] = average
    payload["normalized_score"] = round((average - 1) / 4, 4)
    payload.setdefault("coverage_audit", [])
    payload.setdefault("citation_audit", [])
    payload.setdefault("source_audit", [])
    payload.setdefault("failure_tags", [])
    payload.setdefault("summary", "")
    payload.setdefault("recommended_fix", "")
    return payload


def build_dry_run_judge_payload(heuristic_evaluation: dict[str, Any]) -> dict[str, Any]:
    metrics = heuristic_evaluation.get("metrics", {})
    coverage = 4 if metrics.get("coverage_score", 0.0) >= 0.8 else 3
    evidence = 4 if metrics.get("citation_support_score", 0.0) >= 0.8 else 2
    payload = {
        "schema_version": JUDGE_SCHEMA_VERSION,
        "scores": {
            "factual_accuracy": 3,
            "coverage": coverage,
            "evidence_quality": evidence,
            "uncertainty_handling": 3,
            "engineer_usefulness": 3,
            "conciseness_and_structure": 3,
        },
        "coverage_audit": [],
        "citation_audit": [],
        "source_audit": [],
        "failure_tags": ["dry_run"],
        "summary": "Dry-run judge output; no model call was made.",
        "recommended_fix": "Run without --dry-run for semantic evaluation.",
    }
    return normalize_judge_payload(payload)


def calculate_final_score(
    *,
    heuristic_score: float,
    judge_normalized_score: float,
) -> float:
    return round((0.35 * heuristic_score) + (0.65 * judge_normalized_score), 4)


def judge_trace(judge_input: JudgeInput) -> dict[str, Any]:
    trace = load_json(judge_input.trace_path)
    questions_payload = load_json(judge_input.questions_path)
    _ = load_json_or_yaml(judge_input.rubric_path)
    heuristic_evaluation = evaluate_trace(
        EvaluationInput(
            trace_path=judge_input.trace_path,
            questions_path=judge_input.questions_path,
            rubric_path=judge_input.rubric_path,
            question_id=judge_input.question_id,
        )
    )
    question = {
        "id": heuristic_evaluation["question_id"],
        "question": heuristic_evaluation["question"],
    }
    for item in questions_payload.get("questions", []):
        if item.get("id") == heuristic_evaluation["question_id"]:
            question = item
            break

    started_at = utc_now_iso()
    if judge_input.dry_run:
        judge_payload = build_dry_run_judge_payload(heuristic_evaluation)
        response_id = None
        judge_usage: dict[str, Any] = {}
    else:
        if not judge_input.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for model-assisted judging.")

        prompt = build_judge_prompt(
            trace=trace,
            question=question,
            heuristic_evaluation=heuristic_evaluation,
        )
        client = OpenAI(api_key=judge_input.settings.openai_api_key)
        try:
            response = client.responses.create(
                model=judge_input.judge_model,
                reasoning={"effort": "low"},
                max_output_tokens=3500,
                input=prompt,
            )
        except OpenAIError as exc:
            raise RuntimeError(f"OpenAI judge call failed: {exc}") from exc

        response_payload = response_to_dict(response)
        response_id = response_payload.get("id")
        judge_usage = extract_usage(response_payload)
        judge_payload = normalize_judge_payload(
            extract_json_object(extract_output_text(response_payload))
        )

    result = {
        "schema_version": JUDGE_SCHEMA_VERSION,
        "evaluation_type": "model_assisted_trace_judge",
        "started_at": started_at,
        "finished_at": utc_now_iso(),
        "trace_path": str(judge_input.trace_path),
        "question_id": heuristic_evaluation["question_id"],
        "question": heuristic_evaluation["question"],
        "agent_id": heuristic_evaluation.get("agent_id"),
        "answer_model": heuristic_evaluation.get("model"),
        "judge_model": judge_input.judge_model,
        "dry_run": judge_input.dry_run,
        "heuristic_score": heuristic_evaluation["overall_score"],
        "judge_score": judge_payload["normalized_score"],
        "final_score": calculate_final_score(
            heuristic_score=heuristic_evaluation["overall_score"],
            judge_normalized_score=judge_payload["normalized_score"],
        ),
        "heuristic_evaluation": heuristic_evaluation,
        "judge_evaluation": judge_payload,
        "judge_usage": judge_usage,
        "response_id": response_id,
    }

    if judge_input.output_path:
        write_evaluation(judge_input.output_path, result)

    return result
