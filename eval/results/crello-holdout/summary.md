# Benchmark summary: crello-holdout

Engine commit `0436a50-dirty`, 300 cases (100 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 295/300** (98.3%)
- **Average score: 89.55** / 100
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
| 0.186 | 0.048 | 0.064 | 0.051 | 0.228 | 0.031 | 0.024 | 0.422 | 0.020 | 0.053 | 0.203 | 0.099 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 24 | 24 | 90.7 |
| Email Header | 600x200 | 18 | 18 | 88.5 |
| Facebook Cover | 820x312 | 28 | 28 | 90.0 |
| Facebook Post | 1200x630 | 17 | 17 | 89.9 |
| Instagram Portrait | 1080x1350 | 20 | 20 | 91.1 |
| Instagram Post | 1080x1080 | 17 | 17 | 89.5 |
| Instagram Story | 1080x1920 | 20 | 20 | 89.1 |
| Leaderboard | 728x90 | 20 | 20 | 85.6 |
| LinkedIn Banner | 1584x396 | 16 | 16 | 89.1 |
| Medium Rectangle | 300x250 | 18 | 16 | 87.8 |
| Pinterest Pin | 1000x1500 | 19 | 19 | 88.4 |
| Presentation 16:9 | 1920x1080 | 18 | 18 | 90.9 |
| Wide Skyscraper | 160x600 | 23 | 20 | 89.5 |
| X Post | 1600x900 | 23 | 23 | 91.6 |
| YouTube Thumbnail | 1280x720 | 19 | 19 | 90.4 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5dee3d5b9fea0cc374173de6__wide_skyscraper | 83.7 | hidden_element:svg10;hidden_element:svg14 |
| crello_590af4b195a7a863ddcd68ac__wide_skyscraper | 88.4 | hidden_element:svg3;hidden_element:svg4 |
| crello_59b26bab1350e8329300d51a__medium_rectangle | 89.0 | hidden_element:svg1;hidden_element:svg2 |
| crello_58a1e88995a7a863ddcc657e__wide_skyscraper | 91.8 | hidden_element:svg7;hidden_element:svg8;hidden_element:svg9;hidden_element:svg11 |
| crello_5dee3d5b9fea0cc374173de6__medium_rectangle | 93.8 | hidden_element:svg10;hidden_element:svg14 |
| crello_5f9150d1a637ee11e397afd4__medium_rectangle | 71.3 |  |
| crello_59528ca795a7a863ddcdfa21__leaderboard | 72.5 |  |
| crello_5f041ec0499b85dcc7b152b6__leaderboard | 72.8 |  |
| crello_588a0fc195a7a863ddcc4509__wide_skyscraper | 73.7 |  |
| crello_595287fd95a7a863ddcdf690__facebook_cover | 75.0 |  |
| crello_5f041ec0499b85dcc7b152b6__email_header | 76.0 |  |
| crello_5f041ec0499b85dcc7b152b6__pinterest_pin | 76.2 |  |
| crello_5ddd35239fea0cc374ef3ebf__instagram_story | 76.6 |  |
| crello_5c0a89da133a785392a7f992__leaderboard | 76.8 |  |
| crello_5e7c749c4b3890eb07230de5__email_header | 76.9 |  |
| crello_5ef30fa9499b85dcc73cb20e__pinterest_pin | 77.2 |  |
| crello_5aa91c86f07aee6977472083__instagram_post | 77.7 |  |
| crello_5ddd35239fea0cc374ef3ebf__instagram_portrait | 78.3 |  |
| crello_590b112e95a7a863ddcd749f__leaderboard | 78.5 |  |
| crello_58ab127e95a7a863ddcc75f7__leaderboard | 79.1 |  |
| crello_58ab127e95a7a863ddcc75f7__instagram_story | 79.1 |  |
| crello_588a0fc195a7a863ddcc4509__instagram_post | 79.4 |  |
| crello_5f0415c7499b85dcc7a2d9b1__facebook_cover | 80.0 |  |
| crello_5dcbd0779fea0cc374098ede__email_header | 80.4 |  |
| crello_5f9150d1a637ee11e397afd4__linkedin_banner | 80.5 |  |
| crello_59b26bab1350e8329300d51a__x_post | 80.7 |  |
| crello_5f5f3fdfa637ee11e3358fbe__facebook_cover | 81.0 |  |
| crello_58ab127e95a7a863ddcc75f7__instagram_portrait | 81.1 |  |
| crello_590b112e95a7a863ddcd749f__youtube_thumbnail | 81.5 |  |
| crello_5889915e95a7a863ddcc3491__instagram_story | 81.6 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 5411 ms, median 4476 ms, p95 12597 ms, max 46216 ms
- check: mean 5 ms, median 4 ms, p95 10 ms, max 17 ms
- score: mean 7 ms, median 5 ms, p95 19 ms, max 36 ms
- render: n/a
