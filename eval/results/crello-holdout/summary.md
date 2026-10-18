# Benchmark summary: crello-holdout

Engine commit `2db5b11-dirty`, 300 cases (100 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 295/300** (98.3%)
- **Average score: 89.39** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 12 | 5 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.156 | 0.050 | 0.065 | 0.056 | 0.250 | 0.030 | 0.025 | 0.415 | 0.017 | 0.053 | 0.215 | 0.104 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 24 | 24 | 90.4 |
| Email Header | 600x200 | 18 | 18 | 88.7 |
| Facebook Cover | 820x312 | 28 | 28 | 90.1 |
| Facebook Post | 1200x630 | 17 | 17 | 89.8 |
| Instagram Portrait | 1080x1350 | 20 | 20 | 90.3 |
| Instagram Post | 1080x1080 | 17 | 17 | 89.5 |
| Instagram Story | 1080x1920 | 20 | 20 | 89.4 |
| Leaderboard | 728x90 | 20 | 20 | 85.5 |
| LinkedIn Banner | 1584x396 | 16 | 16 | 87.8 |
| Medium Rectangle | 300x250 | 18 | 16 | 88.1 |
| Pinterest Pin | 1000x1500 | 19 | 19 | 88.7 |
| Presentation 16:9 | 1920x1080 | 18 | 18 | 90.6 |
| Wide Skyscraper | 160x600 | 23 | 20 | 89.4 |
| X Post | 1600x900 | 23 | 23 | 91.1 |
| YouTube Thumbnail | 1280x720 | 19 | 19 | 90.3 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5dee3d5b9fea0cc374173de6__wide_skyscraper | 83.7 | hidden_element:svg10;hidden_element:svg14 |
| crello_590af4b195a7a863ddcd68ac__wide_skyscraper | 88.4 | hidden_element:svg3;hidden_element:svg4 |
| crello_59b26bab1350e8329300d51a__medium_rectangle | 89.0 | hidden_element:svg1;hidden_element:svg2 |
| crello_58a1e88995a7a863ddcc657e__wide_skyscraper | 91.8 | hidden_element:svg7;hidden_element:svg8;hidden_element:svg9;hidden_element:svg11 |
| crello_5dee3d5b9fea0cc374173de6__medium_rectangle | 93.8 | hidden_element:svg10;hidden_element:svg14 |
| crello_5f041ec0499b85dcc7b152b6__email_header | 67.2 |  |
| crello_5928035b95a7a863ddcd8ff7__linkedin_banner | 68.4 |  |
| crello_5f9150d1a637ee11e397afd4__medium_rectangle | 71.3 |  |
| crello_59528ca795a7a863ddcdfa21__leaderboard | 72.5 |  |
| crello_5f041ec0499b85dcc7b152b6__leaderboard | 72.8 |  |
| crello_588a0fc195a7a863ddcc4509__wide_skyscraper | 73.7 |  |
| crello_5ddd35239fea0cc374ef3ebf__instagram_portrait | 73.8 |  |
| crello_595287fd95a7a863ddcdf690__facebook_cover | 75.0 |  |
| crello_5f041ec0499b85dcc7b152b6__pinterest_pin | 75.5 |  |
| crello_5ddd35239fea0cc374ef3ebf__instagram_story | 75.8 |  |
| crello_5f9150d1a637ee11e397afd4__linkedin_banner | 76.6 |  |
| crello_58ab127e95a7a863ddcc75f7__leaderboard | 76.7 |  |
| crello_5aa91c86f07aee6977472083__instagram_post | 77.7 |  |
| crello_58ab127e95a7a863ddcc75f7__instagram_story | 79.1 |  |
| crello_59b26bab1350e8329300d51a__x_post | 79.4 |  |
| crello_590b112e95a7a863ddcd749f__leaderboard | 79.5 |  |
| crello_5f3b7921a637ee11e3188a19__facebook_post | 79.6 |  |
| crello_5f0415c7499b85dcc7a2d9b1__facebook_cover | 80.0 |  |
| crello_5dcbd0779fea0cc374098ede__email_header | 80.4 |  |
| crello_588a0fc195a7a863ddcc4509__instagram_post | 80.7 |  |
| crello_5f5f3fdfa637ee11e3358fbe__facebook_cover | 81.0 |  |
| crello_58ab127e95a7a863ddcc75f7__instagram_portrait | 81.1 |  |
| crello_5888cfbb95a7a863ddcc262c__presentation_16_9 | 81.5 |  |
| crello_5888cfbb95a7a863ddcc262c__youtube_thumbnail | 81.5 |  |
| crello_5eb180ed499b85dcc75848d8__x_post | 81.5 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 4631 ms, median 3824 ms, p95 11485 ms, max 26134 ms
- check: mean 4 ms, median 3 ms, p95 10 ms, max 17 ms
- score: mean 7 ms, median 5 ms, p95 17 ms, max 40 ms
- render: n/a
