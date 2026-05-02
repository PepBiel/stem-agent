# State Of The Art Notes

This document maps the related work that informs the Stem Agent project. The
goal is not to produce a broad academic survey. The goal is to extract concrete
engineering patterns that justify the architecture, evaluation, and safeguards
used in this repository.

## Research Question

What existing work is closest to a constrained stem agent that specializes into
a deep research agent, and what should that work imply for the implementation?

## Summary

The literature points toward a controlled design:

- use explicit reasoning/action traces rather than opaque single-shot answers
- improve behavior through feedback, reflection, or configuration updates
- separate tool selection from arbitrary source-code modification
- treat retrieval as an iterative process, not a single search call
- evaluate agents on planning, tool use, memory, robustness, cost, and evidence
- preserve failures and traces because they explain why an architecture changed

This supports the project choice: evolve a constrained **agent genome** rather
than letting the agent rewrite arbitrary code.

## Key Sources

### ReAct: Synergizing Reasoning and Acting in Language Models

- Year: 2022
- Type: paper
- Link: https://arxiv.org/abs/2210.03629
- Core idea: interleave reasoning traces with actions so the model can use
  external tools while updating its plan.
- Why it matters: the baseline should not be a hidden one-shot summary; the
  evolved agent should expose a trace of decomposition, search, reading, and
  synthesis decisions.
- Implementation pattern: model the evolved workflow as explicit steps:
  decompose, search, inspect, update coverage, synthesize.
- Caveat: ReAct-style traces can become noisy, so this project should store
  concise structured traces rather than unrestricted chain-of-thought text.

### Toolformer: Language Models Can Teach Themselves to Use Tools

- Year: 2023
- Type: paper
- Link: https://arxiv.org/abs/2302.04761
- Core idea: models can learn when to call tools, what arguments to use, and how
  to incorporate tool outputs.
- Why it matters: tool use should be evaluated explicitly, not treated as magic.
- Implementation pattern: keep a tool registry and let genomes select from
  allowed tools under constraints.
- Caveat: Toolformer is about training/self-supervision; this project will not
  train a model, so tool selection must be implemented as bounded configuration.

### Reflexion: Language Agents with Verbal Reinforcement Learning

- Year: 2023
- Type: paper
- Link: https://arxiv.org/abs/2303.11366
- Core idea: agents can improve across attempts by turning feedback into
  verbal reflection stored in episodic memory, without updating model weights.
- Why it matters: the stem agent can use evaluation feedback to propose a better
  genome without fine-tuning.
- Implementation pattern: after each evolution round, record evaluator feedback,
  failed criteria, and a concise reflection that informs the next candidate
  genome.
- Caveat: reflective memory can accumulate misleading conclusions, so the memory
  should be scoped and tied to measured failures.

### Self-Refine: Iterative Refinement with Self-Feedback

- Year: 2023
- Type: paper
- Link: https://arxiv.org/abs/2303.17651
- Core idea: generate an output, critique it, and refine it iteratively using
  the same or similar model.
- Why it matters: evolution can be framed as generate genome -> critique with
  safeguards/evaluator -> refine genome.
- Implementation pattern: use short, bounded evolution rounds with explicit
  stopping criteria.
- Caveat: self-feedback alone can reinforce mistakes. The project should use
  external signals from the fixed evaluation set, not only model self-critique.

### Automated Design of Agentic Systems

- Year: 2024/2025
- Type: paper
- Link: https://arxiv.org/abs/2408.08435
- Core idea: a meta-agent can search over agentic system designs, including
  prompts, tools, workflows, and combinations of components.
- Why it matters: this is the closest conceptual neighbor to the stem-agent
  task.
- Implementation pattern: search over a constrained genome instead of arbitrary
  code generation.
- Caveat: the paper explores code-level agent discovery. For this assignment,
  unrestricted self-modifying code would make safety, reproducibility, and
  debugging worse.

### Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG

- Year: 2025/2026 revision
- Type: survey
- Link: https://arxiv.org/abs/2501.09136
- Core idea: agentic RAG extends static retrieve-then-generate pipelines with
  planning, tool use, reflection, multi-agent coordination, adaptive retrieval,
  and richer knowledge representations.
- Why it matters: deep research is naturally an agentic RAG task.
- Implementation pattern: compare a simple retrieve/summarize baseline against
  an evolved workflow with source triage, coverage checks, and citation audit.
- Caveat: agentic RAG adds complexity. The project should show whether each
  added step improves measurable evaluation signals.

### Survey on Evaluation of LLM-based Agents

- Year: 2025/2026 revision
- Type: survey
- Link: https://arxiv.org/abs/2503.16416
- Core idea: agent evaluation must cover capabilities such as planning, tool
  use, self-reflection, memory, robustness, cost-efficiency, and application
  performance.
- Why it matters: a single "quality" score is not enough for this project.
- Implementation pattern: keep multiple metrics: coverage, citation support,
  source quality, unsupported claims, contradiction handling, latency, and cost.
- Caveat: many agent benchmarks are still emerging, so a small custom eval set
  should be described honestly as task-specific rather than universal.

### DeepResearcher: Scaling Deep Research via Reinforcement Learning in Real-world Environments

- Year: 2025
- Type: paper
- Link: https://arxiv.org/abs/2504.03160
- Core idea: deep research agents benefit from real web interaction, planning,
  cross-validation, self-reflection, and honesty when definitive evidence is
  unavailable.
- Why it matters: the evolved agent should be judged on evidence quality and
  uncertainty handling, not only breadth.
- Implementation pattern: add source cross-checking, uncertainty notes, and
  citation-level validation to the evolved workflow.
- Caveat: the paper uses RL and real-world training. This project will only
  prototype the architecture and evaluation loop, not train a research model.

### OpenAI Deep Research

- Year: 2025
- Type: product/technical release notes
- Link: https://openai.com/index/introducing-deep-research/
- Core idea: deep research is positioned as multi-step internet research that
  searches, interprets, analyzes, and synthesizes many sources into documented
  reports.
- Why it matters: it validates the chosen task class as a real applied AI
  engineering problem.
- Implementation pattern: emphasize planning, source audit, citations, and
  report traceability.
- Caveat: OpenAI itself notes limitations around hallucinations, source
  authority, uncertainty calibration, formatting, and citation issues. These
  map directly to this project's evaluation criteria.

## Framework Notes

### LangGraph

- Type: framework documentation
- Link: https://docs.langchain.com/oss/python/langgraph/overview
- Useful idea: long-running stateful workflows, durable execution, memory,
  human-in-the-loop, and tracing are first-class concerns.
- Decision: keep the first implementation framework-light, but use LangGraph as
  a reference model for explicit graph steps and state transitions.

### DSPy

- Type: framework documentation
- Link: https://dspy.ai/
- Useful idea: treat LM behavior as modular programs that can be optimized
  against metrics instead of brittle prompt strings.
- Decision: do not introduce DSPy at the start. The genome idea can borrow its
  spirit: prompts/workflows are configurable and evaluated, not hand-waved.

### OpenAI Agents SDK

- Type: framework documentation
- Link: https://openai.github.io/openai-agents-python/
- Useful idea: agents, tools, handoffs, guardrails, sessions, and tracing are
  packaged as runtime primitives.
- Decision: keep custom code minimal at first. The trace format should still
  capture the same categories: model calls, tool calls, guardrail decisions,
  evaluator feedback, and final result.

## Patterns Extracted

1. Baseline first: every advanced workflow needs a simple comparison point.
2. Genome over source rewriting: evolution should modify structured config,
   not arbitrary code.
3. Explicit tool registry: the agent can only choose known tools with known
   limits.
4. Evaluate intermediate behavior: coverage, citations, tool errors, and source
   quality matter before final prose.
5. Bounded reflection: feedback should be stored as concise measured failure
   notes, not unlimited memory.
6. Trace every evolution round: record candidate genome, safeguards, smoke
   result, eval result, accept/reject decision, and reason.
7. Reward uncertainty: a research agent should admit when sources are weak or
   contradictory.
8. Penalize unsupported claims: citation audit should be central, not optional.

## Implications For This Project

The most defensible architecture is:

```text
fixed domain
-> baseline research agent
-> stem agent proposes candidate genome
-> validate genome against tool/schema/cost constraints
-> run smoke task
-> evaluate on fixed questions
-> accept if measurable improvement appears
-> otherwise rollback and refine
```

The write-up should frame the contribution as a controlled engineering
prototype inspired by ADAS, Reflexion, Self-Refine, ReAct, and agentic RAG, with
agent evaluation principles shaping the before/after comparison.

## Recommended Citations For The Write-up

Use a small set rather than citation padding:

- ReAct for reasoning/action traces
- Reflexion or Self-Refine for feedback-driven improvement
- ADAS for automated agent design
- Agentic RAG survey for deep research workflow framing
- Survey on Evaluation of LLM-based Agents for metrics
- DeepResearcher or OpenAI Deep Research for the deep research task class

## Open Questions

- How much of the evolved genome should be generated by the model versus seeded
  by templates?
- Should citation auditing be model-based, heuristic, or hybrid?
- How do we prevent the evolved agent from winning only by writing longer
  answers?
- What is the minimum trace format that is useful without leaking unnecessary
  chain-of-thought?
