# Benchmark summary: samples

Engine commit `v1-submittable-3-g71b0674-dirty`, 45 cases (3 designs), render=no, contrast=no, jobs=1.

- **Cases passing every hard rule: 45/45** (100.0%)
- **Average score: 97.36** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| (none) | 0 | 0 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.000 | 0.000 | 0.062 | 0.047 | 0.012 | 0.000 | 0.000 | 0.067 | 0.000 | 0.160 | 0.000 | 0.039 | 0.082 | 0.049 |

## Score by format

| format | size | level1_warmup | level2_core | level3_advanced | passed |
|---|---|---|---|---|---|
| Instagram Post | 1080x1080 | 97.5 | 100.0 | 97.4 | 3/3 |
| Instagram Portrait | 1080x1350 | 99.0 | 99.4 | 100.0 | 3/3 |
| Instagram Story | 1080x1920 | 99.0 | 99.8 | 98.7 | 3/3 |
| Facebook Post | 1200x630 | 98.0 | 99.1 | 95.9 | 3/3 |
| Facebook Cover | 820x312 | 97.9 | 98.7 | 94.8 | 3/3 |
| LinkedIn Banner | 1584x396 | 98.0 | 98.5 | 96.6 | 3/3 |
| YouTube Thumbnail | 1280x720 | 98.8 | 99.5 | 95.2 | 3/3 |
| X Post | 1600x900 | 98.8 | 99.5 | 95.7 | 3/3 |
| Pinterest Pin | 1000x1500 | 99.0 | 99.8 | 98.0 | 3/3 |
| Leaderboard | 728x90 | 96.0 | 92.0 | 91.3 | 3/3 |
| Medium Rectangle | 300x250 | 98.1 | 98.2 | 88.6 | 3/3 |
| Wide Skyscraper | 160x600 | 98.9 | 98.6 | 89.0 | 3/3 |
| A4 Poster (150 dpi) | 1240x1754 | 99.0 | 99.8 | 98.1 | 3/3 |
| Presentation 16:9 | 1920x1080 | 98.8 | 99.5 | 97.1 | 3/3 |
| Email Header | 600x200 | 98.0 | 98.5 | 89.4 | 3/3 |

## Timings (per case, this machine)

- resize: mean 1769 ms, median 1735 ms, p95 2882 ms, max 4799 ms
- check: mean 1 ms, median 1 ms, p95 3 ms, max 3 ms
- score: mean 2 ms, median 1 ms, p95 4 ms, max 4 ms
- render: n/a
