# Benchmark summary: crello-dev

Engine commit `v1-submittable-3-g71b0674-dirty`, 600 cases (200 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 592/600** (98.7%)
- **Average score: 88.76** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 13 | 8 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.184 | 0.053 | 0.045 | 0.062 | 0.208 | 0.300 | 0.037 | 0.025 | 0.031 | 0.447 | 0.018 | 0.087 | 0.182 | 0.112 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 44 | 43 | 88.6 |
| Email Header | 600x200 | 42 | 41 | 86.6 |
| Facebook Cover | 820x312 | 46 | 46 | 88.7 |
| Facebook Post | 1200x630 | 32 | 31 | 92.2 |
| Instagram Portrait | 1080x1350 | 42 | 42 | 90.2 |
| Instagram Post | 1080x1080 | 35 | 35 | 86.6 |
| Instagram Story | 1080x1920 | 41 | 41 | 89.7 |
| Leaderboard | 728x90 | 36 | 34 | 86.4 |
| LinkedIn Banner | 1584x396 | 47 | 47 | 87.6 |
| Medium Rectangle | 300x250 | 38 | 38 | 89.8 |
| Pinterest Pin | 1000x1500 | 35 | 34 | 88.9 |
| Presentation 16:9 | 1920x1080 | 39 | 39 | 89.0 |
| Wide Skyscraper | 160x600 | 32 | 30 | 89.3 |
| X Post | 1600x900 | 47 | 47 | 89.8 |
| YouTube Thumbnail | 1280x720 | 44 | 44 | 88.4 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_59b266771350e8329300d02b__pinterest_pin | 70.8 | hidden_element:svg12;hidden_element:svg13 |
| crello_59b266771350e8329300d02b__a4_poster__150_dpi | 71.1 | hidden_element:svg12;hidden_element:svg13 |
| crello_59b266771350e8329300d02b__facebook_post | 77.1 | hidden_element:svg12;hidden_element:svg13 |
| crello_5dc3c996abc8ea6d1cbcc226__leaderboard | 87.5 | hidden_element:svg1 |
| crello_5b756cf71cc8aa5429ba8033__leaderboard | 91.0 | hidden_element:svg7;hidden_element:svg10 |
| crello_5952967595a7a863ddce0220__wide_skyscraper | 95.6 | hidden_element:svg1 |
| crello_5ac4a8ce4b568b8eece2fd9b__wide_skyscraper | 95.6 | hidden_element:svg3;hidden_element:svg4 |
| crello_5fabaa59a637ee11e3a88e87__email_header | 98.5 | hidden_element:svg1 |
| crello_5e563cae1cc98b350a78b20a__leaderboard | 48.4 |  |
| crello_5e563cae1cc98b350a78b20a__pinterest_pin | 53.7 |  |
| crello_5f5b3068a637ee11e383ae07__email_header | 56.9 |  |
| crello_5ab9076df07aee69770e9039__leaderboard | 57.8 |  |
| crello_5db1a542abc8ea6d1cd835af__leaderboard | 60.2 |  |
| crello_59b7ff721350e8329300fd73__medium_rectangle | 61.4 |  |
| crello_5db1a542abc8ea6d1cd835af__wide_skyscraper | 64.1 |  |
| crello_5c8fb5a885ea3c16f94b98c1__wide_skyscraper | 66.9 |  |
| crello_58a4155595a7a863ddcc6dd1__linkedin_banner | 67.4 |  |
| crello_5d08e5d48cba87f943d052da__instagram_story | 67.4 |  |
| crello_5dadaa37abc8ea6d1cf0a669__instagram_portrait | 69.0 |  |
| crello_5ef30e1a499b85dcc739d4b0__facebook_cover | 69.2 |  |
| crello_5888da2995a7a863ddcc2bc6__a4_poster__150_dpi | 69.2 |  |
| crello_5eb9a87e499b85dcc709b1a3__youtube_thumbnail | 69.8 |  |
| crello_5ef30e1a499b85dcc739d4b0__pinterest_pin | 69.9 |  |
| crello_5c8fb5a885ea3c16f94b98c1__instagram_story | 70.0 |  |
| crello_593118b995a7a863ddcdc93c__instagram_post | 70.4 |  |
| crello_5e4120f69fea0cc3748a41f2__instagram_story | 70.8 |  |
| crello_5c41df6b048d064dbc80111f__instagram_portrait | 70.8 |  |
| crello_5db1a542abc8ea6d1cd835af__youtube_thumbnail | 71.1 |  |
| crello_5888da2995a7a863ddcc2bc6__instagram_story | 71.2 |  |
| crello_5c0a9ab5133a785392285eeb__presentation_16_9 | 71.7 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 4588 ms, median 3772 ms, p95 11442 ms, max 16587 ms
- check: mean 4 ms, median 3 ms, p95 8 ms, max 16 ms
- score: mean 5 ms, median 4 ms, p95 15 ms, max 29 ms
- render: n/a
