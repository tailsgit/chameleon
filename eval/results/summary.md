# Benchmark summary

Engine commit `fddbb80-dirty`, 45 cases (3 samples x 15 formats), render=yes, contrast=yes.

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

- resize: mean 1344.21 ms, median 1342.61 ms, max 2528.84 ms
- check: mean 1.41 ms, median 1.17 ms, max 4.33 ms
- score: mean 98.27 ms, median 102.68 ms, max 201.71 ms (incl. contrast render)
- render: mean 76.63 ms, median 74.36 ms, max 154.44 ms
