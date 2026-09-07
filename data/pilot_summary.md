# AI Pilot Log Summary

Generated from `data/ai_logs/*.jsonl` — 3855 action rows across 60 trials, 3 scenarios. Every player runs a fixed `agents/coplayers.py` policy (random / cooperator / free_rider / tit_for_tat) — no LLM or RL policy involved yet. Regenerate with `python tasks.py pilot && python -m agents.pilot_summary`.

## Action distribution

| Scenario | gather | hoard | share | skip | Total |
|---|---|---|---|---|---|
| ALL | 2811 | 320 | 601 | 123 | 3855 |
| calm | 665 | 39 | 142 | 41 | 887 |
| drought | 677 | 39 | 130 | 41 | 887 |
| repeated_trust | 1469 | 242 | 329 | 41 | 2081 |

## Survival rate by scenario

| Scenario | Agent-trials | Survived | Survival rate |
|---|---|---|---|
| calm | 100 | 78 | 78.0% |
| drought | 100 | 75 | 75.0% |
| repeated_trust | 100 | 30 | 30.0% |

## Mean resource_after by round

**calm**

| Round | Mean resource_after | n |
|---|---|---|
| 1 | 3.63 | 100 |
| 2 | 4.28 | 100 |
| 3 | 4.63 | 100 |
| 4 | 5.43 | 90 |
| 5 | 6.06 | 87 |
| 6 | 6.58 | 86 |
| 7 | 7.20 | 84 |
| 8 | 8.00 | 82 |
| 9 | 8.89 | 79 |
| 10 | 9.42 | 79 |

**drought**

| Round | Mean resource_after | n |
|---|---|---|
| 1 | 3.63 | 100 |
| 2 | 4.28 | 100 |
| 3 | 4.63 | 100 |
| 4 | 5.43 | 90 |
| 5 | 6.06 | 87 |
| 6 | 4.98 | 86 |
| 7 | 5.92 | 84 |
| 8 | 6.87 | 82 |
| 9 | 7.63 | 79 |
| 10 | 8.08 | 79 |

**repeated_trust**

| Round | Mean resource_after | n |
|---|---|---|
| 1 | 3.63 | 100 |
| 2 | 4.28 | 100 |
| 3 | 4.63 | 100 |
| 4 | 5.43 | 90 |
| 5 | 6.06 | 87 |
| 6 | 6.58 | 86 |
| 7 | 7.20 | 84 |
| 8 | 8.00 | 82 |
| 9 | 8.89 | 79 |
| 10 | 9.42 | 79 |
| 11 | 10.08 | 78 |
| 12 | 11.20 | 75 |
| 13 | 11.56 | 75 |
| 14 | 11.80 | 75 |
| 15 | 11.07 | 75 |
| 16 | 9.53 | 75 |
| 17 | 8.56 | 75 |
| 18 | 7.53 | 75 |
| 19 | 6.27 | 75 |
| 20 | 4.95 | 75 |
| 21 | 4.00 | 75 |
| 22 | 2.79 | 75 |
| 23 | 1.47 | 75 |
| 24 | 3.97 | 36 |
| 25 | 5.33 | 30 |
| 26 | 4.93 | 30 |
| 27 | 5.12 | 30 |
| 28 | 5.05 | 30 |
| 29 | 4.48 | 30 |
| 30 | 3.95 | 30 |
