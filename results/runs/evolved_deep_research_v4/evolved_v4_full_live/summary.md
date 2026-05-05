# Evaluation Run: evolved_v4_full_live

- Agent: `evolved_deep_research_v4`
- Dry run: `False`
- Questions: `8`
- Heuristic average: `0.8862`
- Judge average: `0.7552`
- Final average: `0.801`

| Question | Heuristic | Judge | Final | Runtime |
|---|---:|---:|---:|---:|
| DR-001 | 0.9591 | 0.8333 | 0.8773 | 75.0 |
| DR-002 | 0.5571 | 0.5833 | 0.5741 | 88.0 |
| DR-003 | 0.9062 | 0.7500 | 0.8047 | 135.0 |
| DR-004 | 0.9182 | 0.8333 | 0.8630 | 59.0 |
| DR-005 | 0.9571 | 0.8333 | 0.8766 | 95.0 |
| DR-006 | 0.9167 | 0.7500 | 0.8083 | 69.0 |
| DR-007 | 0.9250 | 0.7500 | 0.8113 | 80.0 |
| DR-008 | 0.9500 | 0.7083 | 0.7929 | 84.0 |

## Usage

```json
{
  "agent": {
    "input_tokens": 311005,
    "input_tokens_details": {
      "cached_tokens": 37376
    },
    "output_tokens": 89987,
    "output_tokens_details": {
      "reasoning_tokens": 64209
    },
    "total_tokens": 400992
  },
  "judge": {
    "input_tokens": 36018,
    "input_tokens_details": {
      "cached_tokens": 0
    },
    "output_tokens": 13051,
    "output_tokens_details": {
      "reasoning_tokens": 999
    },
    "total_tokens": 49069
  },
  "combined": {
    "input_tokens": 347023,
    "input_tokens_details": {
      "cached_tokens": 37376
    },
    "output_tokens": 103038,
    "output_tokens_details": {
      "reasoning_tokens": 65208
    },
    "total_tokens": 450061
  }
}
```
