# Benchmark summary: crello-holdout

Engine commit `v2-1-gaefa4de-dirty`, 300 cases (100 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 295/300** (98.3%)
- **Average score: 89.32** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 12 | 5 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | share_drift | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.257 | 0.033 | 0.057 | 0.045 | 0.128 | 0.176 | 0.034 | 0.432 | 0.139 | 0.023 | 0.041 | 0.360 | 0.035 | 0.058 | 0.229 | 0.124 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 24 | 24 | 91.5 |
| Email Header | 600x200 | 18 | 18 | 86.5 |
| Facebook Cover | 820x312 | 28 | 28 | 90.9 |
| Facebook Post | 1200x630 | 17 | 17 | 87.6 |
| Instagram Portrait | 1080x1350 | 20 | 20 | 91.6 |
| Instagram Post | 1080x1080 | 17 | 17 | 88.3 |
| Instagram Story | 1080x1920 | 20 | 20 | 89.3 |
| Leaderboard | 728x90 | 20 | 20 | 87.1 |
| LinkedIn Banner | 1584x396 | 16 | 16 | 90.5 |
| Medium Rectangle | 300x250 | 18 | 16 | 87.1 |
| Pinterest Pin | 1000x1500 | 19 | 19 | 90.6 |
| Presentation 16:9 | 1920x1080 | 18 | 18 | 88.1 |
| Wide Skyscraper | 160x600 | 23 | 20 | 85.7 |
| X Post | 1600x900 | 23 | 23 | 91.7 |
| YouTube Thumbnail | 1280x720 | 19 | 19 | 91.7 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5dee3d5b9fea0cc374173de6__wide_skyscraper | 76.0 | hidden_element:svg10;hidden_element:svg14 |
| crello_58a1e88995a7a863ddcc657e__wide_skyscraper | 81.2 | hidden_element:svg7;hidden_element:svg8;hidden_element:svg9;hidden_element:svg11 |
| crello_590af4b195a7a863ddcd68ac__wide_skyscraper | 89.6 | hidden_element:svg3;hidden_element:svg4 |
| crello_59b26bab1350e8329300d51a__medium_rectangle | 90.1 | hidden_element:svg1;hidden_element:svg2 |
| crello_5dee3d5b9fea0cc374173de6__medium_rectangle | 94.2 | hidden_element:svg10;hidden_element:svg14 |
| crello_5dcbd0779fea0cc374098ede__email_header | 63.3 |  |
| crello_588a0fc195a7a863ddcc4509__wide_skyscraper | 65.0 |  |
| crello_5e7c749c4b3890eb07230de5__email_header | 66.6 |  |
| crello_5c6c325085ea3c16f9256af7__leaderboard | 68.5 |  |
| crello_5eb180ed499b85dcc75848d8__facebook_post | 69.1 |  |
| crello_5c6c325085ea3c16f9256af7__wide_skyscraper | 70.2 |  |
| crello_5ef30fa9499b85dcc73cb20e__presentation_16_9 | 70.4 |  |
| crello_5c0a89da133a785392a7f992__medium_rectangle | 71.5 |  |
| crello_5e7c749c4b3890eb07230de5__facebook_post | 71.6 |  |
| crello_5d6928bdabc8ea6d1c57334e__presentation_16_9 | 72.8 |  |
| crello_5c6c325085ea3c16f9256af7__pinterest_pin | 73.2 |  |
| crello_5c0a89da133a785392a7f992__leaderboard | 74.4 |  |
| crello_588a0fc195a7a863ddcc4509__instagram_post | 74.7 |  |
| crello_5928047f95a7a863ddcd90c7__email_header | 75.5 |  |
| crello_5930129195a7a863ddcdc014__wide_skyscraper | 75.5 |  |
| crello_59528ca795a7a863ddcdfa21__leaderboard | 75.8 |  |
| crello_5f4ce0dea637ee11e3dd5cfa__facebook_cover | 76.2 |  |
| crello_5c0a89da133a785392a7f992__instagram_post | 76.2 |  |
| crello_5ef30fa9499b85dcc73cb20e__linkedin_banner | 76.7 |  |
| crello_5aa91c86f07aee6977472083__instagram_post | 76.8 |  |
| crello_5d690aa1abc8ea6d1c0e0df9__medium_rectangle | 76.9 |  |
| crello_5930129195a7a863ddcdc014__instagram_story | 77.1 |  |
| crello_5928035b95a7a863ddcd8ff7__facebook_post | 77.4 |  |
| crello_5f5f3fdfa637ee11e3358fbe__instagram_story | 77.5 |  |
| crello_58cfaec595a7a863ddccc715__facebook_cover | 77.5 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 7631 ms, median 6907 ms, p95 15588 ms, max 28223 ms
- check: mean 5 ms, median 4 ms, p95 11 ms, max 20 ms
- score: mean 7 ms, median 5 ms, p95 21 ms, max 53 ms
- render: n/a
