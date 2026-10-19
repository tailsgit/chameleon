# Benchmark summary: crello-dev

Engine commit `v2-2-gc68ee0e`, 600 cases (200 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 592/600** (98.7%)
- **Average score: 89.32** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 13 | 8 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | share_drift | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.239 | 0.026 | 0.046 | 0.038 | 0.127 | 0.183 | 0.058 | 0.394 | 0.126 | 0.028 | 0.033 | 0.347 | 0.029 | 0.092 | 0.201 | 0.119 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 44 | 43 | 90.2 |
| Email Header | 600x200 | 42 | 41 | 88.2 |
| Facebook Cover | 820x312 | 46 | 46 | 88.3 |
| Facebook Post | 1200x630 | 32 | 31 | 90.7 |
| Instagram Portrait | 1080x1350 | 42 | 42 | 92.1 |
| Instagram Post | 1080x1080 | 35 | 35 | 88.3 |
| Instagram Story | 1080x1920 | 41 | 41 | 91.0 |
| Leaderboard | 728x90 | 36 | 34 | 85.0 |
| LinkedIn Banner | 1584x396 | 47 | 47 | 89.0 |
| Medium Rectangle | 300x250 | 38 | 38 | 88.8 |
| Pinterest Pin | 1000x1500 | 35 | 34 | 90.6 |
| Presentation 16:9 | 1920x1080 | 39 | 39 | 88.9 |
| Wide Skyscraper | 160x600 | 32 | 30 | 88.0 |
| X Post | 1600x900 | 47 | 47 | 89.6 |
| YouTube Thumbnail | 1280x720 | 44 | 44 | 90.4 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5dc3c996abc8ea6d1cbcc226__leaderboard | 85.2 | hidden_element:svg1 |
| crello_59b266771350e8329300d02b__a4_poster__150_dpi | 88.5 | hidden_element:svg12;hidden_element:svg13 |
| crello_59b266771350e8329300d02b__pinterest_pin | 89.4 | hidden_element:svg12;hidden_element:svg13 |
| crello_59b266771350e8329300d02b__facebook_post | 90.3 | hidden_element:svg12;hidden_element:svg13 |
| crello_5b756cf71cc8aa5429ba8033__leaderboard | 90.3 | hidden_element:svg7;hidden_element:svg10 |
| crello_5952967595a7a863ddce0220__wide_skyscraper | 92.3 | hidden_element:svg1 |
| crello_5ac4a8ce4b568b8eece2fd9b__wide_skyscraper | 94.8 | hidden_element:svg3;hidden_element:svg4 |
| crello_5fabaa59a637ee11e3a88e87__email_header | 98.6 | hidden_element:svg1 |
| crello_5e563cae1cc98b350a78b20a__leaderboard | 50.8 |  |
| crello_5d08e5d48cba87f943d052da__facebook_post | 51.1 |  |
| crello_5db1a542abc8ea6d1cd835af__leaderboard | 53.4 |  |
| crello_5bdc41119259f9ba5416c94c__instagram_post | 54.3 |  |
| crello_59b7ff721350e8329300fd73__medium_rectangle | 60.9 |  |
| crello_5ef32868499b85dcc76e66fc__email_header | 61.1 |  |
| crello_5e563cae1cc98b350a78b20a__x_post | 62.6 |  |
| crello_5ab9076df07aee69770e9039__leaderboard | 63.0 |  |
| crello_5db1a542abc8ea6d1cd835af__wide_skyscraper | 63.1 |  |
| crello_5dadaa37abc8ea6d1cf0a669__facebook_cover | 64.1 |  |
| crello_58b0124395a7a863ddcc91fa__linkedin_banner | 66.0 |  |
| crello_5dadaa37abc8ea6d1cf0a669__x_post | 66.5 |  |
| crello_5c0a9ab5133a785392285eeb__presentation_16_9 | 67.0 |  |
| crello_5c8fb5a885ea3c16f94b98c1__wide_skyscraper | 67.3 |  |
| crello_5cf14d798cba87f9434fefb8__pinterest_pin | 67.5 |  |
| crello_5f3bbac8a637ee11e3a8e3aa__email_header | 68.4 |  |
| crello_5d08e5d48cba87f943d052da__instagram_story | 68.6 |  |
| crello_5d9cad46abc8ea6d1c234bd4__presentation_16_9 | 68.8 |  |
| crello_5d9cad46abc8ea6d1c234bd4__x_post | 68.8 |  |
| crello_5cf14d798cba87f9434fefb8__instagram_post | 69.3 |  |
| crello_5d691f00abc8ea6d1c396bbf__presentation_16_9 | 69.5 |  |
| crello_5952a15795a7a863ddce0a02__presentation_16_9 | 69.6 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 6636 ms, median 5710 ms, p95 13795 ms, max 21447 ms
- check: mean 4 ms, median 3 ms, p95 9 ms, max 18 ms
- score: mean 6 ms, median 4 ms, p95 17 ms, max 31 ms
- render: n/a
