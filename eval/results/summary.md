# Benchmark summary

Engine commit `f5e9e0c`, 45 cases (3 samples x 15 formats), render=yes, contrast=yes.

- **Cases passing every hard rule: 45/45**
- **Average score: 94.44** / 100

## Violations by rule

| rule | violations | cases |
|---|---|---|
| (none) | 0 | 0 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | small_text | headline | space | balance | floating | alignment | reading_order | contrast |
|---|---|---|---|---|---|---|---|---|
| 0.000 | 0.059 | 0.042 | 0.059 | 0.002 | 0.128 | 0.167 | 0.047 | 0.001 |

## Score by format

| format | size | level1_warmup | level2_core | level3_advanced | passed |
|---|---|---|---|---|---|
| Instagram Post | 1080x1080 | 96.5 | 100.0 | 95.8 | 3/3 |
| Instagram Portrait | 1080x1350 | 96.7 | 99.4 | 100.0 | 3/3 |
| Instagram Story | 1080x1920 | 96.7 | 99.4 | 98.6 | 3/3 |
| Facebook Post | 1200x630 | 93.3 | 96.9 | 94.4 | 3/3 |
| Facebook Cover | 820x312 | 93.2 | 95.4 | 85.2 | 3/3 |
| LinkedIn Banner | 1584x396 | 93.6 | 96.4 | 93.6 | 3/3 |
| YouTube Thumbnail | 1280x720 | 96.1 | 97.0 | 94.5 | 3/3 |
| X Post | 1600x900 | 96.1 | 97.0 | 94.0 | 3/3 |
| Pinterest Pin | 1000x1500 | 96.9 | 99.5 | 97.0 | 3/3 |
| Leaderboard | 728x90 | 87.1 | 86.6 | 83.5 | 3/3 |
| Medium Rectangle | 300x250 | 94.8 | 94.8 | 81.8 | 3/3 |
| Wide Skyscraper | 160x600 | 96.4 | 96.8 | 88.5 | 3/3 |
| A4 Poster (150 dpi) | 1240x1754 | 96.9 | 99.4 | 97.0 | 3/3 |
| Presentation 16:9 | 1920x1080 | 96.1 | 97.0 | 94.0 | 3/3 |
| Email Header | 600x200 | 93.4 | 93.2 | 79.3 | 3/3 |

## Timings (per case, this machine)

- resize: mean 1335.84 ms, median 1340.89 ms, max 2484.83 ms
- check: mean 1.36 ms, median 1.18 ms, max 2.77 ms
- score: mean 97.33 ms, median 102.72 ms, max 193.84 ms (incl. contrast render)
- render: mean 75.52 ms, median 75.04 ms, max 150.29 ms
