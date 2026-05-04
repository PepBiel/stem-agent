from __future__ import annotations

from typing import Any


def response_to_dict(response: Any) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump(mode="json")
    if isinstance(response, dict):
        return response
    raise TypeError(f"Unsupported OpenAI response type: {type(response)!r}")


def extract_output_text(response_payload: dict[str, Any]) -> str:
    direct = response_payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct

    chunks: list[str] = []
    for item in response_payload.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                chunks.append(content["text"])

    return "\n".join(chunks).strip()


def extract_citations(response_payload: dict[str, Any]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    for item in response_payload.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            for annotation in content.get("annotations", []):
                if isinstance(annotation, dict) and annotation.get("type") == "url_citation":
                    citations.append(annotation)
    return citations


def extract_web_search_calls(response_payload: dict[str, Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for item in response_payload.get("output", []):
        if isinstance(item, dict) and item.get("type") == "web_search_call":
            calls.append(item)
    return calls


def extract_usage(response_payload: dict[str, Any]) -> dict[str, Any]:
    usage = response_payload.get("usage")
    if isinstance(usage, dict):
        return usage
    return {}
