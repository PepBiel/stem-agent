# Stem Agent

Applied AI engineering prototype for JetBrains AI Engineering Intern Task #1.

The project explores a constrained version of a "stem agent": a minimal agent
that specializes into a task-specific agent through an observable and
measurable process. The chosen domain is technical deep research about LLM
agents.

## Project Goal

The goal is not to build a universal autonomous agent. The goal is to show that
a small initial agent can analyze a narrow task domain, propose a specialized
agent configuration, validate it, and improve over a simple baseline on a fixed
evaluation set.

In this repository, specialization is represented as an **agent genome**:

- workflow steps
- allowed tools
- prompt roles
- memory policy
- safeguards
- stopping criteria
- evaluation rubric

This keeps evolution controlled and inspectable instead of allowing arbitrary
self-modifying code.

## Planned Comparison

Baseline:

```text
question -> search/read top sources -> summarize
```

Evolved deep research agent:

```text
question -> decompose -> search plan -> source triage -> evidence extraction
         -> coverage check -> contradiction check -> synthesis -> citation audit
```

The final submission will compare both agents using a fixed set of technical
research questions and measurable signals such as coverage, citation support,
source quality, unsupported claims, latency, and cost.

## Repository Layout

```text
stem-agent/
  src/stem_agent/       Python package and CLI entry points
  configs/              Agent genome YAML files
  evals/                Evaluation questions, rubrics, and runners
  results/              Experiment outputs and traces
  docs/                 Research notes, design decisions, and experiment log
```

## Setup

Requirements:

- Python 3.11+
- OpenAI API key for model-backed runs once the agents are implemented

Create a local environment:

```bash
python -m venv .venv
python -m pip install -e .
```

If you prefer `uv`:

```bash
uv venv
uv sync
```

Configure secrets locally:

```bash
cp .env.example .env
```

Then edit `.env` and set `OPENAI_API_KEY`. Never commit `.env`.

Recommended starting model:

```bash
OPENAI_MODEL=gpt-5.4-mini
OPENAI_EVAL_MODEL=gpt-5.4-mini
```

This keeps early experiments cheaper and faster. A stronger model can be used
later for final synthesis or citation auditing if the evaluation shows a real
need.

## Current Status

The project currently has a runnable baseline, saved traces, a transparent
heuristic scorer, and a stricter model-assisted judge. The next implementation
step is the stem agent that proposes and validates evolved genomes.

Smoke check:

```bash
python -m stem_agent status
python -m stem_agent eval-info
```

Run the baseline without spending API credits:

```bash
python -m stem_agent run-baseline --question-id DR-001 --dry-run
```

Run the baseline live:

```bash
python -m stem_agent run-baseline --question-id DR-001
```

Live runs use the OpenAI Responses API with the `web_search` tool, so the API
key must have permission for Responses writes.

Each run writes a JSON trace under `results/traces/`.

Score a trace against the fixed evaluation rubric:

```bash
python -m stem_agent score-trace --trace results/traces/<trace>.json
```

The automatic scorer is intentionally transparent. It estimates coverage,
citation support, source quality, unsupported claims, uncertainty handling, and
redundancy from the saved trace. Later evaluations will combine this with
manual or model-assisted review for the final before/after comparison.

Run the stricter model-assisted judge:

```bash
python -m stem_agent judge-trace --trace results/traces/<trace>.json
```

This second layer grades factual accuracy, real coverage, evidence quality,
uncertainty handling, engineer usefulness, and structure using the fixed rubric.
It exists because the heuristic scorer can overestimate answers that merely look
well-cited.

Run a full evaluation batch:

```bash
python -m stem_agent run-eval-batch --agent baseline --dry-run
```

Live batches require explicit confirmation because they make model calls for
each answer and each judge evaluation:

```bash
python -m stem_agent run-eval-batch --agent baseline --confirm-live
```

Batch artifacts are written under:

```text
results/runs/<agent>/<run_id>/
  traces/       raw agent traces per question
  heuristic/    automatic scorer outputs per question
  judge/        model-assisted judge outputs per question
  summary.json  aggregate metrics and usage totals
  summary.md    compact human-readable report
```

The summary includes token usage when the OpenAI API returns usage metadata.
