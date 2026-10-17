# Benchmark summary

Engine commit `3af967a`, 45 cases (3 samples x 15 formats), render=yes, contrast=yes.

- **Cases passing every hard rule: 45/45**
- **Average score: 94.88** / 100

## Violations by rule

| rule | violations | cases |
|---|---|---|
| (none) | 0 | 0 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | small_text | headline | space | balance | floating | emphasis | alignment | reading_order | contrast |
|---|---|---|---|---|---|---|---|---|---|
| 0.000 | 0.061 | 0.046 | 0.050 | 0.002 | 0.134 | 0.009 | 0.177 | 0.051 | 0.001 |

## Score by format

| format | size | level1_warmup | level2_core | level3_advanced | passed |
|---|---|---|---|---|---|
| Instagram Post | 1080x1080 | 96.8 | 100.0 | 96.2 | 3/3 |
| Instagram Portrait | 1080x1350 | 97.0 | 99.4 | 100.0 | 3/3 |
| Instagram Story | 1080x1920 | 97.0 | 99.5 | 98.7 | 3/3 |
| Facebook Post | 1200x630 | 94.4 | 97.2 | 94.9 | 3/3 |
| Facebook Cover | 820x312 | 93.9 | 95.8 | 85.8 | 3/3 |
| LinkedIn Banner | 1584x396 | 94.2 | 96.8 | 94.2 | 3/3 |
| YouTube Thumbnail | 1280x720 | 96.5 | 97.2 | 95.0 | 3/3 |
| X Post | 1600x900 | 96.5 | 97.2 | 94.5 | 3/3 |
| Pinterest Pin | 1000x1500 | 97.2 | 99.5 | 97.3 | 3/3 |
| Leaderboard | 728x90 | 93.1 | 87.8 | 82.3 | 3/3 |
| Medium Rectangle | 300x250 | 95.3 | 95.3 | 79.7 | 3/3 |
| Wide Skyscraper | 160x600 | 96.7 | 97.1 | 89.5 | 3/3 |
| A4 Poster (150 dpi) | 1240x1754 | 97.2 | 99.5 | 97.2 | 3/3 |
| Presentation 16:9 | 1920x1080 | 96.5 | 97.2 | 94.5 | 3/3 |
| Email Header | 600x200 | 94.0 | 93.8 | 80.4 | 3/3 |

## Timings (per case, this machine)

- resize: mean 1511.86 ms, median 1592.90 ms, max 3635.30 ms
- check: mean 1.43 ms, median 1.22 ms, max 3.60 ms
- score: mean 98.07 ms, median 104.00 ms, max 195.40 ms (incl. contrast render)
- render: mean 76.06 ms, median 75.30 ms, max 150.26 ms
