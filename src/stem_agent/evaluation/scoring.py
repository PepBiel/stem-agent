from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


STOPWORDS = {
    "about",
    "across",
    "agent",
    "agents",
    "and",
    "are",
    "between",
    "from",
    "have",
    "into",
    "main",
    "methods",
    "quality",
    "that",
    "the",
    "their",
    "these",
    "they",
    "this",
    "what",
    "when",
    "with",
}

AUTHORITATIVE_DOMAINS = {
    "aclanthology.org",
    "arxiv.org",
    "docs.langchain.com",
    "dspy.ai",
    "github.com",
    "iclr.cc",
    "openai.com",
    "openreview.net",
    "platform.openai.com",
    "proceedings.neurips.cc",
}

WEAK_SOURCE_DOMAINS = {
    "huggingface.co",
    "papers.cool",
    "papers.lunadong.com",
    "reddit.com",
    "www.reddit.com",
}

UNCERTAINTY_TERMS = {
    "caveat",
    "conflict",
    "contradict",
    "disagree",
    "however",
    "limitation",
    "limitations",
    "not clear",
    "open question",
    "uncertain",
    "uncertainty",
}


@dataclass(frozen=True)
class EvaluationInput:
    trace_path: Path
    questions_path: Path
    rubric_path: Path
    question_id: str | None


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if len(word) >= 4 and word not in STOPWORDS}


def find_question(
    questions_payload: dict[str, Any],
    *,
    question_id: str | None,
    question_text: str,
) -> dict[str, Any]:
    questions = questions_payload.get("questions", [])
    if not isinstance(questions, list):
        raise ValueError("Expected questions list in evaluation dataset")

    if question_id:
        for item in questions:
            if item.get("id") == question_id:
                return item
        raise ValueError(f"Unknown question id: {question_id}")

    normalized_question = normalize_text(question_text)
    for item in questions:
        if normalize_text(str(item.get("question", ""))) == normalized_question:
            return item

    raise ValueError(
        "Could not infer question from trace. Pass --question-id explicitly."
    )


def score_coverage(
    answer: str,
    question: dict[str, Any],
) -> tuple[float, list[dict[str, Any]]]:
    answer_tokens = tokenize(answer)
    details: list[dict[str, Any]] = []

    for aspect in question.get("must_cover", []):
        aspect_text = str(aspect)
        expected_tokens = sorted(tokenize(aspect_text))
        if not expected_tokens:
            coverage = 0.0
            matched: list[str] = []
        else:
            matched = [token for token in expected_tokens if token in answer_tokens]
            coverage = len(matched) / len(expected_tokens)

        covered = coverage >= 0.5 or len(matched) >= min(2, len(expected_tokens))
        details.append(
            {
                "aspect": aspect_text,
                "covered": covered,
                "matched_terms": matched,
                "expected_terms": expected_tokens,
            }
        )

    if not details:
        return 0.0, details

    return sum(1 for item in details if item["covered"]) / len(details), details


def extract_answer_lines(answer: str) -> list[str]:
    lines: list[str] = []
    in_sources = False
    in_limitations = False

    for raw_line in answer.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower().strip("# ")
        if lower.startswith("sources"):
            in_sources = True
            in_limitations = False
            continue
        if lower.startswith("limitations"):
            in_limitations = True
            in_sources = False
            continue
        if line.startswith("#"):
            continue
        if in_sources or in_limitations:
            continue
        if is_claim_line(line):
            lines.append(line)

    return lines


def is_claim_line(line: str) -> bool:
    clean = re.sub(r"^(?:[-*]|\d+[.)])\s*", "", line).strip()
    tokens = tokenize(clean)

    if len(tokens) < 4:
        return False
    if not line_has_citation(clean) and clean.endswith(":"):
        return False
    if (
        not line_has_citation(clean)
        and clean.startswith("**")
        and clean.endswith("**")
    ):
        return False

    return True


def line_has_citation(line: str) -> bool:
    return (
        "http://" in line
        or "https://" in line
        or re.search(r"\[[^\]]+\]\([^)]+\)", line) is not None
    )


def score_citation_support(answer: str) -> tuple[float, int, list[str]]:
    claim_lines = extract_answer_lines(answer)
    if not claim_lines:
        return 0.0, 0, []

    unsupported = [line for line in claim_lines if not line_has_citation(line)]
    supported_count = len(claim_lines) - len(unsupported)
    return supported_count / len(claim_lines), len(unsupported), unsupported


def citation_urls(trace: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for citation in trace.get("citations", []):
        if isinstance(citation, dict) and isinstance(citation.get("url"), str):
            urls.append(citation["url"])
    return urls


def source_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def score_source_quality(urls: list[str]) -> tuple[float, list[dict[str, Any]]]:
    unique_urls = sorted(set(urls))
    details: list[dict[str, Any]] = []

    for url in unique_urls:
        domain = source_domain(url)
        authoritative = domain in AUTHORITATIVE_DOMAINS
        weak = domain in WEAK_SOURCE_DOMAINS
        details.append(
            {
                "url": url,
                "domain": domain,
                "authoritative": authoritative,
                "weak": weak,
            }
        )

    if not details:
        return 0.0, details

    return sum(1 for item in details if item["authoritative"]) / len(details), details


def score_contradiction_handling(answer: str) -> float:
    normalized = normalize_text(answer)
    has_limitations = "limitation" in normalized or "limitations" in normalized
    has_uncertainty = any(term in normalized for term in UNCERTAINTY_TERMS)

    if has_limitations and has_uncertainty:
        return 1.0
    if has_limitations or has_uncertainty:
        return 0.5
    return 0.0


def score_redundancy(urls: list[str], answer: str) -> float:
    if urls:
        citation_diversity = len(set(urls)) / len(urls)
    else:
        citation_diversity = 0.0

    lines = [normalize_text(line.strip()) for line in answer.splitlines() if line.strip()]
    if lines:
        line_diversity = len(set(lines)) / len(lines)
    else:
        line_diversity = 0.0

    return round((citation_diversity + line_diversity) / 2, 4)


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def runtime_seconds(trace: dict[str, Any]) -> float | None:
    started = parse_timestamp(trace.get("started_at"))
    finished = parse_timestamp(trace.get("finished_at"))
    if not started or not finished:
        return None
    return round((finished - started).total_seconds(), 3)


def weighted_score(metrics: dict[str, float], rubric: dict[str, Any]) -> float:
    automatic_metrics = rubric.get("automatic_metrics", {})
    weighted_total = 0.0
    weight_total = 0.0

    for name, config in automatic_metrics.items():
        if name == "unsupported_claim_count":
            continue
        if not isinstance(config, dict):
            continue
        weight = float(config.get("weight", 0.0))
        if name in metrics:
            weighted_total += metrics[name] * weight
            weight_total += weight

    unsupported_weight = float(
        automatic_metrics.get("unsupported_claim_count", {}).get("weight", 0.0)
    )
    unsupported_score = metrics.get("unsupported_claim_score", 0.0)
    weighted_total += unsupported_score * unsupported_weight
    weight_total += unsupported_weight

    if math.isclose(weight_total, 0.0):
        return 0.0

    return round(weighted_total / weight_total, 4)


def failure_tags(
    *,
    coverage_score: float,
    citation_support_score: float,
    source_quality_score: float,
    unsupported_claim_count: int,
    contradiction_handling_score: float,
    redundancy_score: float,
) -> list[str]:
    tags: list[str] = []
    if coverage_score < 0.6:
        tags.append("missing_required_aspect")
    if citation_support_score < 0.8:
        tags.append("unsupported_claim")
    if source_quality_score < 0.6:
        tags.append("weak_source")
    if unsupported_claim_count > 0:
        tags.append("unsupported_claim")
    if contradiction_handling_score < 0.5:
        tags.append("contradiction_missed")
    if redundancy_score < 0.6:
        tags.append("repetitive_answer")
    return sorted(set(tags))


def evaluate_trace(evaluation_input: EvaluationInput) -> dict[str, Any]:
    trace = load_json(evaluation_input.trace_path)
    questions_payload = load_json(evaluation_input.questions_path)
    rubric = load_json_or_yaml(evaluation_input.rubric_path)
    question = find_question(
        questions_payload,
        question_id=evaluation_input.question_id,
        question_text=str(trace.get("question", "")),
    )

    answer = str(trace.get("answer", ""))
    urls = citation_urls(trace)
    coverage_score, coverage_details = score_coverage(answer, question)
    citation_support_score, unsupported_claim_count, unsupported_lines = (
        score_citation_support(answer)
    )
    source_quality_score, source_details = score_source_quality(urls)
    contradiction_handling_score = score_contradiction_handling(answer)
    redundancy_score = score_redundancy(urls, answer)
    claim_lines = extract_answer_lines(answer)
    unsupported_claim_score = (
        1.0
        if not claim_lines
        else max(0.0, 1.0 - unsupported_claim_count / len(claim_lines))
    )

    metrics = {
        "coverage_score": round(coverage_score, 4),
        "citation_support_score": round(citation_support_score, 4),
        "source_quality_score": round(source_quality_score, 4),
        "unsupported_claim_count": unsupported_claim_count,
        "unsupported_claim_score": round(unsupported_claim_score, 4),
        "contradiction_handling_score": round(contradiction_handling_score, 4),
        "redundancy_score": round(redundancy_score, 4),
    }

    tags = failure_tags(
        coverage_score=coverage_score,
        citation_support_score=citation_support_score,
        source_quality_score=source_quality_score,
        unsupported_claim_count=unsupported_claim_count,
        contradiction_handling_score=contradiction_handling_score,
        redundancy_score=redundancy_score,
    )

    return {
        "schema_version": "2026-05-04",
        "trace_path": str(evaluation_input.trace_path),
        "run_type": trace.get("run_type"),
        "agent_id": trace.get("agent_id"),
        "model": trace.get("model"),
        "dry_run": trace.get("dry_run", False),
        "question_id": question.get("id"),
        "question": question.get("question"),
        "metrics": metrics,
        "overall_score": weighted_score(metrics, rubric),
        "failure_tags": tags,
        "runtime_seconds": runtime_seconds(trace),
        "details": {
            "coverage": coverage_details,
            "claim_lines": claim_lines,
            "unsupported_claim_lines": unsupported_lines,
            "sources": source_details,
            "citation_count": len(urls),
            "unique_citation_count": len(set(urls)),
        },
    }


def load_json_or_yaml(path: Path) -> dict[str, Any]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml

        with path.open(encoding="utf-8") as file:
            payload = yaml.safe_load(file)
    else:
        payload = load_json(path)

    if not isinstance(payload, dict):
        raise ValueError(f"Expected mapping in {path}")
    return payload


def write_evaluation(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
