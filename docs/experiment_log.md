# Experiment Log

Experiments will be recorded here as the project evolves.

Each experiment should include:

- date
- hypothesis
- command or script used
- configuration
- metrics
- failure notes
- follow-up decision

## 2026-05-02: Baseline Runner Smoke Test

Hypothesis:

The project needs a runnable baseline before implementing stem-agent evolution.
The first baseline should be intentionally simple and traceable.

Planned command:

```bash
python -m stem_agent run-baseline --question-id DR-001 --dry-run
```

Expected result:

- config loads from `configs/base_agent.yaml`
- question loads from `evals/questions.json`
- no OpenAI API call is made in dry-run mode
- a JSON trace is written to `results/traces/`

Follow-up:

After the dry-run path works, run one live baseline call and inspect whether the
trace captures answer text, citations, web search calls, model, config, and
limits.

Observed result:

- dry-run succeeded and wrote a trace
- live call reached the OpenAI SDK/API
- live call failed with a permissions error: the key is missing
  `api.responses.write`

Decision:

Keep the Responses API + `web_search` implementation because it matches the
baseline design and provides citations/sources. Improve error handling so this
failure is clear to future users. Before live evaluation, use a key that has
Responses API write permissions.

## 2026-05-04: Automatic Trace Scorer V0

Hypothesis:

Before implementing stem-agent evolution, the project needs a reproducible
automatic scorer that can turn saved traces into measurable metrics.

Planned command:

```bash
python -m stem_agent score-trace --trace results/traces/<trace>.json
```

Expected result:

- load a baseline or evolved-agent trace
- infer the evaluation question when possible
- compute coverage, citation support, source quality, unsupported claims,
  contradiction handling, and redundancy
- print a compact summary
- optionally write JSON results for later comparison

Known limitation:

The scorer is heuristic. It can identify missing terms or uncited claim lines,
but it cannot fully verify whether a citation truly supports a claim. That
claim-level audit should be added later as a stronger model-assisted evaluator.

Observed issue:

A baseline trace scored `0.9222` overall even though the answer was only a
compact high-level summary. This showed that the v0 scorer is useful as a smoke
test, but too weak as the main evaluation signal.

Decision:

Add a model-assisted judge before implementing the evolved agent. This prevents
the project from optimizing against a shallow evaluator.

## 2026-05-04: Model-Assisted Trace Judge V1

Hypothesis:

A stricter judge should reduce evaluator optimism by grading substantive
coverage, citation support, source relevance, uncertainty handling, and
engineering usefulness rather than only citation presence.

Planned command:

```bash
python -m stem_agent judge-trace --trace results/traces/<trace>.json
```

Expected result:

- run the heuristic scorer first
- call an evaluator model with the trace, question, rubric, citations, and
  extracted claim lines
- return structured JSON with rubric scores, coverage audit, citation audit,
  source audit, failure tags, summary, and recommended fix
- report separate `heuristic_score`, `judge_score`, and `final_score`

Decision criteria:

Use the judge score and final score for official before/after comparisons. Keep
the heuristic score as a transparent diagnostic.

Observed smoke result on `DR-001` baseline trace:

```text
heuristic_score: 0.9222
judge_score:     0.5417
final_score:     0.6749
```

Qualitative observation:

The judge identified the exact problem we wanted it to catch: the baseline was
directionally correct and well-cited, but only partially covered context
pollution, short-term vs long-term memory trade-offs, and evaluation methods,
and missed over-trusting previous agent outputs.

Decision:

Accept the judge as the main evaluation layer for now. Keep improving it later
with source fetching or claim-level verification if the evolved agent starts
gaming the prompt.

## 2026-05-04: Batch Evaluation Runner

Hypothesis:

The project needs evaluation artifacts grouped by run ID so baseline and evolved
agents can be compared question-by-question and by aggregate metrics.

Planned smoke command:

```bash
python -m stem_agent run-eval-batch --agent baseline --dry-run --limit 2
```

Planned live command:

```bash
python -m stem_agent run-eval-batch --agent baseline --confirm-live
```

Expected artifacts:

```text
results/runs/baseline/<run_id>/
  traces/
  heuristic/
  judge/
  summary.json
  summary.md
```

Metrics to inspect:

- per-question heuristic score
- per-question judge score
- per-question final score
- average scores
- baseline usage
- judge usage
- combined usage

Safety:

Live batch mode requires `--confirm-live` because it performs one baseline call
and one judge call per question.

Observed smoke result:

- `--dry-run --limit 2` generated the expected folder structure, summaries, and
  empty usage totals
- a non-dry-run batch without `--confirm-live` failed before making API calls
- no smoke batch artifacts were kept in `results/`

## 2026-05-04: Baseline Ablation Split

Hypothesis:

The final comparison will be more credible if it separates the value of model
prior knowledge from the value of web retrieval before introducing the evolved
agent.

Planned smoke commands:

```bash
python -m stem_agent run-eval-batch --agent baseline_no_web --dry-run --limit 2
python -m stem_agent run-eval-batch --agent baseline_web --dry-run --limit 2
```

Planned live commands:

```bash
python -m stem_agent run-eval-batch --agent baseline_no_web --confirm-live
python -m stem_agent run-eval-batch --agent baseline_web --confirm-live
```

Expected artifacts:

```text
results/runs/baseline_no_web/<run_id>/
results/runs/baseline_web/<run_id>/
```

Decision criteria:

Use both baselines in the final table. If the evolved agent only beats
`baseline_no_web` but not `baseline_web`, then the project has mostly shown the
value of retrieval, not specialization.

Observed smoke result:

- both dry-run commands generated the expected folder structure
- `baseline_no_web` traces recorded `tools_allowed: []` and
  `web_search_enabled: false`
- `baseline_web` traces recorded `web_search_enabled: true`
- a mismatched `--agent baseline_no_web --config configs/base_agent.yaml`
  command failed before writing a mislabeled batch
- a non-dry-run batch without `--confirm-live` failed before making API calls
- no smoke batch artifacts were kept in `results/`

## 2026-05-04: Baseline Live Ablation Results

Hypothesis:

Web search should improve answer quality over a model-only baseline, but it
should not solve the full deep-research problem because the workflow still lacks
source triage, evidence extraction, coverage checking, contradiction checking,
and citation auditing.

Observed live runs:

```text
baseline_no_web run:
results/runs/baseline_no_web/baseline-no-web-2026-05-04t12-32-33-00-00-live/

baseline_web run:
results/runs/baseline/baseline-2026-05-04t11-44-15-00-00-live/
```

Results:

| Metric | baseline_no_web | baseline_web | Delta |
|---|---:|---:|---:|
| Final avg | 0.3856 | 0.6738 | +0.2882 |
| Judge avg | 0.4167 | 0.5833 | +0.1666 |
| Combined tokens | 34514 | 158887 | +124373 |

Decision:

Accept the ablation as the baseline evidence. Web search is clearly useful, but
the judge summaries still point to missing coverage, weak decision criteria,
contradiction handling gaps, and citation-audit risk. The next step is a
controlled evolved genome that addresses those failures without widening the
tool boundary.

## 2026-05-04: Evolved Genome Contract V1

Hypothesis:

Before implementing a more capable agent runner, the project needs a validated
genome contract so specialization is explicit, bounded, and auditable.

Command:

```bash
python -m stem_agent validate-genome
```

Expected result:

- `configs/evolved_deep_research_agent.yaml` defines the first specialized
  deep-research genome
- `configs/genome_schema.yaml` defines required workflow steps, roles, tool
  boundaries, limits, trace events, and acceptance metrics
- the CLI validator fails if a candidate genome omits required pieces or
  exceeds budget/tool constraints

Decision criteria:

Accept this step if the candidate genome validates and the contract clearly
connects each new workflow stage to a baseline failure mode.

Observed result:

- `python -m stem_agent validate-genome` passed for
  `configs/evolved_deep_research_agent.yaml`
- `python -m stem_agent validate-genome --genome configs\baseline_no_web.yaml`
  failed with explicit schema errors, which confirms that baseline configs are
  not accidentally accepted as evolved genomes

Decision:

Accept the genome contract. The next implementation step is the evolved-agent
runner that executes this validated workflow and writes the required trace
events.

## 2026-05-05: Evolved Runner V1 Smoke Test

Hypothesis:

The first evolved runner should execute the validated genome without widening
the tool boundary, write trace artifacts for every required workflow stage, and
integrate with batch evaluation in dry-run mode before any live API spend.

Commands:

```bash
python -m stem_agent run-evolved --question-id DR-001 --dry-run
python -m stem_agent run-eval-batch --agent evolved --dry-run --limit 1
```

Expected result:

- the runner validates `configs/evolved_deep_research_agent.yaml` before
  execution
- the trace records `run_type: evolved` and `agent_type:
  evolved_deep_research_v1`
- the trace contains required events and artifacts for decomposition, search
  planning, source triage, evidence extraction, coverage audit, contradiction
  audit, citation audit, and final answer
- dry-run batch evaluation produces heuristic, judge, and summary artifacts
  under `results/runs/evolved_deep_research_v1/<run_id>/`

Observed result:

- `run-evolved --dry-run` wrote an evolved trace with the required workflow,
  validation metadata, events, artifacts, answer, and usage fields
- `run-eval-batch --agent evolved --dry-run --limit 1` completed and produced
  the expected batch summary
- live batch without `--confirm-live` failed before making API calls
- smoke artifacts were removed after verification

Decision:

Accept the v1 runner as the first executable evolved agent. The next step is a
small live smoke run on one question, then a full evolved batch only if the live
trace shape is correct.
