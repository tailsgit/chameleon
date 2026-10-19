# Benchmark summary: crello-quick

Engine commit `v3-dirty`, 100 cases (81 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 98/100** (98.0%)
- **Average score: 89.80** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 3 | 2 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | share_drift | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.215 | 0.022 | 0.054 | 0.020 | 0.151 | 0.201 | 0.039 | 0.373 | 0.129 | 0.039 | 0.027 | 0.344 | 0.020 | 0.051 | 0.197 | 0.095 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 6 | 6 | 92.7 |
| Email Header | 600x200 | 6 | 6 | 90.5 |
| Facebook Cover | 820x312 | 12 | 12 | 86.1 |
| Facebook Post | 1200x630 | 5 | 5 | 91.2 |
| Instagram Portrait | 1080x1350 | 3 | 3 | 89.4 |
| Instagram Post | 1080x1080 | 9 | 9 | 87.5 |
| Instagram Story | 1080x1920 | 4 | 4 | 88.2 |
| Leaderboard | 728x90 | 10 | 9 | 87.3 |
| LinkedIn Banner | 1584x396 | 3 | 3 | 91.4 |
| Medium Rectangle | 300x250 | 10 | 10 | 91.9 |
| Pinterest Pin | 1000x1500 | 8 | 8 | 93.8 |
| Presentation 16:9 | 1920x1080 | 6 | 6 | 89.4 |
| Wide Skyscraper | 160x600 | 7 | 6 | 89.3 |
| X Post | 1600x900 | 5 | 5 | 91.5 |
| YouTube Thumbnail | 1280x720 | 6 | 6 | 91.1 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5dc3c996abc8ea6d1cbcc226__leaderboard | 85.2 | hidden_element:svg1 |
| crello_5ac4a8ce4b568b8eece2fd9b__wide_skyscraper | 94.8 | hidden_element:svg3;hidden_element:svg4 |
| crello_5ab9076df07aee69770e9039__leaderboard | 63.0 |  |
| crello_5dadaa37abc8ea6d1cf0a669__facebook_cover | 64.1 |  |
| crello_5c0a9ab5133a785392285eeb__presentation_16_9 | 67.0 |  |
| crello_5f05bdae499b85dcc767e8b7__youtube_thumbnail | 72.4 |  |
| crello_5d691f00abc8ea6d1c396bbf__facebook_cover | 72.5 |  |
| crello_593118b995a7a863ddcdc93c__facebook_cover | 72.6 |  |
| crello_5d691f00abc8ea6d1c396bbf__instagram_story | 73.0 |  |
| crello_5e2aa1c89fea0cc374ba2bff__instagram_portrait | 74.6 |  |
| crello_5d9f1ce1abc8ea6d1c98c087__leaderboard | 75.9 |  |
| crello_5e2aa1c89fea0cc374ba2bff__instagram_post | 76.4 |  |
| crello_5d08ef5d8cba87f943e4586b__wide_skyscraper | 77.1 |  |
| crello_5f608eb1a637ee11e3222235__wide_skyscraper | 78.7 |  |
| crello_5889bcfd95a7a863ddcc3cb9__facebook_cover | 79.0 |  |
| crello_591586e795a7a863ddcd830d__instagram_post | 79.2 |  |
| crello_5f1feb5fa637ee11e36e6b4c__facebook_cover | 79.5 |  |
| crello_58898cb195a7a863ddcc3121__x_post | 81.3 |  |
| crello_5888da2995a7a863ddcc2bc6__email_header | 81.9 |  |
| crello_5f50b378a637ee11e34fa5c6__instagram_post | 82.7 |  |
| crello_5bd1ce9878e1194aa6378870__instagram_post | 82.9 |  |
| crello_5889bcfd95a7a863ddcc3cb9__medium_rectangle | 83.0 |  |
| crello_589d7bb295a7a863ddcc5532__presentation_16_9 | 83.0 |  |
| crello_5f97cda3a637ee11e32492b7__facebook_post | 83.2 |  |
| crello_5eba7bc3499b85dcc7d44cdc__facebook_cover | 83.9 |  |
| crello_5f97cda3a637ee11e32492b7__medium_rectangle | 84.4 |  |
| crello_5dee48ac9fea0cc3743716a5__medium_rectangle | 85.7 |  |
| crello_5ee9d148499b85dcc7b6b727__linkedin_banner | 85.8 |  |
| crello_5f608eb1a637ee11e3222235__a4_poster__150_dpi | 86.4 |  |
| crello_5e7494a24b3890eb07a8b3da__wide_skyscraper | 86.4 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 5667 ms, median 4582 ms, p95 12370 ms, max 14833 ms
- check: mean 4 ms, median 3 ms, p95 8 ms, max 11 ms
- score: mean 5 ms, median 4 ms, p95 12 ms, max 18 ms
- render: n/a
