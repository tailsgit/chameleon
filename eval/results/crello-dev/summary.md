# Benchmark summary: crello-dev

Engine commit `v1-submittable-dirty`, 600 cases (200 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 592/600** (98.7%)
- **Average score: 91.31** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 13 | 8 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.190 | 0.024 | 0.046 | 0.016 | 0.149 | 0.018 | 0.020 | 0.378 | 0.011 | 0.084 | 0.191 | 0.144 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 44 | 43 | 91.6 |
| Email Header | 600x200 | 42 | 41 | 90.8 |
| Facebook Cover | 820x312 | 46 | 46 | 91.3 |
| Facebook Post | 1200x630 | 32 | 31 | 92.6 |
| Instagram Portrait | 1080x1350 | 42 | 42 | 91.6 |
| Instagram Post | 1080x1080 | 35 | 35 | 89.8 |
| Instagram Story | 1080x1920 | 41 | 41 | 91.0 |
| Leaderboard | 728x90 | 36 | 34 | 89.6 |
| LinkedIn Banner | 1584x396 | 47 | 47 | 91.9 |
| Medium Rectangle | 300x250 | 38 | 38 | 91.9 |
| Pinterest Pin | 1000x1500 | 35 | 34 | 92.5 |
| Presentation 16:9 | 1920x1080 | 39 | 39 | 90.9 |
| Wide Skyscraper | 160x600 | 32 | 30 | 90.3 |
| X Post | 1600x900 | 47 | 47 | 92.2 |
| YouTube Thumbnail | 1280x720 | 44 | 44 | 91.4 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_59b266771350e8329300d02b__pinterest_pin | 80.8 | hidden_element:svg12;hidden_element:svg13 |
| crello_59b266771350e8329300d02b__a4_poster__150_dpi | 81.4 | hidden_element:svg12;hidden_element:svg13 |
| crello_5dc3c996abc8ea6d1cbcc226__leaderboard | 82.5 | hidden_element:svg1 |
| crello_59b266771350e8329300d02b__facebook_post | 83.8 | hidden_element:svg12;hidden_element:svg13 |
| crello_5b756cf71cc8aa5429ba8033__leaderboard | 84.8 | hidden_element:svg7;hidden_element:svg10 |
| crello_5952967595a7a863ddce0220__wide_skyscraper | 90.0 | hidden_element:svg1 |
| crello_5ac4a8ce4b568b8eece2fd9b__wide_skyscraper | 93.7 | hidden_element:svg3;hidden_element:svg4 |
| crello_5fabaa59a637ee11e3a88e87__email_header | 98.5 | hidden_element:svg1 |
| crello_5e563cae1cc98b350a78b20a__leaderboard | 69.8 |  |
| crello_5954beee95a7a863ddce15ec__linkedin_banner | 78.2 |  |
| crello_5db1a542abc8ea6d1cd835af__leaderboard | 78.6 |  |
| crello_5d691f00abc8ea6d1c396bbf__facebook_cover | 78.8 |  |
| crello_5f05bdae499b85dcc767e8b7__email_header | 79.2 |  |
| crello_5888da2995a7a863ddcc2bc6__instagram_story | 79.2 |  |
| crello_5cf14d798cba87f9434fefb8__instagram_post | 79.3 |  |
| crello_5f05bdae499b85dcc767e8b7__youtube_thumbnail | 79.5 |  |
| crello_5db1a542abc8ea6d1cd835af__wide_skyscraper | 79.6 |  |
| crello_5f05bdae499b85dcc767e8b7__instagram_portrait | 79.7 |  |
| crello_5888da2995a7a863ddcc2bc6__a4_poster__150_dpi | 80.0 |  |
| crello_595329ac95a7a863ddce0b7c__wide_skyscraper | 80.1 |  |
| crello_5954beee95a7a863ddce15ec__youtube_thumbnail | 80.1 |  |
| crello_5b76e9ec1cc8aa5429ad3902__presentation_16_9 | 80.4 |  |
| crello_5f97cda3a637ee11e32492b7__facebook_post | 80.5 |  |
| crello_59535df595a7a863ddce1115__facebook_cover | 80.5 |  |
| crello_5f9171f7a637ee11e324ed2d__pinterest_pin | 80.8 |  |
| crello_5947b6c395a7a863ddcdd9f0__instagram_post | 81.0 |  |
| crello_5c179226133a7853927e0f04__facebook_cover | 81.1 |  |
| crello_5cde61b77d4459dfe1b30f5b__instagram_post | 81.1 |  |
| crello_5dc3c996abc8ea6d1cbcc226__youtube_thumbnail | 81.1 |  |
| crello_5c8fb5a885ea3c16f94b98c1__wide_skyscraper | 81.3 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 6895 ms, median 5804 ms, p95 17307 ms, max 32731 ms
- check: mean 4 ms, median 3 ms, p95 10 ms, max 20 ms
- score: mean 6 ms, median 4 ms, p95 16 ms, max 57 ms
- render: n/a
