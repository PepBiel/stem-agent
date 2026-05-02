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
