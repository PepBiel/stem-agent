from __future__ import annotations

import argparse
import json
from pathlib import Path

from stem_agent.core.paths import PROJECT_ROOT
from stem_agent.core.settings import load_settings
from stem_agent.workflows.baseline import run_baseline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stem-agent",
        description="Run and evaluate the Stem Agent prototype.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "status",
        help="Print the current scaffold status.",
    )

    subparsers.add_parser(
        "eval-info",
        help="Print the fixed evaluation set summary.",
    )

    baseline_parser = subparsers.add_parser(
        "run-baseline",
        help="Run the baseline research agent for one question.",
    )
    baseline_input = baseline_parser.add_mutually_exclusive_group(required=True)
    baseline_input.add_argument(
        "--question",
        help="Research question to answer.",
    )
    baseline_input.add_argument(
        "--question-id",
        help="Question ID from evals/questions.json, for example DR-001.",
    )
    baseline_parser.add_argument(
        "--config",
        default="configs/base_agent.yaml",
        help="Path to the baseline agent config.",
    )
    baseline_parser.add_argument(
        "--trace-dir",
        default="results/traces",
        help="Directory where the run trace JSON will be written.",
    )
    baseline_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the pipeline without calling the OpenAI API.",
    )

    return parser


def print_status() -> None:
    expected_paths = [
        "configs",
        "configs/base_agent.yaml",
        "docs",
        "docs/evaluation_plan.md",
        "evals",
        "evals/questions.json",
        "evals/rubric.yaml",
        "results/traces",
        "src/stem_agent/core",
        "src/stem_agent/tools",
        "src/stem_agent/workflows",
    ]
    print("Stem Agent scaffold")
    print(f"Project root: {PROJECT_ROOT}")
    for relative_path in expected_paths:
        marker = "ok" if (PROJECT_ROOT / relative_path).exists() else "missing"
        print(f"- {relative_path}: {marker}")


def print_eval_info() -> None:
    questions_path = PROJECT_ROOT / "evals" / "questions.json"
    rubric_path = PROJECT_ROOT / "evals" / "rubric.yaml"

    with questions_path.open(encoding="utf-8") as file:
        payload = json.load(file)

    questions = payload["questions"]
    print("Stem Agent evaluation set")
    print(f"Domain: {payload['domain']}")
    print(f"Version: {payload['version']}")
    print(f"Questions: {len(questions)}")
    print(f"Rubric: {'ok' if rubric_path.exists() else 'missing'}")
    print("Question IDs:")
    for item in questions:
        print(f"- {item['id']}: {item['question']}")


def load_question_by_id(question_id: str) -> str:
    questions_path = PROJECT_ROOT / "evals" / "questions.json"
    with questions_path.open(encoding="utf-8") as file:
        payload = json.load(file)

    for item in payload["questions"]:
        if item["id"] == question_id:
            return item["question"]

    known_ids = ", ".join(item["id"] for item in payload["questions"])
    raise ValueError(f"Unknown question ID {question_id!r}. Known IDs: {known_ids}")


def run_baseline_command(args: argparse.Namespace) -> None:
    question = args.question or load_question_by_id(args.question_id)
    settings = load_settings(PROJECT_ROOT)
    result = run_baseline(
        question=question,
        config_path=PROJECT_ROOT / args.config,
        trace_dir=PROJECT_ROOT / args.trace_dir,
        settings=settings,
        dry_run=args.dry_run,
    )

    print(result.answer)
    print(f"\nTrace written to: {result.trace_path}")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "status":
        print_status()
        return

    if args.command == "eval-info":
        print_eval_info()
        return

    if args.command == "run-baseline":
        try:
            run_baseline_command(args)
        except RuntimeError as exc:
            parser.exit(1, f"error: {exc}\n")
        return

    parser.print_help()
