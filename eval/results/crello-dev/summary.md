# Benchmark summary: crello-dev

Engine commit `v4-5-g6a0f590-dirty`, 600 cases (200 designs), render=no, contrast=no, jobs=4.

- **Cases passing every hard rule: 598/600** (99.7%)
- **Average score: 91.49** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 2 | 2 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | share_drift | space | balance | floating | emphasis | siblings | alignment | reading_order | legibility | coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.236 | 0.029 | 0.048 | 0.040 | 0.132 | 0.167 | 0.033 | 0.406 | 0.128 | 0.028 | 0.026 | 0.330 | 0.031 | 0.080 | 0.201 | 0.115 | 0.015 | 0.054 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 44 | 44 | 92.6 |
| Email Header | 600x200 | 42 | 41 | 89.7 |
| Facebook Cover | 820x312 | 46 | 46 | 91.1 |
| Facebook Post | 1200x630 | 32 | 32 | 94.2 |
| Instagram Portrait | 1080x1350 | 42 | 42 | 93.4 |
| Instagram Post | 1080x1080 | 35 | 35 | 91.5 |
| Instagram Story | 1080x1920 | 41 | 41 | 93.1 |
| Leaderboard | 728x90 | 36 | 36 | 88.0 |
| LinkedIn Banner | 1584x396 | 47 | 47 | 89.4 |
| Medium Rectangle | 300x250 | 38 | 38 | 91.2 |
| Pinterest Pin | 1000x1500 | 35 | 35 | 92.7 |
| Presentation 16:9 | 1920x1080 | 39 | 39 | 92.0 |
| Wide Skyscraper | 160x600 | 32 | 31 | 90.1 |
| X Post | 1600x900 | 47 | 47 | 91.4 |
| YouTube Thumbnail | 1280x720 | 44 | 44 | 92.2 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5952967595a7a863ddce0220__wide_skyscraper | 94.1 | hidden_element:svg1 |
| crello_5fabaa59a637ee11e3a88e87__email_header | 98.9 | hidden_element:svg1 |
| crello_5eb9a87e499b85dcc709b1a3__youtube_thumbnail | 65.6 |  |
| crello_5eb9a87e499b85dcc709b1a3__linkedin_banner | 65.6 |  |
| crello_58898cb195a7a863ddcc3121__leaderboard | 66.4 |  |
| crello_5f5b3068a637ee11e383ae07__email_header | 66.6 |  |
| crello_5952a15795a7a863ddce0a02__linkedin_banner | 67.3 |  |
| crello_58a3089795a7a863ddcc66de__pinterest_pin | 68.7 |  |
| crello_5f608eb1a637ee11e3222235__wide_skyscraper | 69.4 |  |
| crello_5db1a542abc8ea6d1cd835af__leaderboard | 70.0 |  |
| crello_59b7ff721350e8329300fd73__medium_rectangle | 70.3 |  |
| crello_58898cb195a7a863ddcc3121__x_post | 71.5 |  |
| crello_5bdc41119259f9ba5416c94c__instagram_post | 71.5 |  |
| crello_58b0124395a7a863ddcc91fa__linkedin_banner | 71.6 |  |
| crello_5eec6cc3499b85dcc79f7b05__instagram_portrait | 71.9 |  |
| crello_5db1a542abc8ea6d1cd835af__wide_skyscraper | 72.3 |  |
| crello_5f608eb1a637ee11e3222235__x_post | 72.4 |  |
| crello_5ef30e1a499b85dcc739d4b0__facebook_cover | 72.4 |  |
| crello_5bd1c58378e1194aa60ad4a3__linkedin_banner | 72.4 |  |
| crello_58b0124395a7a863ddcc91fa__email_header | 72.6 |  |
| crello_5bd1c58378e1194aa60ad4a3__email_header | 72.6 |  |
| crello_5e563cae1cc98b350a78b20a__leaderboard | 73.0 |  |
| crello_5c8fb5a885ea3c16f94b98c1__wide_skyscraper | 73.7 |  |
| crello_5889bb0195a7a863ddcc394f__email_header | 73.9 |  |
| crello_5cf14d798cba87f9434fefb8__pinterest_pin | 74.1 |  |
| crello_5888da2995a7a863ddcc2bc6__a4_poster__150_dpi | 74.3 |  |
| crello_5c0a9ab5133a785392285eeb__presentation_16_9 | 74.8 |  |
| crello_5889bb0195a7a863ddcc394f__a4_poster__150_dpi | 74.9 |  |
| crello_5eb9a87e499b85dcc709b1a3__medium_rectangle | 75.1 |  |
| crello_5f608eb1a637ee11e3222235__a4_poster__150_dpi | 75.2 |  |

## Timings (per case, this machine, 4 worker processes in parallel)

- resize: mean 5370 ms, median 5053 ms, p95 10166 ms, max 15472 ms
- check: mean 2 ms, median 2 ms, p95 5 ms, max 12 ms
- score: mean 5 ms, median 3 ms, p95 13 ms, max 29 ms
- render: n/a
