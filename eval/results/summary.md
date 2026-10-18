# Benchmark summary: samples

Engine commit `v1-submittable-1-gf0338a2-dirty`, 45 cases (3 designs), render=no, contrast=no, jobs=1.

- **Cases passing every hard rule: 45/45** (100.0%)
- **Average score: 96.83** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| (none) | 0 | 0 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.000 | 0.000 | 0.065 | 0.019 | 0.009 | 0.000 | 0.051 | 0.000 | 0.151 | 0.004 | 0.039 | 0.122 | 0.041 |

## Score by format

| format | size | level1_warmup | level2_core | level3_advanced | passed |
|---|---|---|---|---|---|
| Instagram Post | 1080x1080 | 96.8 | 100.0 | 96.7 | 3/3 |
| Instagram Portrait | 1080x1350 | 98.7 | 99.2 | 100.0 | 3/3 |
| Instagram Story | 1080x1920 | 98.7 | 99.8 | 98.3 | 3/3 |
| Facebook Post | 1200x630 | 97.4 | 98.8 | 94.8 | 3/3 |
| Facebook Cover | 820x312 | 98.0 | 98.3 | 93.4 | 3/3 |
| LinkedIn Banner | 1584x396 | 97.5 | 98.0 | 95.7 | 3/3 |
| YouTube Thumbnail | 1280x720 | 98.5 | 99.4 | 93.9 | 3/3 |
| X Post | 1600x900 | 98.5 | 99.4 | 94.5 | 3/3 |
| Pinterest Pin | 1000x1500 | 98.8 | 99.8 | 97.5 | 3/3 |
| Leaderboard | 728x90 | 96.0 | 94.2 | 89.0 | 3/3 |
| Medium Rectangle | 300x250 | 97.7 | 97.7 | 85.6 | 3/3 |
| Wide Skyscraper | 160x600 | 98.6 | 98.2 | 86.8 | 3/3 |
| A4 Poster (150 dpi) | 1240x1754 | 98.8 | 99.7 | 97.5 | 3/3 |
| Presentation 16:9 | 1920x1080 | 98.5 | 99.4 | 96.3 | 3/3 |
| Email Header | 600x200 | 98.0 | 98.1 | 86.7 | 3/3 |

## Timings (per case, this machine)

- resize: mean 2645 ms, median 2329 ms, p95 4943 ms, max 7168 ms
- check: mean 1 ms, median 1 ms, p95 3 ms, max 3 ms
- score: mean 2 ms, median 1 ms, p95 4 ms, max 4 ms
- render: n/a
