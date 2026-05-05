from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_slug(value: str, max_length: int = 48) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "-", value.lower()).strip("-")
    if not slug:
        return "trace"
    return slug[:max_length].strip("-")


def write_trace(trace_dir: Path, prefix: str, payload: dict[str, Any]) -> Path:
    trace_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = trace_dir / f"{timestamp}-{safe_slug(prefix)}.json"
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path
