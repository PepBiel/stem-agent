# Final Result Comparison

This file is the compact result index for the submitted stem-agent project.
Full discussion is in [`../docs/experiment_log.md`](../docs/experiment_log.md)
and the 4-page write-up is [`../write-up.pdf`](../write-up.pdf).

## Evaluation Setup

- Fixed evaluation set: [`../evals/questions.json`](../evals/questions.json)
- Rubric: [`../evals/rubric.yaml`](../evals/rubric.yaml)
- Questions: 8 technical deep-research questions (`DR-001` to `DR-008`)
- Answer model: `gpt-5.4-mini`
- Judge model: `gpt-5.4-mini`
- Final score: `0.35 * heuristic + 0.65 * judge`

The model-assisted judge is not treated as ground truth. It is used as a
consistent semantic rubric alongside deterministic diagnostics and saved traces.
The main evidence for specialization is the combination of score movement,
trace-level artifacts, and concrete failure fixes.

## Aggregate Results

| Agent | Run | Heuristic | Judge | Final | Combined tokens |
|---|---|---:|---:|---:|---:|
| Model-only baseline | [`baseline-no-web-2026-05-04t12-32-33-00-00-live`](runs/baseline_no_web/baseline-no-web-2026-05-04t12-32-33-00-00-live/summary.md) | 0.3277 | 0.4167 | 0.3856 | 34,514 |
| Web-search baseline | [`baseline-2026-05-04t11-44-15-00-00-live`](runs/baseline/baseline-2026-05-04t11-44-15-00-00-live/summary.md) | 0.8417 | 0.5833 | 0.6738 | 158,887 |
| Evolved v1 | [`evolved_v1_full_live`](runs/evolved_deep_research_v1/evolved_v1_full_live/summary.md) | 0.8133 | 0.5781 | 0.6604 | 306,817 |
| Evolved v2 | [`evolved_v2_full_live`](runs/evolved_deep_research_v2/evolved_v2_full_live/summary.md) | 0.8935 | 0.7240 | 0.7833 | 380,138 |
| Evolved v3 | [`evolved_v3_full_live`](runs/evolved_deep_research_v3/evolved_v3_full_live/summary.md) | 0.8164 | 0.6146 | 0.6852 | 193,890 |
| Evolved v4 | [`evolved_v4_full_live`](runs/evolved_deep_research_v4/evolved_v4_full_live/summary.md) | 0.8862 | 0.7552 | 0.8010 | 450,061 |
| Evolved v5 | [`evolved_v5_full_live`](runs/evolved_deep_research_v5/evolved_v5_full_live/summary.md) | 0.9492 | 0.8073 | 0.8569 | 354,487 |
| Evolved v5 JSON-fix confirmation | [`evolved_deep_research_v5-2026-05-05t21-35-46-00-00-live`](runs/evolved_deep_research_v5/evolved_deep_research_v5-2026-05-05t21-35-46-00-00-live/summary.md) | 0.9563 | 0.8073 | 0.8594 | 444,435 |

## Interpreting The Final Candidate

`evolved_v5_full_live` is the best-quality genome used for the main write-up
claim. It improved over the web-search baseline by:

| Comparison | Judge delta | Final delta | Token multiplier |
|---|---:|---:|---:|
| Evolved v5 vs web-search baseline | +0.2240 | +0.1831 | 2.23x |
| Evolved v5 vs evolved v4 | +0.0521 | +0.0559 | 0.79x |
| Evolved v5 vs evolved v2 | +0.0833 | +0.0736 | 0.93x |

The post-fix confirmation run is not treated as a new genome improvement. It
validates runner robustness after tolerant JSON recovery was added:

- 8/8 traces completed with `status: complete`
- 0/8 parse warnings
- 0/8 citation-contract warnings
- 0/8 traces with unsupported claim lines

The judge average stayed unchanged at `0.8073`, so the post-fix run supports
the same conclusion as the previous v5 run: v5 remains the final candidate, and
the JSON fix improves trace reliability rather than semantic answer quality.

## Specialization Path

| Version | Main change | Outcome |
|---|---|---|
| Baseline no web | Model-only answer, no retrieval | Poor evidence and citation behavior |
| Baseline web | Simple retrieve-and-summarize | Stronger baseline; retrieval helps a lot |
| v1 | Structured deep-research workflow | Observable but did not beat web baseline |
| v2 | Injected fixed required aspects | Quality improved, cost increased |
| v3 | Reduced budget and reasoning effort | Cheaper but less reliable |
| v4 | Added source-quality discipline | Better quality, but exposed citation-contract failure |
| v5 | Added raw URL citation contract and citation filtering | Fixed DR-002 and became final candidate |
| JSON parser fix | Tolerant recovery for almost-valid model JSON | Removed DR-003 parse-warning class |

## Representative Failure Fixes

### DR-002: Citation Contract Failure

`evolved_v4` produced provider/internal citation markers instead of raw URLs.
That caused unsupported claim lines despite a substantively useful answer.

| Metric | evolved v4 | evolved v5 |
|---|---:|---:|
| DR-002 final score | 0.5741 | 0.8785 |
| Citation support | 0.0000 | 1.0000 |
| Unsupported claim lines | 12 | 0 |

### DR-003: Trace Parser Robustness

The original v5 full run produced an almost-valid JSON response that the runner
did not recover cleanly. The answer quality was still strong, but trace
artifacts were less faithful than they should have been.

The runner now uses tolerant JSON recovery for valid leading JSON objects with
harmless trailing text. The confirmation run completed all traces without parse
warnings.

## Final Decision

Freeze `configs/evolved_deep_research_agent_v5.yaml` as the final evolved
genome. The project is ready to submit once the README, write-up, comparison
summary, and security scan are clean.

