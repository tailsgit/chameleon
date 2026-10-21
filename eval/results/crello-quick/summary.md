# Benchmark summary: crello-quick

Engine commit `v5-2-g5f57327-dirty`, 100 cases (81 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 100/100** (100.0%)
- **Average score: 90.18** / 100
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
| 0.210 | 0.011 | 0.061 | 0.050 | 0.148 | 0.210 | 0.031 | 0.268 | 0.223 | 0.025 | 0.016 | 0.134 | 0.035 | 0.028 | 0.344 | 0.034 | 0.046 | 0.194 | 0.115 | 0.009 | 0.115 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 6 | 6 | 93.4 |
| Email Header | 600x200 | 6 | 6 | 90.0 |
| Facebook Cover | 820x312 | 12 | 12 | 87.8 |
| Facebook Post | 1200x630 | 5 | 5 | 92.3 |
| Instagram Portrait | 1080x1350 | 3 | 3 | 89.6 |
| Instagram Post | 1080x1080 | 9 | 9 | 87.0 |
| Instagram Story | 1080x1920 | 4 | 4 | 91.2 |
| Leaderboard | 728x90 | 10 | 10 | 87.9 |
| LinkedIn Banner | 1584x396 | 3 | 3 | 92.2 |
| Medium Rectangle | 300x250 | 10 | 10 | 90.4 |
| Pinterest Pin | 1000x1500 | 8 | 8 | 93.2 |
| Presentation 16:9 | 1920x1080 | 6 | 6 | 92.8 |
| Wide Skyscraper | 160x600 | 7 | 7 | 86.6 |
| X Post | 1600x900 | 5 | 5 | 91.8 |
| YouTube Thumbnail | 1280x720 | 6 | 6 | 93.1 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5ab9076df07aee69770e9039__leaderboard | 71.4 |  |
| crello_5eba7bc3499b85dcc7d44cdc__facebook_cover | 73.0 |  |
| crello_5f608eb1a637ee11e3222235__wide_skyscraper | 74.5 |  |
| crello_5888da2995a7a863ddcc2bc6__email_header | 75.1 |  |
| crello_5e2aa1c89fea0cc374ba2bff__instagram_post | 75.3 |  |
| crello_5e2aa1c89fea0cc374ba2bff__instagram_portrait | 75.5 |  |
| crello_5e7494a24b3890eb07a8b3da__wide_skyscraper | 76.1 |  |
| crello_5d08ef5d8cba87f943e4586b__wide_skyscraper | 76.1 |  |
| crello_58898cb195a7a863ddcc3121__x_post | 76.2 |  |
| crello_5f1feb5fa637ee11e36e6b4c__facebook_cover | 77.4 |  |
| crello_5f05bdae499b85dcc767e8b7__youtube_thumbnail | 77.6 |  |
| crello_5d691f00abc8ea6d1c396bbf__facebook_cover | 78.3 |  |
| crello_5d691f00abc8ea6d1c396bbf__instagram_story | 78.9 |  |
| crello_5c0a9ab5133a785392285eeb__presentation_16_9 | 79.0 |  |
| crello_5f50b378a637ee11e34fa5c6__instagram_post | 79.2 |  |
| crello_5f608eb1a637ee11e3222235__a4_poster__150_dpi | 79.3 |  |
| crello_5889bcfd95a7a863ddcc3cb9__facebook_cover | 79.6 |  |
| crello_589df8d495a7a863ddcc5e39__medium_rectangle | 79.9 |  |
| crello_5d9f1ce1abc8ea6d1c98c087__leaderboard | 80.3 |  |
| crello_5bd1ce9878e1194aa6378870__instagram_post | 81.0 |  |
| crello_5e4120f69fea0cc3748a41f2__leaderboard | 81.2 |  |
| crello_591586e795a7a863ddcd830d__instagram_post | 81.5 |  |
| crello_593118b995a7a863ddcdc93c__facebook_cover | 81.7 |  |
| crello_5889bcfd95a7a863ddcc3cb9__medium_rectangle | 82.0 |  |
| crello_5dc3c996abc8ea6d1cbcc226__leaderboard | 82.9 |  |
| crello_5dee48ac9fea0cc3743716a5__medium_rectangle | 84.4 |  |
| crello_5b9bd56b18654940f7a74143__medium_rectangle | 84.6 |  |
| crello_5f4cf4e7a637ee11e32d0dbb__facebook_cover | 85.5 |  |
| crello_58a4155595a7a863ddcc6dd1__instagram_post | 85.5 |  |
| crello_5f97cda3a637ee11e32492b7__medium_rectangle | 86.2 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 6744 ms, median 6779 ms, p95 12659 ms, max 16489 ms
- check: mean 4 ms, median 3 ms, p95 7 ms, max 21 ms
- score: mean 7 ms, median 5 ms, p95 16 ms, max 35 ms
- render: n/a
