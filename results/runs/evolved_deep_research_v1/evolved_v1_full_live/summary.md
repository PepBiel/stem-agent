# Evaluation Run: evolved_v1_full_live

- Agent: `evolved_deep_research_v1`
- Dry run: `False`
- Questions: `8`
- Heuristic average: `0.8133`
- Judge average: `0.5781`
- Final average: `0.6604`

| Question | Heuristic | Judge | Final | Runtime |
|---|---:|---:|---:|---:|
| DR-001 | 0.9071 | 0.5417 | 0.6696 | 77.0 |
| DR-002 | 0.7125 | 0.5833 | 0.6285 | 37.0 |
| DR-003 | 0.8786 | 0.6250 | 0.7138 | 77.0 |
| DR-004 | 0.8455 | 0.5833 | 0.6751 | 41.0 |
| DR-005 | 0.9500 | 0.7917 | 0.8471 | 52.0 |
| DR-006 | 0.6750 | 0.3750 | 0.4800 | 46.0 |
| DR-007 | 0.7542 | 0.6250 | 0.6702 | 60.0 |
| DR-008 | 0.7833 | 0.5000 | 0.5992 | 44.0 |

## Usage

```json
{
  "agent": {
    "input_tokens": 211109,
    "input_tokens_details": {
      "cached_tokens": 36864
    },
    "output_tokens": 54594,
    "output_tokens_details": {
      "reasoning_tokens": 33989
    },
    "total_tokens": 265703
  },
  "judge": {
    "input_tokens": 29552,
    "input_tokens_details": {
      "cached_tokens": 0
    },
    "output_tokens": 11562,
    "output_tokens_details": {
      "reasoning_tokens": 846
    },
    "total_tokens": 41114
  },
  "combined": {
    "input_tokens": 240661,
    "input_tokens_details": {
      "cached_tokens": 36864
    },
    "output_tokens": 66156,
    "output_tokens_details": {
      "reasoning_tokens": 34835
    },
    "total_tokens": 306817
  }
}
```
