# Benchmark summary: samples

Engine commit `v5-2-g5f57327-dirty`, 45 cases (3 designs), render=no, contrast=no, jobs=4.

- **Cases passing every hard rule: 45/45** (100.0%)
- **Average score: 98.22** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| (none) | 0 | 0 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | groups | related_order | fill | share_drift | space | balance | floating | emphasis | siblings | alignment | reading_order | legibility | coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.000 | 0.000 | 0.062 | 0.033 | 0.015 | 0.000 | 0.000 | 0.078 | 0.000 | 0.000 | 0.000 | 0.020 | 0.068 | 0.003 | 0.142 | 0.003 | 0.050 | 0.102 | 0.043 | 0.000 | 0.000 |

## Score by format

| format | size | level1_warmup | level2_core | level3_advanced | passed |
|---|---|---|---|---|---|
| Instagram Post | 1080x1080 | 98.5 | 100.0 | 97.8 | 3/3 |
| Instagram Portrait | 1080x1350 | 99.4 | 99.7 | 100.0 | 3/3 |
| Instagram Story | 1080x1920 | 98.5 | 99.9 | 98.7 | 3/3 |
| Facebook Post | 1200x630 | 99.2 | 99.0 | 97.5 | 3/3 |
| Facebook Cover | 820x312 | 99.2 | 98.6 | 95.3 | 3/3 |
| LinkedIn Banner | 1584x396 | 98.9 | 98.5 | 97.4 | 3/3 |
| YouTube Thumbnail | 1280x720 | 99.3 | 99.0 | 96.8 | 3/3 |
| X Post | 1600x900 | 99.3 | 99.0 | 97.9 | 3/3 |
| Pinterest Pin | 1000x1500 | 99.5 | 99.9 | 99.7 | 3/3 |
| Leaderboard | 728x90 | 96.1 | 96.3 | 93.3 | 3/3 |
| Medium Rectangle | 300x250 | 98.9 | 98.4 | 92.0 | 3/3 |
| Wide Skyscraper | 160x600 | 98.7 | 98.5 | 94.9 | 3/3 |
| A4 Poster (150 dpi) | 1240x1754 | 99.5 | 99.8 | 99.4 | 3/3 |
| Presentation 16:9 | 1920x1080 | 99.3 | 99.0 | 98.1 | 3/3 |
| Email Header | 600x200 | 98.8 | 98.6 | 93.7 | 3/3 |

## Timings (per case, this machine, 4 worker processes in parallel)

- resize: mean 5072 ms, median 4435 ms, p95 10100 ms, max 11415 ms
- check: mean 2 ms, median 2 ms, p95 3 ms, max 5 ms
- score: mean 3 ms, median 3 ms, p95 6 ms, max 8 ms
- render: n/a
