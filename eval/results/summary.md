# Benchmark summary

Engine commit `74a8df1`, 45 cases (3 samples x 15 formats), render=yes, contrast=yes.

- **Cases passing every hard rule: 1/45**
- **Average score: 87.06** / 100

## Violations by rule

| rule | violations | cases |
|---|---|---|
| image_aspect | 84 | 42 |
| off_canvas_rotated | 20 | 11 |
| off_canvas | 15 | 15 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | small_text | headline | space | alignment | reading_order | contrast |
|---|---|---|---|---|---|---|
| 0.004 | 0.238 | 0.000 | 0.464 | 0.041 | 0.001 | 0.109 |

## Score by format

| format | size | level1_warmup | level2_core | level3_advanced | passed |
|---|---|---|---|---|---|
| Instagram Post | 1080x1080 | 100.0 | 98.6 | 92.4 | 1/3 |
| Instagram Portrait | 1080x1350 | 99.3 | 97.6 | 98.6 | 0/3 |
| Instagram Story | 1080x1920 | 93.6 | 94.2 | 97.2 | 0/3 |
| Facebook Post | 1200x630 | 91.7 | 84.5 | 85.9 | 0/3 |
| Facebook Cover | 820x312 | 86.2 | 77.2 | 78.1 | 0/3 |
| LinkedIn Banner | 1584x396 | 88.0 | 78.3 | 80.0 | 0/3 |
| YouTube Thumbnail | 1280x720 | 93.3 | 86.7 | 88.1 | 0/3 |
| X Post | 1600x900 | 93.0 | 84.7 | 90.0 | 0/3 |
| Pinterest Pin | 1000x1500 | 96.2 | 93.7 | 95.7 | 0/3 |
| Leaderboard | 728x90 | 72.4 | 64.3 | 68.4 | 0/3 |
| Medium Rectangle | 300x250 | 88.0 | 84.5 | 77.9 | 0/3 |
| Wide Skyscraper | 160x600 | 78.2 | 75.0 | 73.8 | 0/3 |
| A4 Poster (150 dpi) | 1240x1754 | 96.7 | 96.7 | 98.1 | 0/3 |
| Presentation 16:9 | 1920x1080 | 93.0 | 87.5 | 90.8 | 0/3 |
| Email Header | 600x200 | 82.1 | 72.9 | 74.3 | 0/3 |

## Timings (per case, this machine)

- resize: mean 0.05 ms, median 0.04 ms, max 0.09 ms
- check: mean 1.27 ms, median 1.14 ms, max 2.26 ms
- score: mean 106.48 ms, median 105.41 ms, max 211.42 ms (incl. contrast render)
- render: mean 72.13 ms, median 69.55 ms, max 143.58 ms
