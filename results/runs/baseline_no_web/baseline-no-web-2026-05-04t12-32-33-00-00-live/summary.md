# Evaluation Run: baseline-no-web-2026-05-04t12-32-33-00-00-live

- Agent: `baseline_no_web`
- Dry run: `False`
- Questions: `8`
- Heuristic average: `0.3277`
- Judge average: `0.4167`
- Final average: `0.3856`

| Question | Heuristic | Judge | Final | Runtime |
|---|---:|---:|---:|---:|
| DR-001 | 0.4000 | 0.4167 | 0.4109 | 6.0 |
| DR-002 | 0.2000 | 0.3750 | 0.3138 | 4.0 |
| DR-003 | 0.4000 | 0.4583 | 0.4379 | 6.0 |
| DR-004 | 0.3000 | 0.4167 | 0.3759 | 4.0 |
| DR-005 | 0.4000 | 0.3750 | 0.3838 | 8.0 |
| DR-006 | 0.3000 | 0.4167 | 0.3759 | 5.0 |
| DR-007 | 0.3500 | 0.5000 | 0.4475 | 6.0 |
| DR-008 | 0.2719 | 0.3750 | 0.3389 | 3.0 |

## Usage

```json
{
  "agent": {
    "input_tokens": 918,
    "input_tokens_details": {
      "cached_tokens": 0
    },
    "output_tokens": 4549,
    "output_tokens_details": {
      "reasoning_tokens": 218
    },
    "total_tokens": 5467
  },
  "judge": {
    "input_tokens": 22403,
    "input_tokens_details": {
      "cached_tokens": 0
    },
    "output_tokens": 6644,
    "output_tokens_details": {
      "reasoning_tokens": 647
    },
    "total_tokens": 29047
  },
  "combined": {
    "input_tokens": 23321,
    "input_tokens_details": {
      "cached_tokens": 0
    },
    "output_tokens": 11193,
    "output_tokens_details": {
      "reasoning_tokens": 865
    },
    "total_tokens": 34514
  }
}
```
