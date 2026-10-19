# Benchmark summary: crello-structure

Engine commit `v2-2-g2e4c9a5`, 120 cases (40 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 118/120** (98.3%)
- **Average score: 82.60** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 4 | 2 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.398 | 0.048 | 0.097 | 0.072 | 0.229 | 0.381 | 0.146 | 0.293 | 0.020 | 0.035 | 0.452 | 0.020 | 0.177 | 0.283 | 0.172 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 6 | 6 | 85.9 |
| Email Header | 600x200 | 7 | 7 | 80.7 |
| Facebook Cover | 820x312 | 8 | 8 | 77.1 |
| Facebook Post | 1200x630 | 7 | 7 | 87.4 |
| Instagram Portrait | 1080x1350 | 5 | 5 | 84.7 |
| Instagram Post | 1080x1080 | 9 | 9 | 87.8 |
| Instagram Story | 1080x1920 | 8 | 8 | 82.9 |
| Leaderboard | 728x90 | 8 | 7 | 72.9 |
| LinkedIn Banner | 1584x396 | 10 | 10 | 78.5 |
| Medium Rectangle | 300x250 | 10 | 10 | 85.3 |
| Pinterest Pin | 1000x1500 | 5 | 5 | 74.4 |
| Presentation 16:9 | 1920x1080 | 13 | 13 | 86.1 |
| Wide Skyscraper | 160x600 | 7 | 6 | 84.0 |
| X Post | 1600x900 | 10 | 10 | 84.8 |
| YouTube Thumbnail | 1280x720 | 7 | 7 | 82.5 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5b756cf71cc8aa5429ba8033__leaderboard | 89.3 | hidden_element:svg7;hidden_element:svg10 |
| crello_5ac4a8ce4b568b8eece2fd9b__wide_skyscraper | 94.6 | hidden_element:svg3;hidden_element:svg4 |
| crello_5e563cae1cc98b350a78b20a__leaderboard | 48.4 |  |
| crello_5ef32868499b85dcc76e66fc__email_header | 50.4 |  |
| crello_5e4facf31cc98b350aeffeeb__facebook_cover | 56.4 |  |
| crello_5db1a542abc8ea6d1cd835af__leaderboard | 60.1 |  |
| crello_5ab9076df07aee69770e9039__leaderboard | 61.3 |  |
| crello_5ef32868499b85dcc76e66fc__linkedin_banner | 61.5 |  |
| crello_5db1a542abc8ea6d1cd835af__wide_skyscraper | 63.9 |  |
| crello_5d691f00abc8ea6d1c396bbf__presentation_16_9 | 65.4 |  |
| crello_5d08e5d48cba87f943d052da__instagram_story | 67.2 |  |
| crello_5d691f00abc8ea6d1c396bbf__facebook_cover | 68.6 |  |
| crello_5d691f00abc8ea6d1c396bbf__instagram_story | 69.3 |  |
| crello_5d9cad46abc8ea6d1c234bd4__x_post | 69.7 |  |
| crello_5889bb0195a7a863ddcc394f__pinterest_pin | 69.9 |  |
| crello_5d9cad46abc8ea6d1c234bd4__presentation_16_9 | 70.1 |  |
| crello_5889bb0195a7a863ddcc394f__a4_poster__150_dpi | 70.2 |  |
| crello_59b26ae81350e8329300d444__linkedin_banner | 70.3 |  |
| crello_5e563cae1cc98b350a78b20a__pinterest_pin | 70.5 |  |
| crello_59b26ae81350e8329300d444__leaderboard | 71.8 |  |
| crello_593118b995a7a863ddcdc93c__facebook_cover | 71.8 |  |
| crello_5d371dae8cba87f943a63b67__leaderboard | 72.7 |  |
| crello_5c179226133a7853927e0f04__medium_rectangle | 73.0 |  |
| crello_5f05bdae499b85dcc767e8b7__youtube_thumbnail | 73.0 |  |
| crello_5954beee95a7a863ddce15ec__linkedin_banner | 73.3 |  |
| crello_58a3089795a7a863ddcc66de__pinterest_pin | 74.2 |  |
| crello_5ef32868499b85dcc76e66fc__medium_rectangle | 74.4 |  |
| crello_5954beee95a7a863ddce15ec__youtube_thumbnail | 75.3 |  |
| crello_59535df595a7a863ddce1115__linkedin_banner | 75.4 |  |
| crello_593118b995a7a863ddcdc93c__instagram_post | 75.5 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 8294 ms, median 7760 ms, p95 15162 ms, max 20619 ms
- check: mean 5 ms, median 4 ms, p95 12 ms, max 16 ms
- score: mean 9 ms, median 7 ms, p95 21 ms, max 26 ms
- render: n/a
