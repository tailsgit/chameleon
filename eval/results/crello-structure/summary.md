# Benchmark summary: crello-structure

Engine commit `v2-2-gc68ee0e-dirty`, 120 cases (40 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 118/120** (98.3%)
- **Average score: 82.82** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 4 | 2 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | share_drift | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.374 | 0.058 | 0.083 | 0.084 | 0.208 | 0.375 | 0.128 | 0.382 | 0.204 | 0.027 | 0.020 | 0.433 | 0.042 | 0.180 | 0.264 | 0.167 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 6 | 6 | 87.4 |
| Email Header | 600x200 | 7 | 7 | 80.6 |
| Facebook Cover | 820x312 | 8 | 8 | 79.0 |
| Facebook Post | 1200x630 | 7 | 7 | 83.0 |
| Instagram Portrait | 1080x1350 | 5 | 5 | 83.6 |
| Instagram Post | 1080x1080 | 9 | 9 | 86.9 |
| Instagram Story | 1080x1920 | 8 | 8 | 83.5 |
| Leaderboard | 728x90 | 8 | 7 | 74.2 |
| LinkedIn Banner | 1584x396 | 10 | 10 | 81.2 |
| Medium Rectangle | 300x250 | 10 | 10 | 85.7 |
| Pinterest Pin | 1000x1500 | 5 | 5 | 79.4 |
| Presentation 16:9 | 1920x1080 | 13 | 13 | 85.3 |
| Wide Skyscraper | 160x600 | 7 | 6 | 83.3 |
| X Post | 1600x900 | 10 | 10 | 83.6 |
| YouTube Thumbnail | 1280x720 | 7 | 7 | 83.1 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5b756cf71cc8aa5429ba8033__leaderboard | 90.3 | hidden_element:svg7;hidden_element:svg10 |
| crello_5ac4a8ce4b568b8eece2fd9b__wide_skyscraper | 94.8 | hidden_element:svg3;hidden_element:svg4 |
| crello_5e4facf31cc98b350aeffeeb__linkedin_banner | 47.1 |  |
| crello_5e563cae1cc98b350a78b20a__leaderboard | 50.8 |  |
| crello_5d08e5d48cba87f943d052da__facebook_post | 51.1 |  |
| crello_5db1a542abc8ea6d1cd835af__leaderboard | 60.2 |  |
| crello_5ef32868499b85dcc76e66fc__email_header | 61.1 |  |
| crello_5e563cae1cc98b350a78b20a__x_post | 62.6 |  |
| crello_5ab9076df07aee69770e9039__leaderboard | 63.0 |  |
| crello_5db1a542abc8ea6d1cd835af__wide_skyscraper | 63.1 |  |
| crello_5cf14d798cba87f9434fefb8__pinterest_pin | 67.5 |  |
| crello_5d08e5d48cba87f943d052da__instagram_story | 68.6 |  |
| crello_5d9cad46abc8ea6d1c234bd4__presentation_16_9 | 68.8 |  |
| crello_5d9cad46abc8ea6d1c234bd4__x_post | 68.8 |  |
| crello_5cf14d798cba87f9434fefb8__instagram_post | 69.3 |  |
| crello_5d691f00abc8ea6d1c396bbf__presentation_16_9 | 69.5 |  |
| crello_5889bb0195a7a863ddcc394f__email_header | 70.0 |  |
| crello_5ef32868499b85dcc76e66fc__medium_rectangle | 70.7 |  |
| crello_5cf14d798cba87f9434fefb8__x_post | 70.7 |  |
| crello_58a3089795a7a863ddcc66de__pinterest_pin | 71.7 |  |
| crello_5f05bdae499b85dcc767e8b7__youtube_thumbnail | 72.4 |  |
| crello_5d691f00abc8ea6d1c396bbf__facebook_cover | 72.5 |  |
| crello_593118b995a7a863ddcdc93c__facebook_cover | 72.6 |  |
| crello_5d691f00abc8ea6d1c396bbf__instagram_story | 73.0 |  |
| crello_5c88fb6d85ea3c16f98df0db__facebook_cover | 73.1 |  |
| crello_5db1a542abc8ea6d1cd835af__youtube_thumbnail | 74.3 |  |
| crello_5ef32868499b85dcc76e66fc__linkedin_banner | 74.5 |  |
| crello_5954beee95a7a863ddce15ec__linkedin_banner | 74.6 |  |
| crello_5889bb0195a7a863ddcc394f__a4_poster__150_dpi | 74.8 |  |
| crello_5f0418f6499b85dcc7a767f9__linkedin_banner | 74.9 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 9825 ms, median 10152 ms, p95 14750 ms, max 20122 ms
- check: mean 6 ms, median 5 ms, p95 13 ms, max 17 ms
- score: mean 10 ms, median 8 ms, p95 27 ms, max 34 ms
- render: n/a
