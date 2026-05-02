from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


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


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "status":
        print_status()
        return

    if args.command == "eval-info":
        print_eval_info()
        return

    parser.print_help()
