# Benchmark summary: crello-dev

Engine commit `v3-12-g49abc60-dirty`, 600 cases (200 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 592/600** (98.7%)
- **Average score: 90.41** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 13 | 8 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | share_drift | space | balance | floating | emphasis | siblings | alignment | reading_order | legibility | coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.229 | 0.029 | 0.049 | 0.044 | 0.141 | 0.198 | 0.051 | 0.377 | 0.136 | 0.031 | 0.033 | 0.356 | 0.027 | 0.094 | 0.204 | 0.123 | 0.025 | 0.073 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 44 | 43 | 91.5 |
| Email Header | 600x200 | 42 | 41 | 88.7 |
| Facebook Cover | 820x312 | 46 | 46 | 89.7 |
| Facebook Post | 1200x630 | 32 | 31 | 92.9 |
| Instagram Portrait | 1080x1350 | 42 | 42 | 92.5 |
| Instagram Post | 1080x1080 | 35 | 35 | 90.9 |
| Instagram Story | 1080x1920 | 41 | 41 | 91.9 |
| Leaderboard | 728x90 | 36 | 34 | 86.7 |
| LinkedIn Banner | 1584x396 | 47 | 47 | 88.6 |
| Medium Rectangle | 300x250 | 38 | 38 | 90.5 |
| Pinterest Pin | 1000x1500 | 35 | 34 | 92.0 |
| Presentation 16:9 | 1920x1080 | 39 | 39 | 89.6 |
| Wide Skyscraper | 160x600 | 32 | 30 | 89.0 |
| X Post | 1600x900 | 47 | 47 | 90.3 |
| YouTube Thumbnail | 1280x720 | 44 | 44 | 91.7 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5b756cf71cc8aa5429ba8033__leaderboard | 70.7 | hidden_element:svg7;hidden_element:svg10 |
| crello_5dc3c996abc8ea6d1cbcc226__leaderboard | 88.7 | hidden_element:svg1 |
| crello_59b266771350e8329300d02b__a4_poster__150_dpi | 89.9 | hidden_element:svg12;hidden_element:svg13 |
| crello_59b266771350e8329300d02b__pinterest_pin | 90.0 | hidden_element:svg12;hidden_element:svg13 |
| crello_59b266771350e8329300d02b__facebook_post | 91.8 | hidden_element:svg12;hidden_element:svg13 |
| crello_5952967595a7a863ddce0220__wide_skyscraper | 94.1 | hidden_element:svg1 |
| crello_5ac4a8ce4b568b8eece2fd9b__wide_skyscraper | 94.7 | hidden_element:svg3;hidden_element:svg4 |
| crello_5fabaa59a637ee11e3a88e87__email_header | 98.9 | hidden_element:svg1 |
| crello_5ef30e1a499b85dcc739d4b0__facebook_cover | 56.8 |  |
| crello_5ef30e1a499b85dcc739d4b0__linkedin_banner | 58.9 |  |
| crello_5d08e5d48cba87f943d052da__instagram_story | 59.9 |  |
| crello_5c8fb5a885ea3c16f94b98c1__wide_skyscraper | 60.8 |  |
| crello_5e4facf31cc98b350aeffeeb__facebook_cover | 61.8 |  |
| crello_5d9cad46abc8ea6d1c234bd4__presentation_16_9 | 61.9 |  |
| crello_5d9cad46abc8ea6d1c234bd4__x_post | 61.9 |  |
| crello_5d08e5d48cba87f943d052da__presentation_16_9 | 61.9 |  |
| crello_5e563cae1cc98b350a78b20a__leaderboard | 62.1 |  |
| crello_5f5b3068a637ee11e383ae07__email_header | 62.1 |  |
| crello_5952a15795a7a863ddce0a02__presentation_16_9 | 62.5 |  |
| crello_5952a15795a7a863ddce0a02__youtube_thumbnail | 62.6 |  |
| crello_58a3089795a7a863ddcc66de__pinterest_pin | 64.2 |  |
| crello_5d08e5d48cba87f943d052da__facebook_post | 64.2 |  |
| crello_5eb9a87e499b85dcc709b1a3__linkedin_banner | 64.9 |  |
| crello_5c8fb5a885ea3c16f94b98c1__instagram_story | 65.0 |  |
| crello_5bdc41119259f9ba5416c94c__instagram_post | 65.2 |  |
| crello_5bd1c58378e1194aa60ad4a3__email_header | 65.7 |  |
| crello_5ef30e1a499b85dcc739d4b0__pinterest_pin | 65.7 |  |
| crello_58898cb195a7a863ddcc3121__leaderboard | 66.4 |  |
| crello_58a3089795a7a863ddcc66de__medium_rectangle | 66.8 |  |
| crello_5bd1c58378e1194aa60ad4a3__facebook_cover | 66.8 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 6295 ms, median 5878 ms, p95 12401 ms, max 15580 ms
- check: mean 4 ms, median 3 ms, p95 8 ms, max 14 ms
- score: mean 6 ms, median 4 ms, p95 14 ms, max 30 ms
- render: n/a
