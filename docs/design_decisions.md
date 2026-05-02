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
