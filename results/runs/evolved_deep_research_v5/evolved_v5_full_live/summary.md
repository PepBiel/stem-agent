# Evaluation Run: evolved_v5_full_live

- Agent: `evolved_deep_research_v5`
- Dry run: `False`
- Questions: `8`
- Heuristic average: `0.9492`
- Judge average: `0.8073`
- Final average: `0.8569`

| Question | Heuristic | Judge | Final | Runtime |
|---|---:|---:|---:|---:|
| DR-001 | 0.9786 | 0.7083 | 0.8029 | 73.0 |
| DR-002 | 0.9625 | 0.8333 | 0.8785 | 46.0 |
| DR-003 | 0.9289 | 0.8750 | 0.8939 | 80.0 |
| DR-004 | 0.8917 | 0.8750 | 0.8808 | 47.0 |
| DR-005 | 1.0000 | 0.8750 | 0.9187 | 83.0 |
| DR-006 | 0.9750 | 0.7500 | 0.8288 | 75.0 |
| DR-007 | 0.8942 | 0.8750 | 0.8817 | 59.0 |
| DR-008 | 0.9625 | 0.6667 | 0.7702 | 56.0 |

## Usage

```json
{
  "agent": {
    "input_tokens": 242193,
    "input_tokens_details": {
      "cached_tokens": 39936
    },
    "output_tokens": 64258,
    "output_tokens_details": {
      "reasoning_tokens": 41987
    },
    "total_tokens": 306451
  },
  "judge": {
    "input_tokens": 36327,
    "input_tokens_details": {
      "cached_tokens": 0
    },
    "output_tokens": 11709,
    "output_tokens_details": {
      "reasoning_tokens": 993
    },
    "total_tokens": 48036
  },
  "combined": {
    "input_tokens": 278520,
    "input_tokens_details": {
      "cached_tokens": 39936
    },
    "output_tokens": 75967,
    "output_tokens_details": {
      "reasoning_tokens": 42980
    },
    "total_tokens": 354487
  }
}
```
