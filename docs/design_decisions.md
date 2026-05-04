# Design Decisions

This log records architectural decisions that affect the final JetBrains Task
#1 submission.

## 2026-05-02: Use Controlled Genome Evolution

The agent will not rewrite arbitrary source code. Instead, the stem agent will
evolve a constrained YAML genome describing workflow steps, tools, prompts,
memory policy, safeguards, stopping criteria, and evaluation settings.

Rationale:

- easier to validate
- easier to diff across evolution rounds
- easier to roll back
- clearer before/after comparison
- safer for a runnable public submission

## 2026-05-02: Keep The First Implementation Framework-Light

Related work suggests that stateful agent frameworks are useful, but the first
prototype should use explicit Python modules, YAML configs, JSON traces, and a
fixed evaluation set.

Rationale:

- easier to inspect for reviewers
- fewer setup risks
- clearer ownership of the stem-agent logic
- avoids hiding the core idea behind a framework abstraction
- leaves room to add LangGraph later if state management becomes complex

## 2026-05-02: Evaluate Research Quality At Claim And Source Level

Deep research systems fail when they produce polished reports with weak or
unsupported evidence. The evaluation should therefore score coverage, source
quality, citation support, unsupported claims, contradiction handling, and
redundancy rather than only final-answer fluency.

Rationale:

- aligns with agent evaluation literature
- prevents longer answers from winning by default
- makes failures useful for genome evolution
- gives the final write-up a stronger before/after story

## 2026-05-04: Use A Two-Layer Evaluator

The first heuristic scorer overestimated a baseline answer because it rewarded
surface signals such as citation presence and reputable domains. The official
comparison should therefore use two separate signals:

- a cheap heuristic score for transparent diagnostics
- a model-assisted judge score for semantic coverage, evidence quality, and
  usefulness

Rationale:

- keeps fast automatic checks available during development
- makes evaluator optimism visible instead of hidden
- allows the final write-up to discuss a real evaluation failure and correction
- reduces the chance that the evolved agent wins by formatting answers to match
  shallow heuristics

## 2026-05-04: Store Evaluations As Run Artifacts

Each full evaluation should write traces, heuristic scores, judge scores, and a
summary under a stable `results/runs/<agent>/<run_id>/` folder.

Rationale:

- avoids overwriting previous experiments
- makes before/after comparisons auditable
- lets the write-up cite exact run IDs
- captures token usage and runtime alongside quality metrics
- supports future comparison between baseline and evolved agents
