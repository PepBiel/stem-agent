from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        payload = yaml.safe_load(file)

    if not isinstance(payload, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")

    return payload


def resolve_model(config: dict[str, Any], env_model: str | None) -> str:
    if env_model:
        return env_model

    model_config = config.get("model", {})
    if not isinstance(model_config, dict):
        raise ValueError("Expected 'model' section in agent config")

    default_model = model_config.get("recommended_default")
    if not isinstance(default_model, str) or not default_model:
        raise ValueError("Agent config must define model.recommended_default")

    return default_model
