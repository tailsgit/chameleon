# Benchmark summary: crello-holdout

Engine commit `v1-submittable-3-g71b0674-dirty`, 300 cases (100 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 295/300** (98.3%)
- **Average score: 88.67** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 12 | 5 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.210 | 0.052 | 0.058 | 0.061 | 0.222 | 0.309 | 0.021 | 0.029 | 0.034 | 0.452 | 0.024 | 0.052 | 0.210 | 0.094 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 24 | 24 | 90.2 |
| Email Header | 600x200 | 18 | 18 | 86.2 |
| Facebook Cover | 820x312 | 28 | 28 | 90.1 |
| Facebook Post | 1200x630 | 17 | 17 | 88.8 |
| Instagram Portrait | 1080x1350 | 20 | 20 | 91.3 |
| Instagram Post | 1080x1080 | 17 | 17 | 88.6 |
| Instagram Story | 1080x1920 | 20 | 20 | 89.7 |
| Leaderboard | 728x90 | 20 | 20 | 86.3 |
| LinkedIn Banner | 1584x396 | 16 | 16 | 89.2 |
| Medium Rectangle | 300x250 | 18 | 16 | 87.3 |
| Pinterest Pin | 1000x1500 | 19 | 19 | 88.8 |
| Presentation 16:9 | 1920x1080 | 18 | 18 | 87.0 |
| Wide Skyscraper | 160x600 | 23 | 20 | 86.7 |
| X Post | 1600x900 | 23 | 23 | 89.5 |
| YouTube Thumbnail | 1280x720 | 19 | 19 | 89.3 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5dee3d5b9fea0cc374173de6__wide_skyscraper | 76.5 | hidden_element:svg10;hidden_element:svg14 |
| crello_58a1e88995a7a863ddcc657e__wide_skyscraper | 82.1 | hidden_element:svg7;hidden_element:svg8;hidden_element:svg9;hidden_element:svg11 |
| crello_590af4b195a7a863ddcd68ac__wide_skyscraper | 91.2 | hidden_element:svg3;hidden_element:svg4 |
| crello_59b26bab1350e8329300d51a__medium_rectangle | 92.5 | hidden_element:svg1;hidden_element:svg2 |
| crello_5dee3d5b9fea0cc374173de6__medium_rectangle | 93.8 | hidden_element:svg10;hidden_element:svg14 |
| crello_5dcbd0779fea0cc374098ede__email_header | 62.1 |  |
| crello_588a0fc195a7a863ddcc4509__wide_skyscraper | 65.7 |  |
| crello_5c6c325085ea3c16f9256af7__pinterest_pin | 65.8 |  |
| crello_5dcbd0779fea0cc374098ede__presentation_16_9 | 66.2 |  |
| crello_5c6c325085ea3c16f9256af7__wide_skyscraper | 66.9 |  |
| crello_5c6c325085ea3c16f9256af7__leaderboard | 67.1 |  |
| crello_5e7c749c4b3890eb07230de5__email_header | 67.3 |  |
| crello_5dcbd0779fea0cc374098ede__facebook_post | 67.9 |  |
| crello_590b112e95a7a863ddcd749f__youtube_thumbnail | 68.2 |  |
| crello_59528ca795a7a863ddcdfa21__leaderboard | 68.6 |  |
| crello_5f4ce0dea637ee11e3dd5cfa__a4_poster__150_dpi | 69.0 |  |
| crello_588a0fc195a7a863ddcc4509__instagram_post | 71.6 |  |
| crello_5f9150d1a637ee11e397afd4__medium_rectangle | 71.8 |  |
| crello_5ef30fa9499b85dcc73cb20e__pinterest_pin | 73.0 |  |
| crello_5c0a89da133a785392a7f992__leaderboard | 73.3 |  |
| crello_5f5f3fdfa637ee11e3358fbe__facebook_cover | 75.2 |  |
| crello_5c0a89da133a785392a7f992__medium_rectangle | 75.3 |  |
| crello_5f4ce0dea637ee11e3dd5cfa__facebook_cover | 76.0 |  |
| crello_59b26bab1350e8329300d51a__x_post | 76.2 |  |
| crello_59b26bab1350e8329300d51a__instagram_post | 76.2 |  |
| crello_5f5f3fdfa637ee11e3358fbe__instagram_story | 77.2 |  |
| crello_5dee48ad9fea0cc374371a03__leaderboard | 77.3 |  |
| crello_588a0fc195a7a863ddcc4509__a4_poster__150_dpi | 77.5 |  |
| crello_5aa91c86f07aee6977472083__instagram_post | 77.5 |  |
| crello_5f97d1eba637ee11e33257c9__a4_poster__150_dpi | 77.8 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 4740 ms, median 4110 ms, p95 11355 ms, max 16796 ms
- check: mean 4 ms, median 3 ms, p95 9 ms, max 17 ms
- score: mean 6 ms, median 5 ms, p95 16 ms, max 37 ms
- render: n/a
