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

## 2026-05-05: Evolved Runner V1 Live Smoke On DR-001

Hypothesis:

A single live evolved-agent run should prove whether the model can follow the
validated genome contract in practice. The run should improve semantic quality
over the web-search baseline on the same question without silently breaking the
trace contract.

Command:

```bash
python -m stem_agent run-evolved --question-id DR-001
python -m stem_agent judge-trace \
  --trace results/traces/20260505T070439Z-evolved-live.json \
  --question-id DR-001 \
  --output results/evaluations/20260505-evolved-dr001-smoke-judge.json
```

Observed artifacts:

```text
results/traces/20260505T070439Z-evolved-live.json
results/evaluations/20260505-evolved-dr001-smoke-judge.json
```

Trace inspection:

- status: `complete`
- required events: 11/11 present
- all required event artifacts present
- web search calls: 7
- citations: 14
- decomposition subquestions: 4
- search queries: 4
- accepted sources: 6
- evidence items: 6
- unsupported claims in citation audit: 0
- weak citations in citation audit: 0

Results against the previous `baseline_web` DR-001 run:

| Metric | baseline_web DR-001 | evolved_v1 DR-001 | Delta |
|---|---:|---:|---:|
| Heuristic score | 0.9200 | 0.9500 | +0.0300 |
| Judge score | 0.5417 | 0.6250 | +0.0833 |
| Final score | 0.6741 | 0.7388 | +0.0647 |
| Combined tokens | 18597 | 40627 | +22030 |

Qualitative observations:

- The evolved runner followed the JSON/artifact contract well enough for a
  live trace.
- The model-assisted judge still found missing explicit coverage for
  over-trusting prior agent outputs, short-term vs long-term memory trade-offs,
  and concrete memory-evaluation methods.
- The token multiplier versus baseline_web on DR-001 is about 2.18x, which is
  above the genome's target budget of 1.8x.

Decision:

Do not run the full evolved batch yet. The live smoke is technically valid and
shows quality improvement, but the next evolution should tighten the prompt or
workflow so it explicitly covers required aspects and reduces cost before
spending a full 8-question batch.

## 2026-05-05: Evolved Genome V3 Coverage And Budget Tuning

Hypothesis:

The DR-001 smoke showed that evolved v1 improved quality but missed explicit
required aspects and exceeded the target token budget. Injecting the fixed
`must_cover` aspects into the evolved prompt and lowering the search/source
budget should improve judge score while keeping combined tokens under the
genome target of 1.8x `baseline_web`.

Changes:

- pass `evals/questions.json` metadata into `run-evolved` and evolved batch
  runs when a question ID is known
- record `evaluation_requirements.required_aspects` and
  `source_expectations` in evolved traces
- require each fixed aspect to appear in `decomposition.required_aspects`,
  `coverage_audit`, and the final answer's Required aspect coverage subsection
- tune `configs/evolved_deep_research_agent.yaml` to genome version 3
- lower `reasoning_effort` from `medium` to `low`
- lower `max_search_queries` from 4 to 2
- lower `max_sources` from 6 to 4

Commands:

```bash
python -m stem_agent run-evolved --question-id DR-001
python -m stem_agent score-trace \
  --trace results/traces/20260505T074337Z-evolved-live.json \
  --question-id DR-001
python -m stem_agent judge-trace \
  --trace results/traces/20260505T074337Z-evolved-live.json \
  --question-id DR-001 \
  --output results/evaluations/20260505-evolved-v3-dr001-smoke-judge.json
```

Intermediate result:

Genome version 2 improved explicit coverage but was rejected before judge
evaluation because the agent alone used 47339 tokens, worse than evolved v1.
Its trace is stored at:

```text
results/traces/20260505T073135Z-evolved-live.json
```

Version 3 result on DR-001:

```text
trace: results/traces/20260505T074337Z-evolved-live.json
judge: results/evaluations/20260505-evolved-v3-dr001-smoke-judge.json
```

| Metric | baseline_web DR-001 | evolved_v1 DR-001 | evolved_v3 DR-001 |
|---|---:|---:|---:|
| Heuristic score | 0.9200 | 0.9500 | 1.0000 |
| Judge score | 0.5417 | 0.6250 | 0.7083 |
| Final score | 0.6741 | 0.7388 | 0.8104 |
| Agent tokens | 13557 | 34665 | 24835 |
| Judge tokens | 5040 | 5962 | 4204 |
| Combined tokens | 18597 | 40627 | 29039 |

Trace inspection:

- genome version: 3
- web search calls: 4
- citations: 4
- evidence items: 6
- missing required aspects: 0
- unsupported claims in citation audit: 0
- weak citations in citation audit: 2

Decision:

Accept genome v3 as the current candidate for a broader evaluation smoke. It
beats the web baseline on DR-001, improves over evolved v1, and its combined
token multiplier versus `baseline_web` is about 1.56x, which is within the
target budget. Do not run the full 8-question live batch yet; first run a
2-question live batch to check whether the gain generalizes beyond memory
questions.

## 2026-05-05: Reproducible Evolved Genome Variants

Hypothesis:

The project should keep v1, v2, and v3 as runnable configurations so the final
write-up can show a real evolution path instead of only the latest candidate.
This also makes it possible to run a full 8-question live batch for any version
if the API budget allows it.

Changes:

- add `configs/evolved_deep_research_agent_v1.yaml`
- add `configs/evolved_deep_research_agent_v2.yaml`
- add `configs/evolved_deep_research_agent_v3.yaml`
- keep `configs/evolved_deep_research_agent.yaml` as the current default
- gate fixed evaluation requirement injection in the runner so it only applies
  to genomes with `genome.version >= 2`

Variant meaning:

| Variant | Internal behavior | Budget |
|---|---|---|
| v1 | Agent infers required aspects from the question | 4 search queries, 6 sources, medium reasoning |
| v2 | Runner injects fixed `must_cover` and `source_expectations` | 4 search queries, 6 sources, medium reasoning |
| v3 | Same fixed coverage injection as v2 | 2 search queries, 4 sources, low reasoning |

Validation commands:

```bash
python -m stem_agent validate-genome --genome configs/evolved_deep_research_agent_v1.yaml
python -m stem_agent validate-genome --genome configs/evolved_deep_research_agent_v2.yaml
python -m stem_agent validate-genome --genome configs/evolved_deep_research_agent_v3.yaml
```

Full live batch commands, if budget allows:

```bash
python -m stem_agent run-eval-batch --agent evolved_v1 --run-id evolved_v1_full_live --confirm-live
python -m stem_agent run-eval-batch --agent evolved_v2 --run-id evolved_v2_full_live --confirm-live
python -m stem_agent run-eval-batch --agent evolved_v3 --run-id evolved_v3_full_live --confirm-live
```

Decision:

Accept the three-version setup as the reproducibility layer for evolved-agent
comparison. The batch runner exposes `evolved_v1`, `evolved_v2`, and
`evolved_v3` aliases. Each variant has its own `agent.type`, so full live
results are stored under separate `results/runs/evolved_deep_research_v*/`
folders.

## 2026-05-05: Evolved Genome V4 Source Quality Discipline

Hypothesis:

The full 8-question results show that `evolved_v2` is the best quality
candidate so far, not `v3`. It achieved:

| Variant | Heuristic | Judge | Final | Combined tokens |
|---|---:|---:|---:|---:|
| baseline_web | 0.8417 | 0.5833 | 0.6738 | 158887 |
| evolved_v2 | 0.8935 | 0.7240 | 0.7833 | 380138 |
| evolved_v3 | 0.8164 | 0.6146 | 0.6852 | 193890 |

This means the next evolution should not primarily optimize cost. The right
move is to start from `v2`, keep its coverage-injected workflow and budget, and
target the error pattern that remains after `v2`: source quality and citation
discipline.

Evidence from `evolved_v2` judge summaries:

- DR-001: one summary claim was not directly supported.
- DR-002: specific tool-use and failure-mode claims were weakly grounded or
  partly inferential.
- DR-003: evidence quality was reduced by weaker or peripheral sources.
- DR-004: the judge explicitly recommended removing Wikipedia/Reddit and
  tightening source support.
- DR-005: the answer included unnecessary low-quality sources.
- DR-006: the judge recommended replacing weak blog/Reddit-style references.
- DR-007: the answer relied on weak or non-authoritative sources and slightly
  overstated what documentation proved.
- DR-008: several citations were broad or only loosely connected to the
  implementation-level claims.

Changes:

- add `configs/evolved_deep_research_agent_v4.yaml`
- add `evolved_v4` and `evolved_deep_research_v4` batch aliases
- make the default `evolved` batch alias point to `evolved_deep_research_v4`
- make `validate-genome` and `run-evolved` default to the v4 genome
- keep v4's budget close to v2:
  - 4 search queries
  - 6 accepted sources
  - medium reasoning
  - 5 model calls maximum
- add a `source_quality_policy` genome section with:
  - authority order for source triage
  - discouraged sources such as Reddit, Wikipedia, paper aggregators, and
    generic SEO-style posts
  - a minimum target of 4 authoritative accepted sources when budget allows it
  - direct-support requirements for failure modes, architecture comparisons,
    evaluation metrics, cost/latency/recovery claims, and engineering
    recommendations
- update the evolved runtime prompt for `genome.version >= 4` so the model must:
  - reject weak sources when authoritative replacements exist
  - use weak sources only as discovery leads unless unavoidable
  - label engineering inferences separately from directly sourced facts
  - fill `support_directness` and `source_authority` in the evidence table
  - flag broad, weak, or indirect citations in `citation_audit.weak_citations`

Decision:

Accept v4 as the next candidate to test, but not yet as the final best genome.
The comparison target for v4 is `evolved_v2`, not `v3`, because v2 currently
has the strongest accuracy signal. v4 should be accepted only if it preserves
or improves v2's judge/final score while improving source quality or reducing
weak citation failures without increasing token usage by more than about 10%.

Validation and smoke commands:

```bash
python -m stem_agent validate-genome --genome configs/evolved_deep_research_agent_v4.yaml
python -m stem_agent run-eval-batch --agent evolved_v4 --run-id evolved_v4_dry_run --dry-run
```

Full live batch command, if budget allows:

```bash
python -m stem_agent run-eval-batch --agent evolved_v4 --run-id evolved_v4_full_live --confirm-live
```

## 2026-05-05: Evolved V4 Full Live Batch Results

Run:

```bash
python -m stem_agent run-eval-batch --agent evolved_v4 --run-id evolved_v4_full_live --confirm-live
```

Artifacts:

```text
results/runs/evolved_deep_research_v4/evolved_v4_full_live/
```

Hypothesis:

Starting from `evolved_v2` and adding explicit source-quality discipline should
preserve or improve quality while reducing v2's repeated weak-citation and
loosely supported-claim failures. The comparison target is `evolved_v2`, because
v2 was the previous best-quality full-batch candidate.

Aggregate results:

| Agent | Heuristic | Judge | Final | Combined tokens | Runtime |
|---|---:|---:|---:|---:|---:|
| baseline_no_web | 0.3277 | 0.4167 | 0.3856 | 34514 | 42s |
| baseline_web | 0.8417 | 0.5833 | 0.6738 | 158887 | 126s |
| evolved_v1 | 0.8133 | 0.5781 | 0.6604 | 306817 | 434s |
| evolved_v2 | 0.8935 | 0.7240 | 0.7833 | 380138 | 533s |
| evolved_v3 | 0.8164 | 0.6146 | 0.6852 | 193890 | 167s |
| evolved_v4 | 0.8862 | 0.7552 | 0.8010 | 450061 | 685s |

Aggregate deltas:

| Comparison | Judge delta | Final delta | Token multiplier |
|---|---:|---:|---:|
| evolved_v4 vs baseline_web | +0.1719 | +0.1272 | 2.83x |
| evolved_v4 vs evolved_v2 | +0.0312 | +0.0177 | 1.18x |

Per-question final-score deltas:

| Question | baseline_web | evolved_v2 | evolved_v4 | v4 vs v2 | v4 vs web |
|---|---:|---:|---:|---:|---:|
| DR-001 | 0.6741 | 0.7912 | 0.8773 | +0.0861 | +0.2032 |
| DR-002 | 0.6291 | 0.7710 | 0.5741 | -0.1969 | -0.0550 |
| DR-003 | 0.6967 | 0.7542 | 0.8047 | +0.0505 | +0.1080 |
| DR-004 | 0.7564 | 0.7158 | 0.8630 | +0.1472 | +0.1066 |
| DR-005 | 0.7832 | 0.8258 | 0.8766 | +0.0508 | +0.0934 |
| DR-006 | 0.5941 | 0.8000 | 0.8083 | +0.0083 | +0.2142 |
| DR-007 | 0.7903 | 0.8226 | 0.8113 | -0.0113 | +0.0210 |
| DR-008 | 0.4662 | 0.7857 | 0.7929 | +0.0072 | +0.3267 |

What improved:

- `evolved_v4` is now the best-quality aggregate candidate: highest judge score
  and highest final score so far.
- It beats `baseline_web` on 7 of 8 questions and beats `evolved_v2` on 6 of 8
  questions.
- The largest gains over `v2` are DR-004 (+0.1472), DR-001 (+0.0861), DR-005
  (+0.0508), and DR-003 (+0.0505).
- Source-quality discipline appears to help the heuristic source-quality signal:
  average source quality increased from about 0.4627 in `v2` to about 0.5746
  in `v4`.
- `v4` eliminated most automatic unsupported-claim failures except DR-002.

What failed or remained weak:

- `v4` violates its own cost guardrail. The acceptance criterion allowed about
  1.10x `v2` tokens, but `v4` used 1.18x. Quality improved, but not cheaply.
- DR-002 regressed badly. Final score dropped from 0.7710 in `v2` to 0.5741 in
  `v4`, and also fell below `baseline_web`.
- The DR-002 heuristic failure is partly a citation-contract issue: the answer
  used model-internal citation markers such as `turn4view0` instead of literal
  `https://...` URLs, so the automatic scorer counted 12 unsupported claim
  lines.
- The DR-002 judge also found a real evidence problem: the answer made several
  reasonable architecture recommendations, but many were only weakly supported
  or inferential.
- Judge summaries still mention weak/secondary/broad sources in several
  questions. v4 improved the source policy, but it did not fully solve direct
  claim-to-source grounding.

Decision:

`evolved_v4` is the best-quality candidate so far, but it is not a clean final
acceptance under the project's own cost and citation-contract criteria.

Current interpretation:

- If prioritizing pure answer quality, `v4` is the current best agent.
- If enforcing the predefined acceptance criteria strictly, `v4` is a
  high-quality candidate that needs one more revision.
- `v2` remains the strongest previous accepted baseline for the evolved family,
  because it is cheaper and did not have the same DR-002 citation-contract
  failure.

Next step:

Create a small `v5`/`v4.1` fix focused only on the remaining failure mode:

- require literal raw URLs in every answer claim instead of provider citation
  markers;
- reject source aggregators from the final trace citations, not only from the
  source triage table;
- strengthen the prompt rule that recommendations must be labeled as
  inference unless directly supported;
- smoke test on DR-002 first before spending another full 8-question batch.

## 2026-05-05: Evolved V5 Citation Contract Fix

Hypothesis:

The v4 regression on DR-002 is not a reason to redesign the whole agent. The
aggregate v4 result is strong, and the failure is narrow: citation formatting
and rejected-source leakage. A targeted v5 should preserve v4's source-quality
discipline while making the citation contract explicit and machine-checkable.

Root cause:

- v4 told the model to use inline URLs, but it did not explicitly ban
  provider/internal citation markers such as `turn4view0`.
- The heuristic scorer only recognizes raw `http://`, `https://`, or Markdown
  links in claim lines. Provider markers therefore made otherwise sourced lines
  look unsupported.
- The evolved runner collected URLs recursively from every artifact. That meant
  URLs from `candidate_sources` and `source_triage.rejected_sources` could still
  appear in `trace.citations`, even when the agent had rejected them.
- The judge also found a real support problem on DR-002: several architecture
  recommendations were plausible but phrased more strongly than the evidence
  allowed.

Changes:

- add `configs/evolved_deep_research_agent_v5.yaml`
- make the default `evolved` alias point to `evolved_deep_research_v5`
- make `validate-genome` and `run-evolved` default to the v5 genome
- add a `citation_contract_policy` genome section requiring raw inline
  `https://...` URLs on key claim lines
- explicitly forbid provider/internal citation markers, numeric-only citations,
  and footnote-only citations as substitutes for raw URLs
- update the evolved runtime prompt so the Sources section alone does not count;
  important claim lines must carry their own raw URL
- change final trace citation extraction so it only reads URLs from:
  - final answer
  - evidence table
  - accepted sources
  - supported or weak citation-audit entries
- stop recursively collecting URLs from rejected-source artifacts
- add `citation_contract_warnings` to live traces when the final answer still
  contains provider citation markers or has trace citations but no raw answer
  URLs

Decision:

Accept v5 as the next candidate to validate, but only as a targeted fix. It
should be judged first on DR-001 and DR-002, because DR-002 is the observed
failure and `--limit 2` covers both questions in the fixed set. If DR-002
improves without damaging DR-001, then run the full 8-question v5 batch.

Validation commands:

```bash
python -m stem_agent validate-genome --genome configs/evolved_deep_research_agent_v5.yaml
python -m stem_agent run-eval-batch --agent evolved_v5 --run-id evolved_v5_dry_run --dry-run --limit 1
```

Recommended live smoke command:

```bash
python -m stem_agent run-eval-batch --agent evolved_v5 --run-id evolved_v5_dr001_dr002_live --limit 2 --confirm-live
```
