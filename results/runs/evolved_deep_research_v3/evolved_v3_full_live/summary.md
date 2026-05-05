# Evaluation Run: evolved_v3_full_live

- Agent: `evolved_deep_research_v3`
- Dry run: `False`
- Questions: `8`
- Heuristic average: `0.8164`
- Judge average: `0.6146`
- Final average: `0.6852`

| Question | Heuristic | Judge | Final | Runtime |
|---|---:|---:|---:|---:|
| DR-001 | 0.8106 | 0.5000 | 0.6087 | 19.0 |
| DR-002 | 0.6972 | 0.5833 | 0.6232 | 27.0 |
| DR-003 | 0.8833 | 0.6250 | 0.7154 | 20.0 |
| DR-004 | 0.8733 | 0.7917 | 0.8203 | 15.0 |
| DR-005 | 0.8208 | 0.6667 | 0.7206 | 28.0 |
| DR-006 | 1.0000 | 0.6667 | 0.7834 | 18.0 |
| DR-007 | 0.5100 | 0.4167 | 0.4494 | 19.0 |
| DR-008 | 0.9357 | 0.6667 | 0.7609 | 21.0 |

## Usage

```json
{
  "agent": {
    "input_tokens": 129563,
    "input_tokens_details": {
      "cached_tokens": 33152
    },
    "output_tokens": 23902,
    "output_tokens_details": {
      "reasoning_tokens": 5217
    },
    "total_tokens": 153465
  },
  "judge": {
    "input_tokens": 28998,
    "input_tokens_details": {
      "cached_tokens": 0
    },
    "output_tokens": 11427,
    "output_tokens_details": {
      "reasoning_tokens": 783
    },
    "total_tokens": 40425
  },
  "combined": {
    "input_tokens": 158561,
    "input_tokens_details": {
      "cached_tokens": 33152
    },
    "output_tokens": 35329,
    "output_tokens_details": {
      "reasoning_tokens": 6000
    },
    "total_tokens": 193890
  }
}
```
