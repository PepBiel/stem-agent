# Stem Agent

Applied AI engineering prototype for JetBrains AI Engineering Intern Task #1.

This repository implements a constrained version of a **stem agent**: a minimal
agent that becomes specialized for a narrow task class through an observable,
validated, and evaluated process. The chosen task class is technical deep
research about LLM agents.

The project does not attempt to build a universal autonomous agent or arbitrary
self-modifying code. Specialization is represented as an auditable **agent
genome**: a YAML configuration that defines workflow steps, prompt roles,
allowed tools, memory policy, safeguards, trace requirements, stopping criteria,
and evaluation expectations.

## Submission Artifacts

- Final write-up: [`write-up.pdf`](write-up.pdf)
- Source write-up: [`write-up.tex`](write-up.tex)
- Result summary: [`results/comparison.md`](results/comparison.md)
- Full experiment log: [`docs/experiment_log.md`](docs/experiment_log.md)
- Final genome: [`configs/evolved_deep_research_agent_v5.yaml`](configs/evolved_deep_research_agent_v5.yaml)
- Evaluation set: [`evals/questions.json`](evals/questions.json)
- Evaluation rubric: [`evals/rubric.yaml`](evals/rubric.yaml)

## What Evolved

The baseline agents are intentionally simple:

```text
model-only baseline:
question -> answer from model knowledge -> state uncertainty

web-search baseline:
question -> search/read top sources -> summarize
```

The evolved deep-research agent specializes into a structured workflow:

```text
question
-> decompose
-> search plan
-> source triage
-> evidence extraction
-> coverage check
-> contradiction check
-> synthesis
-> citation audit
-> limitations
```

The tool boundary stays narrow: the evolved agent still only uses web search.
This makes the comparison about workflow specialization, not about adding more
tools.

## Main Result

The final comparison uses the same fixed 8-question evaluation set for every
agent version. Scores combine a transparent local heuristic layer with a
model-assisted judge. The judge is not treated as ground truth; it is one
semantic signal alongside trace-level diagnostics such as coverage, citation
support, source quality, unsupported claim lines, contradiction handling, token
usage, and saved workflow artifacts.

| Agent | Heuristic | Judge | Final | Combined tokens |
|---|---:|---:|---:|---:|
| Model-only baseline | 0.3277 | 0.4167 | 0.3856 | 34,514 |
| Web-search baseline | 0.8417 | 0.5833 | 0.6738 | 158,887 |
| Evolved v1 | 0.8133 | 0.5781 | 0.6604 | 306,817 |
| Evolved v2 | 0.8935 | 0.7240 | 0.7833 | 380,138 |
| Evolved v3 | 0.8164 | 0.6146 | 0.6852 | 193,890 |
| Evolved v4 | 0.8862 | 0.7552 | 0.8010 | 450,061 |
| Evolved v5 | 0.9492 | 0.8073 | 0.8569 | 354,487 |

The stronger evidence is not only the score improvement. The final agent leaves
inspectable traces for decomposition, source triage, evidence extraction,
coverage checking, contradiction handling, and citation auditing. It also fixes
specific failure modes discovered during evaluation:

- v3 reduced cost but lost reliability, especially on citation-audit tasks.
- v4 improved source discipline but exposed a raw-URL citation-contract failure
  on DR-002.
- v5 fixed that failure: DR-002 final score moved from 0.5741 to 0.8785, and
  citation support moved from 0.0000 to 1.0000.
- A later runner fix removed a DR-003 trace parsing failure without changing the
  genome.

See [`results/comparison.md`](results/comparison.md) for the compact result
table and links to the saved runs.

## Repository Layout

```text
stem-agent/
  src/stem_agent/       Python package and CLI entry points
  configs/              Baseline configs, genome schema, evolved genomes v1-v5
  evals/                Fixed question set and judge rubric
  results/              Saved runs, traces, heuristic scores, judge outputs
  docs/                 Research notes, design decisions, experiment log
```

## Setup

Requirements:

- Python 3.11+
- OpenAI API key for live model-backed runs

Create a local environment:

```bash
python -m venv .venv
python -m pip install -e .
```

Or with `uv`:

```bash
uv venv
uv sync
```

Configure secrets locally:

```bash
cp .env.example .env
```

Then edit `.env` and set:

```bash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4-mini
OPENAI_EVAL_MODEL=gpt-5.4-mini
```

Never commit `.env`.

## Smoke Checks

These commands do not require live model calls:

```bash
python -m stem_agent status
python -m stem_agent eval-info
python -m stem_agent validate-genome
python -m stem_agent run-eval-batch --agent evolved --dry-run
```

Compile the write-up:

```bash
pdflatex -interaction=nonstopmode -halt-on-error write-up.tex
pdflatex -interaction=nonstopmode -halt-on-error write-up.tex
```

## Running Agents

Run one baseline question without spending API credits:

```bash
python -m stem_agent run-baseline --question-id DR-001 --dry-run
```

Run one evolved question without spending API credits:

```bash
python -m stem_agent run-evolved --question-id DR-001 --dry-run
```

Run the final evolved genome explicitly:

```bash
python -m stem_agent run-evolved --question-id DR-001 --genome configs/evolved_deep_research_agent_v5.yaml --dry-run
```

Live one-question runs:

```bash
python -m stem_agent run-baseline --question-id DR-001
python -m stem_agent run-evolved --question-id DR-001 --genome configs/evolved_deep_research_agent_v5.yaml
```

Live web-search runs require an API key with OpenAI Responses API access.

## Evaluation Batches

Dry-run batches:

```bash
python -m stem_agent run-eval-batch --agent baseline_no_web --dry-run
python -m stem_agent run-eval-batch --agent baseline_web --dry-run
python -m stem_agent run-eval-batch --agent evolved --dry-run
```

Live batches require explicit confirmation because they make model calls for
answers and judge evaluations:

```bash
python -m stem_agent run-eval-batch --agent baseline_no_web --confirm-live
python -m stem_agent run-eval-batch --agent baseline_web --confirm-live
python -m stem_agent run-eval-batch --agent evolved --confirm-live
```

Run a historical genome version:

```bash
python -m stem_agent run-eval-batch --agent evolved_v1 --run-id evolved_v1_full_live --confirm-live
python -m stem_agent run-eval-batch --agent evolved_v2 --run-id evolved_v2_full_live --confirm-live
python -m stem_agent run-eval-batch --agent evolved_v3 --run-id evolved_v3_full_live --confirm-live
python -m stem_agent run-eval-batch --agent evolved_v4 --run-id evolved_v4_full_live --confirm-live
python -m stem_agent run-eval-batch --agent evolved_v5 --run-id evolved_v5_full_live --confirm-live
```

Batch artifacts are written under:

```text
results/runs/<agent>/<run_id>/
  traces/       raw agent traces per question
  heuristic/    automatic scorer outputs per question
  judge/        model-assisted judge outputs per question
  summary.json  aggregate metrics and usage totals
  summary.md    compact human-readable report
```

## Evaluation Design

The fixed dataset contains 8 technical research questions about LLM agents
(`DR-001` to `DR-008`). Each question includes required aspects and expected
source types.

The evaluation has two layers:

- **Heuristic scorer**: local and transparent. It checks coverage terms,
  citation support, source domains, unsupported claim lines, contradiction
  handling, redundancy, runtime, and token usage.
- **Model-assisted judge**: stricter semantic review using a fixed rubric:
  factual accuracy, substantive coverage, evidence quality, uncertainty
  handling, usefulness for an engineer, and structure.

The final score is:

```text
final = 0.35 * heuristic + 0.65 * judge
```

This is an engineering rubric, not a benchmark claim. The write-up reports
limitations and uses failure analysis rather than treating the judge score as
absolute truth.

## Reproducibility And Safety Notes

- `.env` is ignored and must stay local.
- Live runs may produce temporary signed URLs in raw web-search traces. Before
  committing traces, sanitize provider URLs that include credentials or
  signature query parameters.
- The committed final traces were sanitized after GitHub secret scanning found a
  temporary AWS signed URL in an earlier history.
- The repo keeps raw run artifacts to make the reported comparison auditable.
