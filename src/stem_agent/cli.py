from __future__ import annotations

import argparse
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

    return parser


def print_status() -> None:
    expected_paths = [
        "configs",
        "docs",
        "evals",
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


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "status":
        print_status()
        return

    parser.print_help()
