# Benchmark summary: samples

Engine commit `0436a50-dirty`, 45 cases (3 designs), render=no, contrast=no, jobs=1.

- **Cases passing every hard rule: 45/45** (100.0%)
- **Average score: 96.26** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| (none) | 0 | 0 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.000 | 0.000 | 0.061 | 0.036 | 0.037 | 0.061 | 0.000 | 0.123 | 0.000 | 0.039 | 0.083 | 0.040 |

## Score by format

| format | size | level1_warmup | level2_core | level3_advanced | passed |
|---|---|---|---|---|---|
| Instagram Post | 1080x1080 | 98.3 | 100.0 | 95.4 | 3/3 |
| Instagram Portrait | 1080x1350 | 98.4 | 99.1 | 100.0 | 3/3 |
| Instagram Story | 1080x1920 | 98.4 | 99.5 | 97.5 | 3/3 |
| Facebook Post | 1200x630 | 96.8 | 98.4 | 93.4 | 3/3 |
| Facebook Cover | 820x312 | 96.7 | 98.0 | 93.7 | 3/3 |
| LinkedIn Banner | 1584x396 | 96.9 | 97.6 | 93.5 | 3/3 |
| YouTube Thumbnail | 1280x720 | 98.1 | 98.8 | 93.0 | 3/3 |
| X Post | 1600x900 | 98.1 | 98.9 | 93.8 | 3/3 |
| Pinterest Pin | 1000x1500 | 98.5 | 99.5 | 96.0 | 3/3 |
| Leaderboard | 728x90 | 93.1 | 90.2 | 90.1 | 3/3 |
| Medium Rectangle | 300x250 | 96.8 | 97.9 | 84.3 | 3/3 |
| Wide Skyscraper | 160x600 | 98.2 | 98.2 | 88.3 | 3/3 |
| A4 Poster (150 dpi) | 1240x1754 | 98.5 | 99.4 | 97.6 | 3/3 |
| Presentation 16:9 | 1920x1080 | 98.1 | 98.8 | 95.6 | 3/3 |
| Email Header | 600x200 | 96.8 | 98.0 | 85.9 | 3/3 |

## Timings (per case, this machine)

- resize: mean 1714 ms, median 1716 ms, p95 2854 ms, max 4647 ms
- check: mean 1 ms, median 1 ms, p95 3 ms, max 3 ms
- score: mean 2 ms, median 1 ms, p95 4 ms, max 4 ms
- render: n/a
