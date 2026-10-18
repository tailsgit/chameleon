# Benchmark summary

Engine commit `1e836c2`, 45 cases (3 samples x 15 formats), render=yes, contrast=no.

- **Cases passing every hard rule: 45/45**
- **Average score: 95.78** / 100

## Violations by rule

| rule | violations | cases |
|---|---|---|
| (none) | 0 | 0 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | small_text | headline | scale | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.000 | 0.079 | 0.036 | 0.047 | 0.062 | 0.002 | 0.127 | 0.001 | 0.000 | 0.085 | 0.046 |

## Score by format

| format | size | level1_warmup | level2_core | level3_advanced | passed |
|---|---|---|---|---|---|
| Instagram Post | 1080x1080 | 98.1 | 100.0 | 94.0 | 3/3 |
| Instagram Portrait | 1080x1350 | 98.2 | 99.0 | 100.0 | 3/3 |
| Instagram Story | 1080x1920 | 98.2 | 99.5 | 96.4 | 3/3 |
| Facebook Post | 1200x630 | 96.5 | 98.2 | 92.6 | 3/3 |
| Facebook Cover | 820x312 | 96.4 | 97.0 | 92.8 | 3/3 |
| LinkedIn Banner | 1584x396 | 96.6 | 97.3 | 94.6 | 3/3 |
| YouTube Thumbnail | 1280x720 | 97.9 | 98.7 | 92.7 | 3/3 |
| X Post | 1600x900 | 97.9 | 98.8 | 93.2 | 3/3 |
| Pinterest Pin | 1000x1500 | 98.3 | 99.5 | 94.7 | 3/3 |
| Leaderboard | 728x90 | 92.5 | 89.3 | 88.8 | 3/3 |
| Medium Rectangle | 300x250 | 96.5 | 97.7 | 82.8 | 3/3 |
| Wide Skyscraper | 160x600 | 98.1 | 98.0 | 88.7 | 3/3 |
| A4 Poster (150 dpi) | 1240x1754 | 98.3 | 99.3 | 97.4 | 3/3 |
| Presentation 16:9 | 1920x1080 | 97.9 | 98.7 | 95.2 | 3/3 |
| Email Header | 600x200 | 96.5 | 92.6 | 84.5 | 3/3 |

## Timings (per case, this machine)

- resize: mean 1580.18 ms, median 1659.06 ms, max 3549.37 ms
- check: mean 1.36 ms, median 1.16 ms, max 2.79 ms
- score: mean 1.72 ms, median 1.33 ms, max 3.69 ms
- render: mean 75.45 ms, median 75.56 ms, max 153.15 ms
