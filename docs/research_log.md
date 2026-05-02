# Research and Engineering Log

This file collects useful references, design patterns, decisions, failures, and
open questions. The final write-up should only include the highest-signal
findings from this log.

## Current Direction

Build a constrained stem agent for technical deep research on LLM agents.

The stem agent should not rewrite arbitrary source code. It should evolve an
agent genome: workflow, tools, prompts, memory policy, safeguards, stopping
criteria, and evaluation settings.

## Timeline

### 2026-05-02: Research the space before implementation

Research question:

> What existing work should inform a stem agent that evolves into a deep
> research agent?

Sources inspected:

- ReAct: ICLR/OpenReview https://openreview.net/forum?id=WE_vluYUL-X;
  project https://react-lm.github.io/; preprint https://arxiv.org/abs/2210.03629
- Toolformer: NeurIPS/OpenReview https://openreview.net/forum?id=Yacmpz84TH;
  preprint https://arxiv.org/abs/2302.04761
- Reflexion: NeurIPS/OpenReview https://openreview.net/forum?id=vAElhFcKW6;
  code https://github.com/noahshinn024/reflexion; preprint https://arxiv.org/abs/2303.11366
- Self-Refine: NeurIPS/OpenReview https://openreview.net/forum?id=S37hOerQLB;
  project https://selfrefine.info/; preprint https://arxiv.org/abs/2303.17651
- Automated Design of Agentic Systems: ICLR/OpenReview https://openreview.net/forum?id=t9U3LW7JVX;
  project https://www.shengranhu.com/ADAS/; code https://github.com/ShengranHu/ADAS
- Agentic RAG survey: preprint https://arxiv.org/abs/2501.09136;
  institutional profile https://facultyprofile.csuohio.edu/en/publications/agentic-retrieval-augmented-generation-a-survey-on-agentic-rag-3/
- Survey on Evaluation of LLM-based Agents: CoRR/OpenReview https://openreview.net/forum?id=jXhAhTMewL;
  preprint https://arxiv.org/abs/2503.16416
- DeepResearcher: ACL Anthology / EMNLP 2025 https://aclanthology.org/2025.emnlp-main.22/;
  code https://github.com/GAIR-NLP/DeepResearcher; preprint https://arxiv.org/abs/2504.03160
- OpenAI Deep Research: https://openai.com/index/introducing-deep-research/
- LangGraph docs: https://docs.langchain.com/oss/python/langgraph/overview
- DSPy docs: https://dspy.ai/
- OpenAI Agents SDK docs: https://openai.github.io/openai-agents-python/

Source hygiene decision:

Use conference, OpenReview, ACL Anthology, official project pages, or official
repositories as primary links when available. Keep arXiv links as stable
preprint fallbacks. Do not cite paper aggregators in the final write-up unless
they are only used for discovery.

Evidence:

- ReAct motivates explicit reasoning/action workflows and interpretable tool-use
  traces.
- Reflexion and Self-Refine motivate feedback-driven improvement without model
  fine-tuning.
- Toolformer motivates treating tool selection and tool-call quality as explicit
  behavior to constrain and evaluate.
- ADAS is conceptually closest to the stem-agent idea, but its code-level search
  is too risky for a compact public assignment.
- Agentic RAG and DeepResearcher both support the view that deep research is
  more than search plus summary: it needs planning, source triage, iterative
  retrieval, cross-validation, and uncertainty handling.
- The agent evaluation survey supports using several metrics rather than one
  vague score.

Interpretation:

The project should not present itself as a new foundation-model training method.
It should present itself as an applied engineering prototype that safely adapts
agent architecture through structured configuration and measurable evaluation.

Decision:

Keep the implementation framework-light for now. Use explicit Python modules,
YAML genomes, JSON traces, and a fixed evaluation set. Reconsider LangGraph only
if the workflow state becomes difficult to manage.

## State Of The Art Notes

Detailed notes live in `docs/state_of_the_art.md`.

## Design Decisions

- Evolution means genome evolution, not arbitrary self-modifying code.
- Baseline and evaluation set are fixed before evolved-agent implementation.
- The evolved agent must justify itself through before/after metrics.
- Traces should capture structured decisions, tool calls, failures, and
  accept/reject decisions.

## Failures and Surprises

- Early risk: it is easy for this project to look like a manually designed deep
  research pipeline rather than a stem agent. The mitigation is to log candidate
  genomes, evaluator feedback, and accept/reject reasoning.
- ADAS is attractive but too broad if copied directly. The safer adaptation is a
  constrained search over config.
- Deep research evaluation can reward verbosity accidentally. The rubric must
  penalize unsupported claims and redundancy.

## Open Questions

- What trace schema is sufficient for the write-up?
- How much source text should be cached for citation auditing?
- Should the evaluator use a model, deterministic heuristics, or both?
- Should the first evolved genome be generated from scratch or from a template
  seeded by the research findings?

## Next Steps

1. Implement a minimal baseline runner.
2. Store baseline traces in `results/traces/`.
3. Implement a simple evaluator that can score fixed questions against the
   rubric.
4. Only then implement stem-agent genome generation.
