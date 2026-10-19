# Benchmark summary: crello-quick

Engine commit `v3-11-g4ac5443-dirty`, 100 cases (81 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 98/100** (98.0%)
- **Average score: 91.63** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 3 | 2 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | share_drift | space | balance | floating | emphasis | siblings | alignment | reading_order | legibility | coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.184 | 0.022 | 0.054 | 0.020 | 0.158 | 0.207 | 0.028 | 0.335 | 0.136 | 0.038 | 0.026 | 0.348 | 0.020 | 0.051 | 0.207 | 0.116 | 0.015 | 0.040 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 6 | 6 | 92.1 |
| Email Header | 600x200 | 6 | 6 | 90.0 |
| Facebook Cover | 820x312 | 12 | 12 | 90.7 |
| Facebook Post | 1200x630 | 5 | 5 | 93.1 |
| Instagram Portrait | 1080x1350 | 3 | 3 | 91.9 |
| Instagram Post | 1080x1080 | 9 | 9 | 90.8 |
| Instagram Story | 1080x1920 | 4 | 4 | 91.0 |
| Leaderboard | 728x90 | 10 | 9 | 89.5 |
| LinkedIn Banner | 1584x396 | 3 | 3 | 93.5 |
| Medium Rectangle | 300x250 | 10 | 10 | 93.2 |
| Pinterest Pin | 1000x1500 | 8 | 8 | 95.0 |
| Presentation 16:9 | 1920x1080 | 6 | 6 | 92.0 |
| Wide Skyscraper | 160x600 | 7 | 6 | 89.6 |
| X Post | 1600x900 | 5 | 5 | 90.7 |
| YouTube Thumbnail | 1280x720 | 6 | 6 | 93.2 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5dc3c996abc8ea6d1cbcc226__leaderboard | 88.7 | hidden_element:svg1 |
| crello_5ac4a8ce4b568b8eece2fd9b__wide_skyscraper | 94.7 | hidden_element:svg3;hidden_element:svg4 |
| crello_5f608eb1a637ee11e3222235__wide_skyscraper | 69.4 |  |
| crello_5ab9076df07aee69770e9039__leaderboard | 71.5 |  |
| crello_58898cb195a7a863ddcc3121__x_post | 71.5 |  |
| crello_5c0a9ab5133a785392285eeb__presentation_16_9 | 74.8 |  |
| crello_5f608eb1a637ee11e3222235__a4_poster__150_dpi | 75.2 |  |
| crello_5b408b451eb1c99e2aae2129__email_header | 77.3 |  |
| crello_5f05bdae499b85dcc767e8b7__youtube_thumbnail | 79.0 |  |
| crello_5d691f00abc8ea6d1c396bbf__facebook_cover | 79.0 |  |
| crello_5d9f1ce1abc8ea6d1c98c087__leaderboard | 79.0 |  |
| crello_593118b995a7a863ddcdc93c__facebook_cover | 79.1 |  |
| crello_5d691f00abc8ea6d1c396bbf__instagram_story | 79.5 |  |
| crello_5e2aa1c89fea0cc374ba2bff__instagram_portrait | 80.6 |  |
| crello_5d08ef5d8cba87f943e4586b__wide_skyscraper | 82.6 |  |
| crello_5889bcfd95a7a863ddcc3cb9__facebook_cover | 83.3 |  |
| crello_5e2aa1c89fea0cc374ba2bff__instagram_post | 83.3 |  |
| crello_5f1feb5fa637ee11e36e6b4c__facebook_cover | 84.4 |  |
| crello_591586e795a7a863ddcd830d__instagram_post | 85.8 |  |
| crello_5888da2995a7a863ddcc2bc6__email_header | 86.4 |  |
| crello_5e4120f69fea0cc3748a41f2__leaderboard | 86.6 |  |
| crello_5f50b378a637ee11e34fa5c6__instagram_post | 86.8 |  |
| crello_5bd1ce9878e1194aa6378870__instagram_post | 87.0 |  |
| crello_5889bcfd95a7a863ddcc3cb9__medium_rectangle | 87.0 |  |
| crello_589d7bb295a7a863ddcc5532__presentation_16_9 | 87.1 |  |
| crello_5f97cda3a637ee11e32492b7__facebook_post | 87.1 |  |
| crello_5eba7bc3499b85dcc7d44cdc__facebook_cover | 87.7 |  |
| crello_5f97cda3a637ee11e32492b7__medium_rectangle | 88.0 |  |
| crello_5dadaa37abc8ea6d1cf0a669__facebook_cover | 88.5 |  |
| crello_5dee48ac9fea0cc3743716a5__medium_rectangle | 89.1 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 5581 ms, median 4642 ms, p95 10421 ms, max 15534 ms
- check: mean 3 ms, median 3 ms, p95 7 ms, max 12 ms
- score: mean 5 ms, median 4 ms, p95 11 ms, max 15 ms
- render: n/a
