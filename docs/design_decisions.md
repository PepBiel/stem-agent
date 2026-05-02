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
