# Benchmark summary: crello-quick

Engine commit `v4-4-g8704cd6-dirty`, 100 cases (81 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 100/100** (100.0%)
- **Average score: 92.07** / 100
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
| 0.193 | 0.021 | 0.051 | 0.010 | 0.142 | 0.184 | 0.024 | 0.410 | 0.138 | 0.039 | 0.022 | 0.329 | 0.032 | 0.046 | 0.203 | 0.097 | 0.013 | 0.030 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 6 | 6 | 93.3 |
| Email Header | 600x200 | 6 | 6 | 91.7 |
| Facebook Cover | 820x312 | 12 | 12 | 91.0 |
| Facebook Post | 1200x630 | 5 | 5 | 93.7 |
| Instagram Portrait | 1080x1350 | 3 | 3 | 93.3 |
| Instagram Post | 1080x1080 | 9 | 9 | 91.5 |
| Instagram Story | 1080x1920 | 4 | 4 | 91.2 |
| Leaderboard | 728x90 | 10 | 10 | 90.1 |
| LinkedIn Banner | 1584x396 | 3 | 3 | 93.6 |
| Medium Rectangle | 300x250 | 10 | 10 | 93.4 |
| Pinterest Pin | 1000x1500 | 8 | 8 | 95.2 |
| Presentation 16:9 | 1920x1080 | 6 | 6 | 91.6 |
| Wide Skyscraper | 160x600 | 7 | 7 | 89.5 |
| X Post | 1600x900 | 5 | 5 | 90.6 |
| YouTube Thumbnail | 1280x720 | 6 | 6 | 93.3 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5f608eb1a637ee11e3222235__wide_skyscraper | 69.4 |  |
| crello_58898cb195a7a863ddcc3121__x_post | 71.5 |  |
| crello_5c0a9ab5133a785392285eeb__presentation_16_9 | 74.8 |  |
| crello_5f608eb1a637ee11e3222235__a4_poster__150_dpi | 75.2 |  |
| crello_5ab9076df07aee69770e9039__leaderboard | 76.2 |  |
| crello_5f05bdae499b85dcc767e8b7__youtube_thumbnail | 78.1 |  |
| crello_5d691f00abc8ea6d1c396bbf__facebook_cover | 78.9 |  |
| crello_5d691f00abc8ea6d1c396bbf__instagram_story | 79.5 |  |
| crello_5d9f1ce1abc8ea6d1c98c087__leaderboard | 79.7 |  |
| crello_593118b995a7a863ddcdc93c__facebook_cover | 79.7 |  |
| crello_5d08ef5d8cba87f943e4586b__wide_skyscraper | 81.7 |  |
| crello_5f1feb5fa637ee11e36e6b4c__facebook_cover | 83.3 |  |
| crello_5dadaa37abc8ea6d1cf0a669__facebook_cover | 83.5 |  |
| crello_5888da2995a7a863ddcc2bc6__email_header | 84.1 |  |
| crello_5e2aa1c89fea0cc374ba2bff__instagram_portrait | 84.8 |  |
| crello_5e2aa1c89fea0cc374ba2bff__instagram_post | 85.2 |  |
| crello_589df8d495a7a863ddcc5e39__medium_rectangle | 85.5 |  |
| crello_591586e795a7a863ddcd830d__instagram_post | 85.7 |  |
| crello_5889bcfd95a7a863ddcc3cb9__facebook_cover | 86.0 |  |
| crello_5e4120f69fea0cc3748a41f2__leaderboard | 86.6 |  |
| crello_5f50b378a637ee11e34fa5c6__instagram_post | 87.0 |  |
| crello_589d7bb295a7a863ddcc5532__presentation_16_9 | 87.5 |  |
| crello_5dee48ac9fea0cc3743716a5__medium_rectangle | 87.7 |  |
| crello_5f97cda3a637ee11e32492b7__medium_rectangle | 88.3 |  |
| crello_5f97cda3a637ee11e32492b7__facebook_post | 88.6 |  |
| crello_5ee9d148499b85dcc7b6b727__linkedin_banner | 89.2 |  |
| crello_5e7494a24b3890eb07a8b3da__wide_skyscraper | 89.6 |  |
| crello_58891e4795a7a863ddcc2f33__email_header | 89.7 |  |
| crello_58a4155595a7a863ddcc6dd1__instagram_post | 89.7 |  |
| crello_5ce2b06f7d4459dfe15ccc86__x_post | 90.0 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 5853 ms, median 5217 ms, p95 10705 ms, max 15606 ms
- check: mean 3 ms, median 3 ms, p95 8 ms, max 11 ms
- score: mean 6 ms, median 5 ms, p95 14 ms, max 26 ms
- render: n/a
