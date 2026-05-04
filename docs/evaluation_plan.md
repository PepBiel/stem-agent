# Evaluation Plan

## Objective

The evaluation should prove whether the evolved deep research agent improves
over the baseline. It must be fixed before the evolved agent is implemented so
the project does not quietly optimize the test after seeing results.

## Dataset

The fixed dataset is stored in `evals/questions.json`.

It contains eight technical research questions about LLM agents. Each question
has:

- a stable ID
- the user-facing research question
- required aspects that should be covered
- expected source types

The required aspects make coverage more measurable than a generic "good answer"
judgment.

## Baseline

The baseline is defined in `configs/base_agent.yaml`.

It is intentionally simple:

```text
question -> generate search queries -> collect top sources -> read sources
         -> summarize with citations
```

Limits are strict:

- at most two search queries
- at most four sources
- no long-term memory
- no contradiction checker
- no citation auditor

This gives the evolved agent room to improve through workflow, memory, source
triage, evidence extraction, and validation.

## Metrics

The rubric is stored in `evals/rubric.yaml`.

Primary automatic metrics:

- coverage score
- citation support score
- source quality score
- unsupported claim count
- contradiction handling score
- redundancy score

Secondary operational metrics:

- model calls
- sources read
- runtime
- estimated cost
- tool errors

Human or LLM-assisted rubric dimensions:

- factual accuracy
- coverage
- evidence quality
- uncertainty handling
- usefulness for an engineer
- conciseness and structure

## Automatic Scorer V0

The first implementation is a transparent heuristic scorer exposed through:

```bash
python -m stem_agent score-trace --trace results/traces/<trace>.json
```

It scores:

- coverage by matching `must_cover` terms from `evals/questions.json`
- citation support by checking whether answer claim lines include citations
- source quality by classifying cited source domains
- unsupported claim count from uncited claim lines
- contradiction/uncertainty handling from limitation and uncertainty language
- redundancy from repeated lines and repeated citations

This scorer is intentionally imperfect. Its purpose is to create a reproducible
first signal and expose detailed diagnostics. The final comparison should still
include manual or model-assisted review for factual accuracy and citation
correctness.

## Model-Assisted Judge V1

The v0 scorer overestimated a baseline answer because it checked citation
presence and source domains, not whether citations actually supported the
answer. The v1 judge adds a stricter semantic layer:

```bash
python -m stem_agent judge-trace --trace results/traces/<trace>.json
```

It asks a model to grade the saved answer with the fixed rubric:

- factual accuracy
- substantive coverage of each required aspect
- evidence and citation quality
- uncertainty handling
- usefulness for an engineer
- conciseness and structure

It also asks for:

- per-aspect coverage audit
- per-claim citation audit
- per-source quality audit
- failure tags
- a recommended fix

Official before/after reporting should separate:

- `heuristic_score`: cheap reproducible signal
- `judge_score`: stricter model-assisted rubric score
- `final_score`: weighted combination, currently 35% heuristic and 65% judge

The judge is still not perfect. It does not fetch every cited source itself, so
claim-level support remains an estimate from answer text and citation metadata.
That limitation should be disclosed in the final write-up.

## Batch Evaluation Runs

Evaluation runs should be stored as immutable-ish batches:

```bash
python -m stem_agent run-eval-batch --agent baseline --confirm-live
```

The command runs every fixed evaluation question through the selected agent,
scores every trace with the heuristic scorer, judges every trace with the
model-assisted evaluator, and writes an aggregate summary.

Artifact layout:

```text
results/runs/<agent>/<run_id>/
  traces/DR-001.json
  heuristic/DR-001.json
  judge/DR-001.json
  summary.json
  summary.md
```

The summary records:

- per-question `heuristic_score`, `judge_score`, and `final_score`
- runtime where available
- baseline token usage
- judge token usage
- combined token usage

This gives the final write-up both quality and efficiency metrics.

## Before/After Table

The final comparison should use this shape:

```text
Metric                         Baseline      Evolved      Delta
---------------------------------------------------------------
Coverage score                 TBD           TBD          TBD
Citation support score         TBD           TBD          TBD
Source quality score           TBD           TBD          TBD
Unsupported claims             TBD           TBD          TBD
Contradiction handling score    TBD           TBD          TBD
Human rubric average           TBD           TBD          TBD
Average runtime seconds         TBD           TBD          TBD
Estimated cost                  TBD           TBD          TBD
```

## Failure Analysis

Each failed or weak answer should be tagged with one or more failure tags from
the rubric:

- unsupported claim
- weak source
- missing required aspect
- citation mismatch
- hallucinated reference
- contradiction missed
- repetitive answer
- exceeded budget
- tool error

This is important for the write-up because JetBrains explicitly asks what
failed and what was surprising.
