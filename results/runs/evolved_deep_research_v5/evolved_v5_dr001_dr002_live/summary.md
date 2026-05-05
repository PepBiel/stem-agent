# Evaluation Run: evolved_v5_dr001_dr002_live

- Agent: `evolved_deep_research_v5`
- Dry run: `False`
- Questions: `2`
- Heuristic average: `0.975`
- Judge average: `0.7708`
- Final average: `0.8422`

| Question | Heuristic | Judge | Final | Runtime |
|---|---:|---:|---:|---:|
| DR-001 | 1.0000 | 0.7083 | 0.8104 | 82.0 |
| DR-002 | 0.9500 | 0.8333 | 0.8741 | 94.0 |

## Usage

```json
{
  "agent": {
    "input_tokens": 79331,
    "input_tokens_details": {
      "cached_tokens": 4736
    },
    "output_tokens": 22096,
    "output_tokens_details": {
      "reasoning_tokens": 16452
    },
    "total_tokens": 101427
  },
  "judge": {
    "input_tokens": 7405,
    "input_tokens_details": {
      "cached_tokens": 0
    },
    "output_tokens": 3188,
    "output_tokens_details": {
      "reasoning_tokens": 384
    },
    "total_tokens": 10593
  },
  "combined": {
    "input_tokens": 86736,
    "input_tokens_details": {
      "cached_tokens": 4736
    },
    "output_tokens": 25284,
    "output_tokens_details": {
      "reasoning_tokens": 16836
    },
    "total_tokens": 112020
  }
}
```
