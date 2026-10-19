# Benchmark summary: crello-holdout

Engine commit `v2-2-g2e4c9a5-dirty`, 300 cases (100 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 295/300** (98.3%)
- **Average score: 87.80** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 12 | 5 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.280 | 0.043 | 0.066 | 0.060 | 0.176 | 0.262 | 0.054 | 0.270 | 0.031 | 0.033 | 0.350 | 0.043 | 0.073 | 0.255 | 0.141 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 24 | 24 | 91.0 |
| Email Header | 600x200 | 18 | 18 | 86.1 |
| Facebook Cover | 820x312 | 28 | 28 | 90.8 |
| Facebook Post | 1200x630 | 17 | 17 | 82.9 |
| Instagram Portrait | 1080x1350 | 20 | 20 | 87.3 |
| Instagram Post | 1080x1080 | 17 | 17 | 88.0 |
| Instagram Story | 1080x1920 | 20 | 20 | 86.0 |
| Leaderboard | 728x90 | 20 | 20 | 82.6 |
| LinkedIn Banner | 1584x396 | 16 | 16 | 88.9 |
| Medium Rectangle | 300x250 | 18 | 16 | 86.5 |
| Pinterest Pin | 1000x1500 | 19 | 19 | 89.6 |
| Presentation 16:9 | 1920x1080 | 18 | 18 | 89.9 |
| Wide Skyscraper | 160x600 | 23 | 20 | 84.8 |
| X Post | 1600x900 | 23 | 23 | 89.1 |
| YouTube Thumbnail | 1280x720 | 19 | 19 | 91.5 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5dee3d5b9fea0cc374173de6__wide_skyscraper | 76.5 | hidden_element:svg10;hidden_element:svg14 |
| crello_58a1e88995a7a863ddcc657e__wide_skyscraper | 79.9 | hidden_element:svg7;hidden_element:svg8;hidden_element:svg9;hidden_element:svg11 |
| crello_59b26bab1350e8329300d51a__medium_rectangle | 85.3 | hidden_element:svg1;hidden_element:svg2 |
| crello_590af4b195a7a863ddcd68ac__wide_skyscraper | 89.5 | hidden_element:svg3;hidden_element:svg4 |
| crello_5dee3d5b9fea0cc374173de6__medium_rectangle | 93.8 | hidden_element:svg10;hidden_element:svg14 |
| crello_5f3b7921a637ee11e3188a19__facebook_post | 49.2 |  |
| crello_5f5f3fdfa637ee11e3358fbe__x_post | 52.1 |  |
| crello_5c6c325085ea3c16f9256af7__leaderboard | 54.0 |  |
| crello_58ab127e95a7a863ddcc75f7__leaderboard | 60.8 |  |
| crello_5dcbd0779fea0cc374098ede__email_header | 63.1 |  |
| crello_5c6c325085ea3c16f9256af7__wide_skyscraper | 66.7 |  |
| crello_5e7c749c4b3890eb07230de5__email_header | 66.7 |  |
| crello_588a0fc195a7a863ddcc4509__wide_skyscraper | 68.0 |  |
| crello_5db2b83aabc8ea6d1c443e7b__instagram_story | 68.7 |  |
| crello_5889915e95a7a863ddcc3491__instagram_story | 69.1 |  |
| crello_5dcbd0779fea0cc374098ede__facebook_post | 69.7 |  |
| crello_5dcbd0779fea0cc374098ede__presentation_16_9 | 70.0 |  |
| crello_5c0e5306133a7853929c3664__medium_rectangle | 70.2 |  |
| crello_5f5f3fdfa637ee11e3358fbe__instagram_story | 70.4 |  |
| crello_588a0fc195a7a863ddcc4509__instagram_post | 70.8 |  |
| crello_5db2b83aabc8ea6d1c443e7b__a4_poster__150_dpi | 71.0 |  |
| crello_5930148c95a7a863ddcdc199__wide_skyscraper | 71.0 |  |
| crello_5e7c749c4b3890eb07230de5__facebook_post | 71.5 |  |
| crello_5a71cb3c8c32ec6f8b15d155__presentation_16_9 | 71.6 |  |
| crello_5930148c95a7a863ddcdc199__email_header | 72.0 |  |
| crello_5930129195a7a863ddcdc014__wide_skyscraper | 72.0 |  |
| crello_5c0e5306133a7853929c3664__pinterest_pin | 72.2 |  |
| crello_5db2b83aabc8ea6d1c443e7b__instagram_post | 72.3 |  |
| crello_58ab127e95a7a863ddcc75f7__instagram_portrait | 72.9 |  |
| crello_5928047f95a7a863ddcd90c7__medium_rectangle | 73.2 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 7458 ms, median 6885 ms, p95 15343 ms, max 20611 ms
- check: mean 5 ms, median 4 ms, p95 11 ms, max 22 ms
- score: mean 7 ms, median 5 ms, p95 20 ms, max 60 ms
- render: n/a
