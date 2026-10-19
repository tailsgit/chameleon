# Benchmark summary: samples

Engine commit `v2-3-gfd055f9-dirty`, 45 cases (3 designs), render=no, contrast=no, jobs=1.

- **Cases passing every hard rule: 45/45** (100.0%)
- **Average score: 97.21** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| (none) | 0 | 0 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | share_drift | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.000 | 0.000 | 0.063 | 0.025 | 0.011 | 0.000 | 0.000 | 0.107 | 0.014 | 0.071 | 0.003 | 0.146 | 0.004 | 0.033 | 0.099 | 0.048 |

## Score by format

| format | size | level1_warmup | level2_core | level3_advanced | passed |
|---|---|---|---|---|---|
| Instagram Post | 1080x1080 | 97.7 | 100.0 | 96.8 | 3/3 |
| Instagram Portrait | 1080x1350 | 99.1 | 99.6 | 100.0 | 3/3 |
| Instagram Story | 1080x1920 | 97.6 | 99.8 | 98.5 | 3/3 |
| Facebook Post | 1200x630 | 98.2 | 98.4 | 96.2 | 3/3 |
| Facebook Cover | 820x312 | 98.1 | 97.8 | 94.5 | 3/3 |
| LinkedIn Banner | 1584x396 | 98.2 | 97.6 | 96.1 | 3/3 |
| YouTube Thumbnail | 1280x720 | 98.9 | 98.3 | 94.7 | 3/3 |
| X Post | 1600x900 | 98.9 | 98.4 | 95.3 | 3/3 |
| Pinterest Pin | 1000x1500 | 99.1 | 99.8 | 99.6 | 3/3 |
| Leaderboard | 728x90 | 93.4 | 94.2 | 91.3 | 3/3 |
| Medium Rectangle | 300x250 | 98.3 | 97.5 | 88.6 | 3/3 |
| Wide Skyscraper | 160x600 | 98.0 | 97.6 | 89.8 | 3/3 |
| A4 Poster (150 dpi) | 1240x1754 | 99.1 | 99.7 | 99.0 | 3/3 |
| Presentation 16:9 | 1920x1080 | 98.9 | 98.4 | 97.2 | 3/3 |
| Email Header | 600x200 | 98.2 | 97.8 | 89.7 | 3/3 |

## Timings (per case, this machine)

- resize: mean 2955 ms, median 2561 ms, p95 5649 ms, max 7650 ms
- check: mean 1 ms, median 1 ms, p95 2 ms, max 3 ms
- score: mean 2 ms, median 1 ms, p95 4 ms, max 5 ms
- render: n/a
