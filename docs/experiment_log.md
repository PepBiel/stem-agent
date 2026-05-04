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
