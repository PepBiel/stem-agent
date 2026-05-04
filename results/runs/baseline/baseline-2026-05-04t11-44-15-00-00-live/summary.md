# Evaluation Run: baseline-2026-05-04t11-44-15-00-00-live

- Agent: `baseline`
- Dry run: `False`
- Questions: `8`
- Heuristic average: `0.8417`
- Judge average: `0.5833`
- Final average: `0.6738`

| Question | Heuristic | Judge | Final | Runtime |
|---|---:|---:|---:|---:|
| DR-001 | 0.9200 | 0.5417 | 0.6741 | 52.0 |
| DR-002 | 0.8688 | 0.5000 | 0.6291 | 8.0 |
| DR-003 | 0.8300 | 0.6250 | 0.6967 | 9.0 |
| DR-004 | 0.8457 | 0.7083 | 0.7564 | 13.0 |
| DR-005 | 0.9222 | 0.7083 | 0.7832 | 13.0 |
| DR-006 | 0.7688 | 0.5000 | 0.5941 | 11.0 |
| DR-007 | 0.8650 | 0.7500 | 0.7903 | 11.0 |
| DR-008 | 0.7131 | 0.3333 | 0.4662 | 9.0 |

## Usage

```json
{
  "baseline": {
    "input_tokens": 114479,
    "input_tokens_details": {
      "cached_tokens": 33792
    },
    "output_tokens": 7517,
    "output_tokens_details": {
      "reasoning_tokens": 3287
    },
    "total_tokens": 121996
  },
  "judge": {
    "input_tokens": 26632,
    "input_tokens_details": {
      "cached_tokens": 0
    },
    "output_tokens": 10259,
    "output_tokens_details": {
      "reasoning_tokens": 632
    },
    "total_tokens": 36891
  },
  "combined": {
    "input_tokens": 141111,
    "input_tokens_details": {
      "cached_tokens": 33792
    },
    "output_tokens": 17776,
    "output_tokens_details": {
      "reasoning_tokens": 3919
    },
    "total_tokens": 158887
  }
}
```
