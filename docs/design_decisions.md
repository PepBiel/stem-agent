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

## 2026-05-04: Separate Model-Only And Web-Search Baselines

The first baseline with web search is useful, but it hides two effects: the
base model's prior knowledge and the value of fresh retrieval. The evaluation
therefore uses two explicit baseline variants:

- `baseline_no_web`: one model answer call, no external tools
- `baseline_web`: one answer call with the `web_search` tool

Rationale:

- gives the final write-up a stronger ablation story
- prevents the evolved agent from being compared only against a vague baseline
- makes cost and token usage easier to attribute
- shows whether retrieval alone explains most of the improvement

## 2026-05-04: Validate Genomes Before Execution

The evolved agent should not be introduced as free-form code or an unbounded
prompt. It is represented as a genome that must pass a project-level schema
before it can be executed.

Rationale:

- keeps specialization controlled and auditable
- makes workflow, prompts, tools, limits, trace events, and acceptance criteria
  visible before running expensive evaluations
- prevents mislabeled or unsafe candidate agents from entering the comparison
- gives the final write-up a concrete evolution artifact rather than only a
  better prompt

## 2026-05-05: Start With A Single-Call Evolved Runner

The first evolved runner executes the full validated workflow in one model call
while still requiring structured trace artifacts for each workflow stage.

Rationale:

- keeps the first evolved implementation cheap enough to smoke test
- makes the architecture observable before adding multi-call orchestration
- preserves a clear comparison against the web-search baseline
- leaves a natural future evolution step: split planning, evidence extraction,
  auditing, and synthesis into separate calls if the v1 trace shows value
