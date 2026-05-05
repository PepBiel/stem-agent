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

Model-only baseline:

```text
question -> answer from model knowledge -> state uncertainty
```

Web-search baseline:

```text
question -> search/read top sources -> summarize
```

Evolved deep research agent:

```text
question -> decompose -> search plan -> source triage -> evidence extraction
         -> coverage check -> contradiction check -> synthesis -> citation audit
```

The final submission will compare model-only, web-search, and evolved-agent
runs using a fixed set of technical research questions and measurable signals
such as coverage, citation support, source quality, unsupported claims, latency,
and cost. This makes the value of retrieval separate from the value of the
specialized agent workflow.

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

The project currently has model-only and web-search baseline variants, saved
traces, a transparent heuristic scorer, and a stricter model-assisted judge. The
project also defines the first evolved deep-research genome, validates it, and
can execute it through an evolved-agent runner that writes workflow artifacts.

Smoke check:

```bash
python -m stem_agent status
python -m stem_agent eval-info
python -m stem_agent validate-genome
```

`validate-genome` checks `configs/evolved_deep_research_agent_v5.yaml` against
`configs/genome_schema.yaml`. This is the contract that keeps specialization
controlled: the evolved agent can change workflow and prompts, but it must stay
inside fixed tool, budget, trace, and evaluation boundaries.

The evolved genome variants are kept as explicit configs so the project can
compare the specialization path without rewriting history:

```text
configs/evolved_deep_research_agent_v1.yaml  inferred coverage, original budget
configs/evolved_deep_research_agent_v2.yaml  fixed coverage injection, original budget
configs/evolved_deep_research_agent_v3.yaml  fixed coverage injection, tuned budget
configs/evolved_deep_research_agent_v4.yaml  v2 budget plus source quality discipline
configs/evolved_deep_research_agent_v5.yaml  v4 plus raw URL citation contract
configs/evolved_deep_research_agent.yaml     earlier default candidate kept for history
```

Version 5 is the current best full-batch candidate. It started as a targeted
fix after the v4 run: v4 produced the best aggregate quality so far, but DR-002
exposed a citation-contract failure where the answer used provider/internal
citation markers instead of raw URLs. v5 keeps v4's source-quality policy,
requires literal raw URLs on claim lines, and filters final trace citations to
answer/evidence/accepted-source artifacts. In the full live batch, v5 improved
both quality and cost relative to v4.

```text
evolved_v5 full live: heuristic 0.9492, judge 0.8073, final 0.8569, tokens 354487
```

Run the evolved agent without spending API credits:

```bash
python -m stem_agent run-evolved --question-id DR-001 --dry-run
python -m stem_agent run-evolved --question-id DR-001 --genome configs/evolved_deep_research_agent_v1.yaml --dry-run
python -m stem_agent run-evolved --question-id DR-001 --genome configs/evolved_deep_research_agent_v2.yaml --dry-run
python -m stem_agent run-evolved --question-id DR-001 --genome configs/evolved_deep_research_agent_v3.yaml --dry-run
python -m stem_agent run-evolved --question-id DR-001 --genome configs/evolved_deep_research_agent_v4.yaml --dry-run
python -m stem_agent run-evolved --question-id DR-001 --genome configs/evolved_deep_research_agent_v5.yaml --dry-run
```

The evolved runner validates the genome before execution and writes trace
artifacts for decomposition, search planning, source triage, evidence
extraction, coverage audit, contradiction audit, citation audit, and the final
answer.

Run the baseline without spending API credits:

```bash
python -m stem_agent run-baseline --question-id DR-001 --dry-run
```

Run the baseline live:

```bash
python -m stem_agent run-baseline --question-id DR-001
```

By default this uses `configs/base_agent.yaml`, which enables the OpenAI
Responses API `web_search` tool. To run the model-only baseline for one
question, pass the no-web config explicitly:

```bash
python -m stem_agent run-baseline --question-id DR-001 --config configs/baseline_no_web.yaml
```

Live web-search runs require an API key with permission for Responses writes.

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

`evolved` currently aliases `evolved_v5`, the best full-batch candidate so far.
The raw results are recorded under
`results/runs/evolved_deep_research_v5/evolved_v5_full_live/`.

```bash
python -m stem_agent run-eval-batch --agent baseline_no_web --dry-run
python -m stem_agent run-eval-batch --agent baseline_web --dry-run
python -m stem_agent run-eval-batch --agent evolved --dry-run
python -m stem_agent run-eval-batch --agent evolved_v1 --run-id evolved_v1_dry_run --dry-run
python -m stem_agent run-eval-batch --agent evolved_v2 --run-id evolved_v2_dry_run --dry-run
python -m stem_agent run-eval-batch --agent evolved_v3 --run-id evolved_v3_dry_run --dry-run
python -m stem_agent run-eval-batch --agent evolved_v4 --run-id evolved_v4_dry_run --dry-run
python -m stem_agent run-eval-batch --agent evolved_v5 --run-id evolved_v5_dry_run --dry-run
```

Live batches require explicit confirmation because they make model calls for
each answer and each judge evaluation:

```bash
python -m stem_agent run-eval-batch --agent baseline_no_web --confirm-live
python -m stem_agent run-eval-batch --agent baseline_web --confirm-live
python -m stem_agent run-eval-batch --agent evolved --confirm-live
python -m stem_agent run-eval-batch --agent evolved_v1 --run-id evolved_v1_full_live --confirm-live
python -m stem_agent run-eval-batch --agent evolved_v2 --run-id evolved_v2_full_live --confirm-live
python -m stem_agent run-eval-batch --agent evolved_v3 --run-id evolved_v3_full_live --confirm-live
python -m stem_agent run-eval-batch --agent evolved_v4 --run-id evolved_v4_full_live --confirm-live
python -m stem_agent run-eval-batch --agent evolved_v5 --run-id evolved_v5_full_live --confirm-live
```

`baseline_no_web` makes one answer call per question plus one judge call per
question. `baseline_web` makes one answer call with `web_search` per question
plus one judge call per question. Each evolved live batch also makes one
evolved answer call with `web_search` per question plus one judge call per
question. The heuristic scorer is local in all cases.

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
