from __future__ import annotations

import argparse
import json
from pathlib import Path

from stem_agent.core.genome import format_validation_result, validate_genome_files
from stem_agent.core.paths import PROJECT_ROOT
from stem_agent.core.settings import load_settings
from stem_agent.evaluation.batch import (
    BatchInput,
    default_config_path,
    default_run_id,
    default_schema_path,
    run_evaluation_batch,
)
from stem_agent.evaluation.scoring import (
    EvaluationInput,
    evaluate_trace,
    write_evaluation,
)
from stem_agent.evaluation.judge import JudgeInput, judge_trace
from stem_agent.evolution import EvolutionProposalInput, propose_evolution
from stem_agent.workflows.baseline import run_baseline
from stem_agent.workflows.evolved import run_evolved


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

    genome_parser = subparsers.add_parser(
        "validate-genome",
        help="Validate an evolved agent genome against the project schema.",
    )
    genome_parser.add_argument(
        "--genome",
        default="configs/evolved_deep_research_agent_v5.yaml",
        help="Path to the candidate agent genome.",
    )
    genome_parser.add_argument(
        "--schema",
        default="configs/genome_schema.yaml",
        help="Path to the genome schema contract.",
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

    evolved_parser = subparsers.add_parser(
        "run-evolved",
        help="Run the evolved deep-research agent for one question.",
    )
    evolved_input = evolved_parser.add_mutually_exclusive_group(required=True)
    evolved_input.add_argument(
        "--question",
        help="Research question to answer.",
    )
    evolved_input.add_argument(
        "--question-id",
        help="Question ID from evals/questions.json, for example DR-001.",
    )
    evolved_parser.add_argument(
        "--genome",
        default="configs/evolved_deep_research_agent_v5.yaml",
        help="Path to the evolved agent genome.",
    )
    evolved_parser.add_argument(
        "--schema",
        default="configs/genome_schema.yaml",
        help="Path to the genome schema contract.",
    )
    evolved_parser.add_argument(
        "--trace-dir",
        default="results/traces",
        help="Directory where the run trace JSON will be written.",
    )
    evolved_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the evolved runner without calling the OpenAI API.",
    )

    score_parser = subparsers.add_parser(
        "score-trace",
        help="Score one agent trace against the fixed evaluation rubric.",
    )
    score_parser.add_argument(
        "--trace",
        required=True,
        help="Path to a trace JSON file.",
    )
    score_parser.add_argument(
        "--question-id",
        help="Question ID from evals/questions.json. Inferred when omitted.",
    )
    score_parser.add_argument(
        "--questions",
        default="evals/questions.json",
        help="Path to the fixed question set.",
    )
    score_parser.add_argument(
        "--rubric",
        default="evals/rubric.yaml",
        help="Path to the scoring rubric.",
    )
    score_parser.add_argument(
        "--output",
        help="Optional path where the score JSON should be written.",
    )

    judge_parser = subparsers.add_parser(
        "judge-trace",
        help="Run a stricter model-assisted evaluation for one trace.",
    )
    judge_parser.add_argument(
        "--trace",
        required=True,
        help="Path to a trace JSON file.",
    )
    judge_parser.add_argument(
        "--question-id",
        help="Question ID from evals/questions.json. Inferred when omitted.",
    )
    judge_parser.add_argument(
        "--questions",
        default="evals/questions.json",
        help="Path to the fixed question set.",
    )
    judge_parser.add_argument(
        "--rubric",
        default="evals/rubric.yaml",
        help="Path to the scoring rubric.",
    )
    judge_parser.add_argument(
        "--model",
        help="Judge model. Defaults to OPENAI_EVAL_MODEL, then OPENAI_MODEL.",
    )
    judge_parser.add_argument(
        "--output",
        help="Optional path where the judge JSON should be written.",
    )
    judge_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate judge wiring without calling the OpenAI API.",
    )

    batch_parser = subparsers.add_parser(
        "run-eval-batch",
        help="Run an evaluation batch across the fixed question set.",
    )
    batch_parser.add_argument(
        "--agent",
        default="baseline_web",
        choices=[
            "baseline_no_web",
            "baseline_web",
            "baseline",
            "evolved_deep_research_v1",
            "evolved_deep_research_v2",
            "evolved_deep_research_v3",
            "evolved_deep_research_v4",
            "evolved_deep_research_v5",
            "evolved_v1",
            "evolved_v2",
            "evolved_v3",
            "evolved_v4",
            "evolved_v5",
            "evolved",
        ],
        help=(
            "Agent variant to evaluate. 'baseline' aliases baseline_web; "
            "'evolved' aliases the current evolved candidate."
        ),
    )
    batch_parser.add_argument(
        "--run-id",
        help="Stable run ID. Defaults to a timestamped ID.",
    )
    batch_parser.add_argument(
        "--questions",
        default="evals/questions.json",
        help="Path to the fixed question set.",
    )
    batch_parser.add_argument(
        "--rubric",
        default="evals/rubric.yaml",
        help="Path to the scoring rubric.",
    )
    batch_parser.add_argument(
        "--config",
        help="Optional path to an agent config. Defaults depend on --agent.",
    )
    batch_parser.add_argument(
        "--schema",
        help="Optional path to the evolved-agent genome schema.",
    )
    batch_parser.add_argument(
        "--output-root",
        default="results",
        help="Root directory for batch artifacts.",
    )
    batch_parser.add_argument(
        "--judge-model",
        help="Judge model. Defaults to OPENAI_EVAL_MODEL, then OPENAI_MODEL.",
    )
    batch_parser.add_argument(
        "--limit",
        type=int,
        help="Evaluate only the first N questions. Useful for smoke tests.",
    )
    batch_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without OpenAI calls. Baseline and judge both use dry-run mode.",
    )
    batch_parser.add_argument(
        "--confirm-live",
        action="store_true",
        help="Required for non-dry-run batches because they spend API calls.",
    )

    evolve_parser = subparsers.add_parser(
        "evolve",
        help="Propose the next genome from saved evaluation artifacts.",
    )
    evolve_parser.add_argument(
        "--from-run",
        required=True,
        help="Run directory containing summary.json, traces/, heuristic/, and judge/.",
    )
    evolve_parser.add_argument(
        "--base-genome",
        default="configs/evolved_deep_research_agent_v5.yaml",
        help="Genome to use as the parent for the proposed candidate.",
    )
    evolve_parser.add_argument(
        "--schema",
        default="configs/genome_schema.yaml",
        help="Path to the genome schema contract.",
    )
    evolve_parser.add_argument(
        "--output-dir",
        help=(
            "Directory for proposal.md and candidate_genome.yaml. Defaults to "
            "results/evolution_proposals/<run-id>."
        ),
    )
    evolve_parser.add_argument(
        "--candidate-id",
        help="Optional genome.id for the proposed candidate.",
    )
    evolve_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze artifacts and print the proposal target without writing files.",
    )

    return parser


def print_status() -> None:
    expected_paths = [
        "configs",
        "configs/base_agent.yaml",
        "configs/baseline_no_web.yaml",
        "configs/evolved_deep_research_agent.yaml",
        "configs/evolved_deep_research_agent_v1.yaml",
        "configs/evolved_deep_research_agent_v2.yaml",
        "configs/evolved_deep_research_agent_v3.yaml",
        "configs/evolved_deep_research_agent_v4.yaml",
        "configs/evolved_deep_research_agent_v5.yaml",
        "configs/genome_schema.yaml",
        "docs",
        "docs/evaluation_plan.md",
        "evals",
        "evals/questions.json",
        "evals/rubric.yaml",
        "results/traces",
        "src/stem_agent/core",
        "src/stem_agent/tools",
        "src/stem_agent/workflows",
        "src/stem_agent/workflows/evolved.py",
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


def load_question_item_by_id(question_id: str) -> dict[str, object]:
    questions_path = PROJECT_ROOT / "evals" / "questions.json"
    with questions_path.open(encoding="utf-8") as file:
        payload = json.load(file)

    for item in payload["questions"]:
        if item["id"] == question_id:
            return item

    known_ids = ", ".join(item["id"] for item in payload["questions"])
    raise ValueError(f"Unknown question ID {question_id!r}. Known IDs: {known_ids}")


def load_question_by_id(question_id: str) -> str:
    return str(load_question_item_by_id(question_id)["question"])


def run_baseline_command(args: argparse.Namespace) -> None:
    question = args.question or load_question_by_id(args.question_id)
    settings = load_settings(PROJECT_ROOT)
    result = run_baseline(
        question=question,
        config_path=resolve_cli_path(args.config),
        trace_dir=resolve_cli_path(args.trace_dir),
        settings=settings,
        dry_run=args.dry_run,
    )

    print(result.answer)
    print(f"\nTrace written to: {result.trace_path}")


def run_evolved_command(args: argparse.Namespace) -> None:
    question_item = (
        load_question_item_by_id(args.question_id) if args.question_id else None
    )
    question = args.question or str(question_item["question"])
    settings = load_settings(PROJECT_ROOT)
    result = run_evolved(
        question=question,
        genome_path=resolve_cli_path(args.genome),
        schema_path=resolve_cli_path(args.schema),
        trace_dir=resolve_cli_path(args.trace_dir),
        settings=settings,
        dry_run=args.dry_run,
        question_metadata=question_item,
    )

    print(result.answer)
    print(f"\nTrace written to: {result.trace_path}")


def resolve_cli_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def validate_genome_command(args: argparse.Namespace) -> None:
    result = validate_genome_files(
        genome_path=resolve_cli_path(args.genome),
        schema_path=resolve_cli_path(args.schema),
    )
    print(format_validation_result(result))
    if not result.valid:
        raise RuntimeError("Genome validation failed.")


def default_evolution_output_dir(run_dir: Path) -> Path:
    return PROJECT_ROOT / "results" / "evolution_proposals" / run_dir.name


def evolve_command(args: argparse.Namespace) -> None:
    run_dir = resolve_cli_path(args.from_run)
    output_dir = (
        resolve_cli_path(args.output_dir)
        if args.output_dir
        else default_evolution_output_dir(run_dir)
    )
    result = propose_evolution(
        EvolutionProposalInput(
            run_dir=run_dir,
            base_genome_path=resolve_cli_path(args.base_genome),
            schema_path=resolve_cli_path(args.schema),
            output_dir=output_dir,
            candidate_id=args.candidate_id,
            dry_run=args.dry_run,
        )
    )

    print("Evolution proposal complete")
    print(f"Run ID: {result['run_id']}")
    print(f"Base genome: {result['base_genome']}")
    print(f"Candidate ID: {result['candidate_id']}")
    print(f"Output dir: {result['output_dir']}")
    print(f"Proposal: {result['proposal_path']}")
    print(f"Candidate genome: {result['candidate_path']}")
    print(f"Validation: {result['validation']}")


def score_trace_command(args: argparse.Namespace) -> None:
    evaluation = evaluate_trace(
        EvaluationInput(
            trace_path=resolve_cli_path(args.trace),
            questions_path=resolve_cli_path(args.questions),
            rubric_path=resolve_cli_path(args.rubric),
            question_id=args.question_id,
        )
    )

    if args.output:
        output_path = resolve_cli_path(args.output)
        write_evaluation(output_path, evaluation)
        print(f"Evaluation written to: {output_path}")

    metrics = evaluation["metrics"]
    print("Trace evaluation")
    print(f"Question: {evaluation['question_id']}")
    print(f"Overall score: {evaluation['overall_score']}")
    print(f"Coverage: {metrics['coverage_score']}")
    print(f"Citation support: {metrics['citation_support_score']}")
    print(f"Source quality: {metrics['source_quality_score']}")
    print(f"Unsupported claims: {metrics['unsupported_claim_count']}")
    print(f"Failure tags: {', '.join(evaluation['failure_tags']) or 'none'}")


def judge_trace_command(args: argparse.Namespace) -> None:
    settings = load_settings(PROJECT_ROOT)
    judge_model = args.model or settings.openai_eval_model or settings.openai_model
    if not judge_model:
        raise RuntimeError(
            "A judge model is required. Set OPENAI_EVAL_MODEL or pass --model."
        )

    evaluation = judge_trace(
        JudgeInput(
            trace_path=resolve_cli_path(args.trace),
            questions_path=resolve_cli_path(args.questions),
            rubric_path=resolve_cli_path(args.rubric),
            question_id=args.question_id,
            output_path=resolve_cli_path(args.output) if args.output else None,
            settings=settings,
            judge_model=judge_model,
            dry_run=args.dry_run,
        )
    )

    judge = evaluation["judge_evaluation"]
    print("Model-assisted trace evaluation")
    print(f"Question: {evaluation['question_id']}")
    print(f"Heuristic score: {evaluation['heuristic_score']}")
    print(f"Judge score: {evaluation['judge_score']}")
    print(f"Final score: {evaluation['final_score']}")
    print(f"Judge model: {evaluation['judge_model']}")
    print(f"Summary: {judge['summary']}")
    print(f"Recommended fix: {judge['recommended_fix']}")


def run_eval_batch_command(args: argparse.Namespace) -> None:
    if not args.dry_run and not args.confirm_live:
        raise RuntimeError(
            "Live batch evaluation makes OpenAI calls for each question and "
            "judge. Re-run with --confirm-live or use --dry-run."
        )

    settings = load_settings(PROJECT_ROOT)
    judge_model = (
        args.judge_model or settings.openai_eval_model or settings.openai_model
    )
    if not judge_model:
        raise RuntimeError(
            "A judge model is required. Set OPENAI_EVAL_MODEL or pass --judge-model."
        )

    run_id = args.run_id or default_run_id(args.agent, args.dry_run)
    config_path = (
        resolve_cli_path(args.config)
        if args.config
        else PROJECT_ROOT / default_config_path(args.agent)
    )
    schema_path = (
        resolve_cli_path(args.schema)
        if args.schema
        else PROJECT_ROOT / default_schema_path()
    )
    summary = run_evaluation_batch(
        BatchInput(
            agent=args.agent,
            run_id=run_id,
            output_root=resolve_cli_path(args.output_root),
            questions_path=resolve_cli_path(args.questions),
            rubric_path=resolve_cli_path(args.rubric),
            config_path=config_path,
            schema_path=schema_path,
            settings=settings,
            judge_model=judge_model,
            dry_run=args.dry_run,
            limit=args.limit,
        )
    )

    print("Evaluation batch complete")
    print(f"Run ID: {summary['run_id']}")
    print(f"Artifact root: {summary['artifact_root']}")
    print(f"Questions: {summary['question_count']}")
    print(f"Heuristic avg: {summary['aggregate']['heuristic_score_avg']}")
    print(f"Judge avg: {summary['aggregate']['judge_score_avg']}")
    print(f"Final avg: {summary['aggregate']['final_score_avg']}")
    print("Usage totals:")
    print(json.dumps(summary["usage_totals"], indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "status":
        print_status()
        return

    if args.command == "eval-info":
        print_eval_info()
        return

    if args.command == "validate-genome":
        try:
            validate_genome_command(args)
        except (OSError, RuntimeError, ValueError) as exc:
            parser.exit(1, f"error: {exc}\n")
        return

    if args.command == "run-baseline":
        try:
            run_baseline_command(args)
        except RuntimeError as exc:
            parser.exit(1, f"error: {exc}\n")
        return

    if args.command == "run-evolved":
        try:
            run_evolved_command(args)
        except (OSError, RuntimeError, ValueError) as exc:
            parser.exit(1, f"error: {exc}\n")
        return

    if args.command == "score-trace":
        try:
            score_trace_command(args)
        except (OSError, RuntimeError, ValueError) as exc:
            parser.exit(1, f"error: {exc}\n")
        return

    if args.command == "judge-trace":
        try:
            judge_trace_command(args)
        except (OSError, RuntimeError, ValueError) as exc:
            parser.exit(1, f"error: {exc}\n")
        return

    if args.command == "run-eval-batch":
        try:
            run_eval_batch_command(args)
        except (OSError, RuntimeError, ValueError) as exc:
            parser.exit(1, f"error: {exc}\n")
        return

    if args.command == "evolve":
        try:
            evolve_command(args)
        except (OSError, RuntimeError, ValueError) as exc:
            parser.exit(1, f"error: {exc}\n")
        return

    parser.print_help()
