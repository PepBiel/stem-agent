# Evaluation Run: evolved_v2_full_live

- Agent: `evolved_deep_research_v2`
- Dry run: `False`
- Questions: `8`
- Heuristic average: `0.8935`
- Judge average: `0.724`
- Final average: `0.7833`

| Question | Heuristic | Judge | Final | Runtime |
|---|---:|---:|---:|---:|
| DR-001 | 0.8678 | 0.7500 | 0.7912 | 66.0 |
| DR-002 | 0.8875 | 0.7083 | 0.7710 | 77.0 |
| DR-003 | 0.9167 | 0.6667 | 0.7542 | 72.0 |
| DR-004 | 0.8071 | 0.6667 | 0.7158 | 38.0 |
| DR-005 | 0.9667 | 0.7500 | 0.8258 | 79.0 |
| DR-006 | 0.8929 | 0.7500 | 0.8000 | 66.0 |
| DR-007 | 0.8800 | 0.7917 | 0.8226 | 54.0 |
| DR-008 | 0.9294 | 0.7083 | 0.7857 | 81.0 |

## Usage

```json
{
  "agent": {
    "input_tokens": 257194,
    "input_tokens_details": {
      "cached_tokens": 37888
    },
    "output_tokens": 75022,
    "output_tokens_details": {
      "reasoning_tokens": 52426
    },
    "total_tokens": 332216
  },
  "judge": {
    "input_tokens": 35616,
    "input_tokens_details": {
      "cached_tokens": 0
    },
    "output_tokens": 12306,
    "output_tokens_details": {
      "reasoning_tokens": 875
    },
    "total_tokens": 47922
  },
  "combined": {
    "input_tokens": 292810,
    "input_tokens_details": {
      "cached_tokens": 37888
    },
    "output_tokens": 87328,
    "output_tokens_details": {
      "reasoning_tokens": 53301
    },
    "total_tokens": 380138
  }
}
```
