from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import AuthenticationError, OpenAI, OpenAIError

from stem_agent.core.config import load_yaml, resolve_model
from stem_agent.core.openai_responses import (
    extract_citations,
    extract_output_text,
    extract_web_search_calls,
    response_to_dict,
)
from stem_agent.core.settings import Settings
from stem_agent.core.tracing import utc_now_iso, write_trace


@dataclass(frozen=True)
class BaselineRunResult:
    answer: str
    trace_path: Path
    dry_run: bool


def build_baseline_prompt(question: str, config: dict[str, Any]) -> str:
    limits = config.get("limits", {})
    max_sources = limits.get("max_sources", 4)
    max_search_queries = limits.get("max_search_queries", 2)

    return f"""You are the baseline research agent for a controlled evaluation.

Answer the technical research question using a simple search-and-summarize
workflow. Do not perform advanced source triage, contradiction checking, or
claim-level citation auditing. Those are reserved for the evolved agent.

Constraints:
- Use at most {max_search_queries} focused search queries.
- Cite at most {max_sources} sources.
- Prefer primary sources, official docs, papers, benchmarks, or repositories.
- Keep the answer concise and useful for an engineer.
- Include three sections: Answer, Sources, Limitations.

Question:
{question}
"""


def build_dry_run_answer(question: str) -> str:
    return f"""Answer
This is a dry-run baseline response for: {question}

Sources
- No external sources were fetched because --dry-run was enabled.

Limitations
- This output only validates configuration loading, CLI wiring, and trace
  creation. It is not an evaluated research answer.
"""


def run_baseline(
    *,
    question: str,
    config_path: Path,
    trace_dir: Path,
    settings: Settings,
    dry_run: bool,
) -> BaselineRunResult:
    config = load_yaml(config_path)
    model = resolve_model(config, settings.openai_model)
    prompt = build_baseline_prompt(question, config)

    started_at = utc_now_iso()
    trace: dict[str, Any] = {
        "run_type": "baseline",
        "started_at": started_at,
        "question": question,
        "config_path": str(config_path),
        "agent_id": config.get("agent", {}).get("id"),
        "model": model,
        "dry_run": dry_run,
        "workflow": config.get("workflow", []),
        "limits": config.get("limits", {}),
    }

    if dry_run:
        answer = build_dry_run_answer(question)
        trace.update(
            {
                "finished_at": utc_now_iso(),
                "answer": answer,
                "citations": [],
                "web_search_calls": [],
                "status": "dry_run_complete",
            }
        )
        trace_path = write_trace(trace_dir, "baseline-dry-run", trace)
        return BaselineRunResult(answer=answer, trace_path=trace_path, dry_run=True)

    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required for live baseline runs. "
            "Use --dry-run to validate the pipeline without calling the API."
        )

    client = OpenAI(api_key=settings.openai_api_key)
    model_config = config.get("model", {})
    reasoning_effort = model_config.get("reasoning_effort", "low")

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
        trace_path = write_trace(trace_dir, "baseline-error", trace)
        raise RuntimeError(
            "OpenAI authentication failed. For this baseline, the API key must "
            "allow Responses API writes, including the api.responses.write "
            f"scope. Error trace written to: {trace_path}"
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
        trace_path = write_trace(trace_dir, "baseline-error", trace)
        raise RuntimeError(
            f"OpenAI API call failed. Error trace written to: {trace_path}"
        ) from exc

    response_payload = response_to_dict(response)
    answer = extract_output_text(response_payload)

    trace.update(
        {
            "finished_at": utc_now_iso(),
            "answer": answer,
            "citations": extract_citations(response_payload),
            "web_search_calls": extract_web_search_calls(response_payload),
            "response_id": response_payload.get("id"),
            "status": "complete",
        }
    )
    trace_path = write_trace(trace_dir, "baseline-live", trace)
    return BaselineRunResult(answer=answer, trace_path=trace_path, dry_run=False)
