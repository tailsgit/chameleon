# Benchmark summary: crello-dev

Engine commit `v1-submittable-1-gf0338a2-dirty`, 600 cases (200 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 592/600** (98.7%)
- **Average score: 90.45** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 13 | 8 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.277 | 0.036 | 0.046 | 0.027 | 0.099 | 0.119 | 0.019 | 0.029 | 0.411 | 0.020 | 0.089 | 0.197 | 0.146 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 44 | 43 | 91.2 |
| Email Header | 600x200 | 42 | 41 | 89.4 |
| Facebook Cover | 820x312 | 46 | 46 | 89.8 |
| Facebook Post | 1200x630 | 32 | 31 | 92.7 |
| Instagram Portrait | 1080x1350 | 42 | 42 | 91.9 |
| Instagram Post | 1080x1080 | 35 | 35 | 89.8 |
| Instagram Story | 1080x1920 | 41 | 41 | 91.9 |
| Leaderboard | 728x90 | 36 | 34 | 85.2 |
| LinkedIn Banner | 1584x396 | 47 | 47 | 89.7 |
| Medium Rectangle | 300x250 | 38 | 38 | 91.3 |
| Pinterest Pin | 1000x1500 | 35 | 34 | 90.7 |
| Presentation 16:9 | 1920x1080 | 39 | 39 | 90.9 |
| Wide Skyscraper | 160x600 | 32 | 30 | 88.7 |
| X Post | 1600x900 | 47 | 47 | 91.9 |
| YouTube Thumbnail | 1280x720 | 44 | 44 | 91.0 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5dc3c996abc8ea6d1cbcc226__leaderboard | 84.2 | hidden_element:svg1 |
| crello_59b266771350e8329300d02b__pinterest_pin | 85.6 | hidden_element:svg12;hidden_element:svg13 |
| crello_59b266771350e8329300d02b__a4_poster__150_dpi | 85.8 | hidden_element:svg12;hidden_element:svg13 |
| crello_59b266771350e8329300d02b__facebook_post | 87.5 | hidden_element:svg12;hidden_element:svg13 |
| crello_5b756cf71cc8aa5429ba8033__leaderboard | 89.4 | hidden_element:svg7;hidden_element:svg10 |
| crello_5952967595a7a863ddce0220__wide_skyscraper | 94.4 | hidden_element:svg1 |
| crello_5ac4a8ce4b568b8eece2fd9b__wide_skyscraper | 94.5 | hidden_element:svg3;hidden_element:svg4 |
| crello_5fabaa59a637ee11e3a88e87__email_header | 98.1 | hidden_element:svg1 |
| crello_5e563cae1cc98b350a78b20a__leaderboard | 61.0 |  |
| crello_5db1a542abc8ea6d1cd835af__leaderboard | 64.3 |  |
| crello_5ab9076df07aee69770e9039__leaderboard | 65.1 |  |
| crello_5ef32868499b85dcc76e66fc__email_header | 65.5 |  |
| crello_5954beee95a7a863ddce15ec__linkedin_banner | 65.5 |  |
| crello_5c8fb5a885ea3c16f94b98c1__wide_skyscraper | 66.1 |  |
| crello_5f1feb5fa637ee11e36e6b4c__leaderboard | 66.4 |  |
| crello_5f3bbac8a637ee11e3a8e3aa__email_header | 67.3 |  |
| crello_5954beee95a7a863ddce15ec__youtube_thumbnail | 67.5 |  |
| crello_58898cb195a7a863ddcc3121__leaderboard | 68.4 |  |
| crello_59535df595a7a863ddce1115__linkedin_banner | 68.8 |  |
| crello_5d691f00abc8ea6d1c396bbf__presentation_16_9 | 68.9 |  |
| crello_5db1a542abc8ea6d1cd835af__wide_skyscraper | 69.2 |  |
| crello_5c8fb5a885ea3c16f94b98c1__facebook_cover | 69.8 |  |
| crello_5ef32868499b85dcc76e66fc__medium_rectangle | 70.1 |  |
| crello_5d691f00abc8ea6d1c396bbf__facebook_cover | 70.2 |  |
| crello_5c8fb5a885ea3c16f94b98c1__instagram_story | 70.5 |  |
| crello_59b26ae81350e8329300d444__leaderboard | 70.6 |  |
| crello_59535df595a7a863ddce1115__facebook_cover | 70.7 |  |
| crello_5ee9d148499b85dcc7b6b727__leaderboard | 71.0 |  |
| crello_5bd1c58378e1194aa60ad4a3__email_header | 71.4 |  |
| crello_5f608eb1a637ee11e3222235__wide_skyscraper | 71.6 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 7238 ms, median 6505 ms, p95 15225 ms, max 18293 ms
- check: mean 4 ms, median 3 ms, p95 9 ms, max 17 ms
- score: mean 6 ms, median 4 ms, p95 17 ms, max 39 ms
- render: n/a
