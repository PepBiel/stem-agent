from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from stem_agent.core.config import load_yaml
from stem_agent.core.paths import PROJECT_ROOT


@dataclass(frozen=True)
class GenomeValidationResult:
    genome_path: Path
    schema_path: Path
    valid: bool
    errors: list[str]
    warnings: list[str]


def validate_genome_files(
    *,
    genome_path: Path,
    schema_path: Path,
) -> GenomeValidationResult:
    genome = load_yaml(genome_path)
    schema = load_yaml(schema_path)

    errors: list[str] = []
    warnings: list[str] = []

    validate_required_sections(genome, schema, errors)
    validate_workflow(genome, schema, errors)
    validate_prompt_roles(genome, schema, errors)
    validate_tools(genome, schema, errors)
    validate_limits(genome, schema, errors)
    validate_trace_contract(genome, schema, errors)
    validate_acceptance_criteria(genome, schema, errors)
    validate_parent_and_schema_paths(genome, genome_path, schema_path, warnings)

    return GenomeValidationResult(
        genome_path=genome_path,
        schema_path=schema_path,
        valid=not errors,
        errors=errors,
        warnings=warnings,
    )


def validate_required_sections(
    genome: dict[str, Any],
    schema: dict[str, Any],
    errors: list[str],
) -> None:
    for section in string_list(schema.get("required_sections")):
        if section not in genome:
            errors.append(f"Missing required section: {section}")


def validate_workflow(
    genome: dict[str, Any],
    schema: dict[str, Any],
    errors: list[str],
) -> None:
    workflow = string_list(genome.get("workflow"))
    if not workflow:
        errors.append("workflow must be a non-empty list")
        return

    required_steps = string_list(schema.get("required_workflow_steps"))
    missing_steps = [step for step in required_steps if step not in workflow]
    if missing_steps:
        errors.append(f"workflow is missing required steps: {', '.join(missing_steps)}")

    required_positions = [
        workflow.index(step) for step in required_steps if step in workflow
    ]
    if required_positions != sorted(required_positions):
        errors.append("workflow steps do not follow the required schema order")


def validate_prompt_roles(
    genome: dict[str, Any],
    schema: dict[str, Any],
    errors: list[str],
) -> None:
    prompt_roles = mapping(genome.get("prompt_roles"))
    if not prompt_roles:
        errors.append("prompt_roles must be a non-empty mapping")
        return

    missing_roles = [
        role
        for role in string_list(schema.get("required_prompt_roles"))
        if role not in prompt_roles
    ]
    if missing_roles:
        errors.append(f"prompt_roles is missing roles: {', '.join(missing_roles)}")


def validate_tools(
    genome: dict[str, Any],
    schema: dict[str, Any],
    errors: list[str],
) -> None:
    tools = mapping(genome.get("tools"))
    allowed_tools = set(string_list(tools.get("allowed")))
    forbidden_tools = set(string_list(tools.get("forbidden")))
    schema_allowed = set(string_list(schema.get("allowed_tool_ids")))
    schema_forbidden = set(string_list(schema.get("forbidden_tool_ids")))

    unknown_allowed = sorted(allowed_tools - schema_allowed)
    if unknown_allowed:
        errors.append(
            "tools.allowed contains unsupported tools: "
            f"{', '.join(unknown_allowed)}"
        )

    forbidden_allowed = sorted(allowed_tools & schema_forbidden)
    if forbidden_allowed:
        errors.append(
            "tools.allowed includes forbidden tools: "
            f"{', '.join(forbidden_allowed)}"
        )

    missing_forbidden = sorted(schema_forbidden - forbidden_tools)
    if missing_forbidden:
        errors.append(
            "tools.forbidden is missing required bans: "
            f"{', '.join(missing_forbidden)}"
        )


def validate_limits(
    genome: dict[str, Any],
    schema: dict[str, Any],
    errors: list[str],
) -> None:
    limits = mapping(genome.get("limits"))
    max_limits = mapping(schema.get("max_limits"))

    for name, max_value in max_limits.items():
        value = limits.get(name)
        if value is None:
            errors.append(f"limits.{name} is required")
            continue
        if not isinstance(value, int):
            errors.append(f"limits.{name} must be an integer")
            continue
        if isinstance(max_value, int) and value > max_value:
            errors.append(f"limits.{name}={value} exceeds schema max {max_value}")


def validate_trace_contract(
    genome: dict[str, Any],
    schema: dict[str, Any],
    errors: list[str],
) -> None:
    trace = mapping(genome.get("trace"))
    required_events = string_list(trace.get("required_events"))
    schema_events = string_list(schema.get("required_trace_events"))
    missing_events = [
        event for event in schema_events if event not in required_events
    ]
    if missing_events:
        errors.append(f"trace.required_events is missing: {', '.join(missing_events)}")


def validate_acceptance_criteria(
    genome: dict[str, Any],
    schema: dict[str, Any],
    errors: list[str],
) -> None:
    acceptance = mapping(genome.get("acceptance_criteria"))
    metrics = string_list(acceptance.get("metrics"))
    missing_metrics = [
        metric
        for metric in string_list(schema.get("required_acceptance_metrics"))
        if metric not in metrics
    ]
    if missing_metrics:
        errors.append(
            "acceptance_criteria.metrics is missing: "
            f"{', '.join(missing_metrics)}"
        )

    if not mapping(acceptance.get("accept_if")):
        errors.append(
            "acceptance_criteria.accept_if must define acceptance thresholds"
        )
    if not string_list(acceptance.get("reject_if")):
        errors.append("acceptance_criteria.reject_if must define rejection triggers")


def validate_parent_and_schema_paths(
    genome: dict[str, Any],
    genome_path: Path,
    schema_path: Path,
    warnings: list[str],
) -> None:
    genome_meta = mapping(genome.get("genome"))

    parent = genome_meta.get("parent")
    if isinstance(parent, str) and not (PROJECT_ROOT / parent).exists():
        warnings.append(f"genome.parent does not exist on disk: {parent}")

    declared_schema = genome_meta.get("schema")
    if isinstance(declared_schema, str):
        declared_schema_path = PROJECT_ROOT / declared_schema
        if declared_schema_path.resolve() != schema_path.resolve():
            warnings.append(
                "genome.schema does not match the schema file being used: "
                f"{declared_schema}"
            )


def format_validation_result(result: GenomeValidationResult) -> str:
    lines = [
        "Genome validation",
        f"Genome: {result.genome_path}",
        f"Schema: {result.schema_path}",
        f"Valid: {result.valid}",
    ]

    if result.errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in result.errors)

    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in result.warnings)

    return "\n".join(lines)


def mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]
