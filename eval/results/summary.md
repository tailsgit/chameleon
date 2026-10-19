# Benchmark summary: samples

Engine commit `v4-5-g6a0f590-dirty`, 45 cases (3 designs), render=no, contrast=no, jobs=4.

- **Cases passing every hard rule: 45/45** (100.0%)
- **Average score: 97.94** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| (none) | 0 | 0 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | share_drift | space | balance | floating | emphasis | siblings | alignment | reading_order | legibility | coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.000 | 0.000 | 0.064 | 0.020 | 0.012 | 0.000 | 0.000 | 0.107 | 0.019 | 0.068 | 0.003 | 0.136 | 0.000 | 0.033 | 0.085 | 0.057 | 0.000 | 0.000 |

## Score by format

| format | size | level1_warmup | level2_core | level3_advanced | passed |
|---|---|---|---|---|---|
| Instagram Post | 1080x1080 | 98.2 | 100.0 | 99.1 | 3/3 |
| Instagram Portrait | 1080x1350 | 99.3 | 99.7 | 100.0 | 3/3 |
| Instagram Story | 1080x1920 | 98.2 | 99.9 | 98.9 | 3/3 |
| Facebook Post | 1200x630 | 99.1 | 98.8 | 97.1 | 3/3 |
| Facebook Cover | 820x312 | 99.1 | 98.4 | 95.8 | 3/3 |
| LinkedIn Banner | 1584x396 | 98.6 | 98.2 | 97.0 | 3/3 |
| YouTube Thumbnail | 1280x720 | 99.2 | 98.7 | 96.0 | 3/3 |
| X Post | 1600x900 | 99.2 | 98.8 | 96.4 | 3/3 |
| Pinterest Pin | 1000x1500 | 99.3 | 99.9 | 99.7 | 3/3 |
| Leaderboard | 728x90 | 95.3 | 95.6 | 93.4 | 3/3 |
| Medium Rectangle | 300x250 | 98.7 | 98.1 | 91.3 | 3/3 |
| Wide Skyscraper | 160x600 | 98.4 | 98.2 | 92.4 | 3/3 |
| A4 Poster (150 dpi) | 1240x1754 | 99.3 | 99.8 | 99.3 | 3/3 |
| Presentation 16:9 | 1920x1080 | 99.2 | 98.8 | 97.9 | 3/3 |
| Email Header | 600x200 | 98.6 | 98.4 | 92.1 | 3/3 |

## Timings (per case, this machine, 4 worker processes in parallel)

- resize: mean 5123 ms, median 5029 ms, p95 9586 ms, max 10076 ms
- check: mean 2 ms, median 2 ms, p95 4 ms, max 5 ms
- score: mean 3 ms, median 3 ms, p95 7 ms, max 8 ms
- render: n/a
