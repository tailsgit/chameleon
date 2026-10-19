# Benchmark summary: crello-structure

Engine commit `v3-12-g49abc60-dirty`, 120 cases (40 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 118/120** (98.3%)
- **Average score: 85.20** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 4 | 2 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | share_drift | space | balance | floating | emphasis | siblings | alignment | reading_order | legibility | coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.344 | 0.059 | 0.084 | 0.069 | 0.218 | 0.384 | 0.115 | 0.363 | 0.207 | 0.025 | 0.021 | 0.437 | 0.033 | 0.172 | 0.262 | 0.158 | 0.056 | 0.104 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 6 | 6 | 89.8 |
| Email Header | 600x200 | 7 | 7 | 84.4 |
| Facebook Cover | 820x312 | 8 | 8 | 82.6 |
| Facebook Post | 1200x630 | 7 | 7 | 87.0 |
| Instagram Portrait | 1080x1350 | 5 | 5 | 88.0 |
| Instagram Post | 1080x1080 | 9 | 9 | 90.0 |
| Instagram Story | 1080x1920 | 8 | 8 | 83.6 |
| Leaderboard | 728x90 | 8 | 7 | 76.0 |
| LinkedIn Banner | 1584x396 | 10 | 10 | 85.8 |
| Medium Rectangle | 300x250 | 10 | 10 | 87.6 |
| Pinterest Pin | 1000x1500 | 5 | 5 | 80.3 |
| Presentation 16:9 | 1920x1080 | 13 | 13 | 85.2 |
| Wide Skyscraper | 160x600 | 7 | 6 | 84.8 |
| X Post | 1600x900 | 10 | 10 | 85.1 |
| YouTube Thumbnail | 1280x720 | 7 | 7 | 87.3 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5b756cf71cc8aa5429ba8033__leaderboard | 70.7 | hidden_element:svg7;hidden_element:svg10 |
| crello_5ac4a8ce4b568b8eece2fd9b__wide_skyscraper | 94.7 | hidden_element:svg3;hidden_element:svg4 |
| crello_5d08e5d48cba87f943d052da__instagram_story | 59.9 |  |
| crello_5e4facf31cc98b350aeffeeb__facebook_cover | 61.8 |  |
| crello_5d9cad46abc8ea6d1c234bd4__presentation_16_9 | 61.9 |  |
| crello_5d9cad46abc8ea6d1c234bd4__x_post | 61.9 |  |
| crello_5d08e5d48cba87f943d052da__presentation_16_9 | 61.9 |  |
| crello_5e563cae1cc98b350a78b20a__leaderboard | 62.1 |  |
| crello_5d08e5d48cba87f943d052da__facebook_post | 62.3 |  |
| crello_58a3089795a7a863ddcc66de__pinterest_pin | 64.2 |  |
| crello_5f0418f6499b85dcc7a767f9__linkedin_banner | 66.6 |  |
| crello_58a3089795a7a863ddcc66de__medium_rectangle | 66.8 |  |
| crello_5e563cae1cc98b350a78b20a__x_post | 69.0 |  |
| crello_5db1a542abc8ea6d1cd835af__leaderboard | 69.5 |  |
| crello_5ab9076df07aee69770e9039__leaderboard | 71.5 |  |
| crello_5db1a542abc8ea6d1cd835af__wide_skyscraper | 71.8 |  |
| crello_5b756cf71cc8aa5429ba8033__linkedin_banner | 72.5 |  |
| crello_5b756cf71cc8aa5429ba8033__wide_skyscraper | 72.5 |  |
| crello_5f0418f6499b85dcc7a767f9__instagram_story | 72.9 |  |
| crello_5d9cad46abc8ea6d1c234bd4__email_header | 73.5 |  |
| crello_5cf14d798cba87f9434fefb8__pinterest_pin | 74.1 |  |
| crello_5ef32868499b85dcc76e66fc__email_header | 74.3 |  |
| crello_5cf14d798cba87f9434fefb8__instagram_post | 76.2 |  |
| crello_5cf14d798cba87f9434fefb8__x_post | 76.5 |  |
| crello_5d691f00abc8ea6d1c396bbf__presentation_16_9 | 76.8 |  |
| crello_5889bb0195a7a863ddcc394f__a4_poster__150_dpi | 77.5 |  |
| crello_5ef32868499b85dcc76e66fc__medium_rectangle | 78.7 |  |
| crello_5f05bdae499b85dcc767e8b7__youtube_thumbnail | 79.0 |  |
| crello_5d691f00abc8ea6d1c396bbf__facebook_cover | 79.0 |  |
| crello_5d9f1ce1abc8ea6d1c98c087__leaderboard | 79.0 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 7898 ms, median 8155 ms, p95 14503 ms, max 15318 ms
- check: mean 5 ms, median 4 ms, p95 10 ms, max 15 ms
- score: mean 9 ms, median 7 ms, p95 22 ms, max 27 ms
- render: n/a
