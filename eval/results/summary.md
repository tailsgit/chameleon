# Benchmark summary: samples

Engine commit `v2-2-g2e4c9a5-dirty`, 45 cases (3 designs), render=no, contrast=no, jobs=1.

- **Cases passing every hard rule: 45/45** (100.0%)
- **Average score: 96.41** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| (none) | 0 | 0 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.000 | 0.000 | 0.076 | 0.051 | 0.043 | 0.019 | 0.000 | 0.044 | 0.075 | 0.004 | 0.152 | 0.000 | 0.039 | 0.148 | 0.045 |

## Score by format

| format | size | level1_warmup | level2_core | level3_advanced | passed |
|---|---|---|---|---|---|
| Instagram Post | 1080x1080 | 97.5 | 100.0 | 96.9 | 3/3 |
| Instagram Portrait | 1080x1350 | 98.4 | 99.4 | 100.0 | 3/3 |
| Instagram Story | 1080x1920 | 97.6 | 97.9 | 98.7 | 3/3 |
| Facebook Post | 1200x630 | 97.7 | 97.1 | 96.0 | 3/3 |
| Facebook Cover | 820x312 | 99.1 | 96.8 | 94.4 | 3/3 |
| LinkedIn Banner | 1584x396 | 98.3 | 92.2 | 96.2 | 3/3 |
| YouTube Thumbnail | 1280x720 | 98.5 | 97.0 | 94.8 | 3/3 |
| X Post | 1600x900 | 98.5 | 96.6 | 95.3 | 3/3 |
| Pinterest Pin | 1000x1500 | 98.0 | 99.0 | 98.1 | 3/3 |
| Leaderboard | 728x90 | 98.5 | 81.6 | 91.1 | 3/3 |
| Medium Rectangle | 300x250 | 98.2 | 95.5 | 88.4 | 3/3 |
| Wide Skyscraper | 160x600 | 97.9 | 97.4 | 90.3 | 3/3 |
| A4 Poster (150 dpi) | 1240x1754 | 98.2 | 99.1 | 98.1 | 3/3 |
| Presentation 16:9 | 1920x1080 | 98.5 | 96.7 | 97.2 | 3/3 |
| Email Header | 600x200 | 99.2 | 93.2 | 89.2 | 3/3 |

## Timings (per case, this machine)

- resize: mean 2575 ms, median 1955 ms, p95 5391 ms, max 7247 ms
- check: mean 1 ms, median 1 ms, p95 3 ms, max 3 ms
- score: mean 2 ms, median 2 ms, p95 4 ms, max 4 ms
- render: n/a
