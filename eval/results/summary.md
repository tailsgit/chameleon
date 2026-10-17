# Benchmark summary

Engine commit `1a2d7be`, 45 cases (3 samples x 15 formats), render=yes, contrast=yes.

- **Cases passing every hard rule: 45/45**
- **Average score: 95.82** / 100

## Violations by rule

| rule | violations | cases |
|---|---|---|
| (none) | 0 | 0 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | small_text | headline | space | alignment | reading_order | contrast |
|---|---|---|---|---|---|---|
| 0.000 | 0.042 | 0.000 | 0.103 | 0.042 | 0.080 | 0.070 |

## Score by format

| format | size | level1_warmup | level2_core | level3_advanced | passed |
|---|---|---|---|---|---|
| Instagram Post | 1080x1080 | 98.1 | 99.8 | 98.0 | 3/3 |
| Instagram Portrait | 1080x1350 | 99.9 | 99.8 | 96.4 | 3/3 |
| Instagram Story | 1080x1920 | 100.0 | 99.8 | 96.9 | 3/3 |
| Facebook Post | 1200x630 | 98.0 | 93.4 | 92.8 | 3/3 |
| Facebook Cover | 820x312 | 98.9 | 91.8 | 94.6 | 3/3 |
| LinkedIn Banner | 1584x396 | 99.4 | 94.0 | 94.1 | 3/3 |
| YouTube Thumbnail | 1280x720 | 98.1 | 97.1 | 93.0 | 3/3 |
| X Post | 1600x900 | 98.1 | 98.6 | 92.8 | 3/3 |
| Pinterest Pin | 1000x1500 | 99.9 | 99.8 | 96.8 | 3/3 |
| Leaderboard | 728x90 | 97.0 | 92.2 | 82.8 | 3/3 |
| Medium Rectangle | 300x250 | 99.7 | 92.9 | 80.2 | 3/3 |
| Wide Skyscraper | 160x600 | 99.8 | 94.0 | 87.3 | 3/3 |
| A4 Poster (150 dpi) | 1240x1754 | 99.9 | 100.0 | 96.5 | 3/3 |
| Presentation 16:9 | 1920x1080 | 99.7 | 98.5 | 94.2 | 3/3 |
| Email Header | 600x200 | 98.1 | 93.8 | 85.3 | 3/3 |

## Timings (per case, this machine)

- resize: mean 1326.97 ms, median 1337.57 ms, max 2493.11 ms
- check: mean 1.34 ms, median 1.16 ms, max 2.74 ms
- score: mean 97.43 ms, median 102.91 ms, max 199.39 ms (incl. contrast render)
- render: mean 75.80 ms, median 73.50 ms, max 152.39 ms
