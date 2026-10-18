# Benchmark summary: crello-dev

Engine commit `2db5b11`, 600 cases (200 designs), render=yes, contrast=no, jobs=8.

- **Cases passing every hard rule: 592/600** (98.7%)
- **Average score: 89.72** / 100
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
| 0.141 | 0.044 | 0.048 | 0.053 | 0.243 | 0.025 | 0.026 | 0.419 | 0.012 | 0.083 | 0.187 | 0.112 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 44 | 43 | 89.6 |
| Email Header | 600x200 | 42 | 41 | 88.3 |
| Facebook Cover | 820x312 | 46 | 46 | 89.6 |
| Facebook Post | 1200x630 | 32 | 31 | 91.9 |
| Instagram Portrait | 1080x1350 | 42 | 42 | 90.6 |
| Instagram Post | 1080x1080 | 35 | 35 | 88.3 |
| Instagram Story | 1080x1920 | 41 | 41 | 89.1 |
| Leaderboard | 728x90 | 36 | 34 | 88.8 |
| LinkedIn Banner | 1584x396 | 47 | 47 | 89.0 |
| Medium Rectangle | 300x250 | 38 | 38 | 90.2 |
| Pinterest Pin | 1000x1500 | 35 | 34 | 90.9 |
| Presentation 16:9 | 1920x1080 | 39 | 39 | 89.7 |
| Wide Skyscraper | 160x600 | 32 | 30 | 89.5 |
| X Post | 1600x900 | 47 | 47 | 90.8 |
| YouTube Thumbnail | 1280x720 | 44 | 44 | 89.8 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_59b266771350e8329300d02b__pinterest_pin | 76.2 | hidden_element:svg12;hidden_element:svg13 |
| crello_59b266771350e8329300d02b__a4_poster__150_dpi | 76.3 | hidden_element:svg12;hidden_element:svg13 |
| crello_5dc3c996abc8ea6d1cbcc226__leaderboard | 82.1 | hidden_element:svg1 |
| crello_59b266771350e8329300d02b__facebook_post | 84.6 | hidden_element:svg12;hidden_element:svg13 |
| crello_5b756cf71cc8aa5429ba8033__leaderboard | 84.8 | hidden_element:svg7;hidden_element:svg10 |
| crello_5952967595a7a863ddce0220__wide_skyscraper | 90.0 | hidden_element:svg1 |
| crello_5ac4a8ce4b568b8eece2fd9b__wide_skyscraper | 93.7 | hidden_element:svg3;hidden_element:svg4 |
| crello_5fabaa59a637ee11e3a88e87__email_header | 98.5 | hidden_element:svg1 |
| crello_5888da2995a7a863ddcc2bc6__a4_poster__150_dpi | 65.8 |  |
| crello_5888da2995a7a863ddcc2bc6__instagram_story | 67.5 |  |
| crello_5e563cae1cc98b350a78b20a__leaderboard | 69.4 |  |
| crello_58a4155595a7a863ddcc6dd1__linkedin_banner | 71.4 |  |
| crello_58afff1695a7a863ddcc8fb5__email_header | 75.2 |  |
| crello_58a4155595a7a863ddcc6dd1__instagram_post | 75.5 |  |
| crello_5cf14d798cba87f9434fefb8__x_post | 75.5 |  |
| crello_5f916f8ea637ee11e3169da4__linkedin_banner | 76.0 |  |
| crello_592811a995a7a863ddcd9183__instagram_portrait | 76.3 |  |
| crello_592811a995a7a863ddcd9183__youtube_thumbnail | 76.6 |  |
| crello_5954beee95a7a863ddce15ec__youtube_thumbnail | 76.6 |  |
| crello_5cf14d798cba87f9434fefb8__instagram_post | 76.8 |  |
| crello_5bd1ce9878e1194aa6378870__instagram_post | 77.3 |  |
| crello_5f05bdae499b85dcc767e8b7__instagram_portrait | 77.5 |  |
| crello_5954beee95a7a863ddce15ec__linkedin_banner | 77.6 |  |
| crello_5ab9076df07aee69770e9039__leaderboard | 77.8 |  |
| crello_592811a995a7a863ddcd9183__instagram_story | 77.8 |  |
| crello_5a82c4a6f07aee6977be6291__medium_rectangle | 78.1 |  |
| crello_58a4155595a7a863ddcc6dd1__a4_poster__150_dpi | 78.4 |  |
| crello_58afff1695a7a863ddcc8fb5__a4_poster__150_dpi | 78.6 |  |
| crello_59535df595a7a863ddce1115__linkedin_banner | 78.6 |  |
| crello_5db1a542abc8ea6d1cd835af__leaderboard | 78.6 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 4463 ms, median 3664 ms, p95 10936 ms, max 19197 ms
- check: mean 4 ms, median 3 ms, p95 9 ms, max 21 ms
- score: mean 5 ms, median 4 ms, p95 16 ms, max 32 ms
- render: mean 324 ms, median 204 ms, p95 1052 ms, max 1989 ms
