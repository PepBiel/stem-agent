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

## Current Status

Step 1 is the project scaffold. The next step is to define the baseline agent
and the initial evaluation shape before adding more complex evolution logic.

Smoke check:

```bash
python -m stem_agent status
```
