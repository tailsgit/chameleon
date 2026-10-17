# Benchmark summary

Engine commit `614423c`, 45 cases (3 samples x 15 formats), render=yes, contrast=yes.

- **Cases passing every hard rule: 45/45**
- **Average score: 96.05** / 100

## Violations by rule

| rule | violations | cases |
|---|---|---|
| (none) | 0 | 0 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | small_text | headline | space | alignment | reading_order | contrast |
|---|---|---|---|---|---|---|
| 0.000 | 0.039 | 0.000 | 0.094 | 0.030 | 0.081 | 0.072 |

## Score by format

| format | size | level1_warmup | level2_core | level3_advanced | passed |
|---|---|---|---|---|---|
| Instagram Post | 1080x1080 | 99.9 | 99.8 | 97.8 | 3/3 |
| Instagram Portrait | 1080x1350 | 99.9 | 99.8 | 97.2 | 3/3 |
| Instagram Story | 1080x1920 | 99.8 | 99.9 | 97.2 | 3/3 |
| Facebook Post | 1200x630 | 97.1 | 93.4 | 93.0 | 3/3 |
| Facebook Cover | 820x312 | 99.1 | 92.8 | 94.6 | 3/3 |
| LinkedIn Banner | 1584x396 | 99.7 | 95.5 | 92.0 | 3/3 |
| YouTube Thumbnail | 1280x720 | 98.1 | 97.1 | 93.1 | 3/3 |
| X Post | 1600x900 | 98.1 | 98.6 | 93.2 | 3/3 |
| Pinterest Pin | 1000x1500 | 99.9 | 99.8 | 97.3 | 3/3 |
| Leaderboard | 728x90 | 97.1 | 92.2 | 82.3 | 3/3 |
| Medium Rectangle | 300x250 | 99.6 | 95.3 | 83.2 | 3/3 |
| Wide Skyscraper | 160x600 | 99.5 | 93.9 | 87.6 | 3/3 |
| A4 Poster (150 dpi) | 1240x1754 | 100.0 | 100.0 | 96.3 | 3/3 |
| Presentation 16:9 | 1920x1080 | 98.1 | 98.5 | 95.3 | 3/3 |
| Email Header | 600x200 | 98.5 | 93.8 | 87.2 | 3/3 |

## Timings (per case, this machine)

- resize: mean 1320.10 ms, median 1341.77 ms, max 2495.85 ms
- check: mean 1.37 ms, median 1.17 ms, max 2.81 ms
- score: mean 97.53 ms, median 102.50 ms, max 197.26 ms (incl. contrast render)
- render: mean 76.29 ms, median 73.81 ms, max 151.72 ms
