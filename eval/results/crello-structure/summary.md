# Benchmark summary: crello-structure

Engine commit `v4-5-g6a0f590-dirty`, 120 cases (40 designs), render=no, contrast=no, jobs=4.

- **Cases passing every hard rule: 120/120** (100.0%)
- **Average score: 87.62** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| (none) | 0 | 0 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | share_drift | space | balance | floating | emphasis | siblings | alignment | reading_order | legibility | coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.383 | 0.055 | 0.078 | 0.068 | 0.220 | 0.351 | 0.059 | 0.423 | 0.191 | 0.025 | 0.012 | 0.411 | 0.042 | 0.142 | 0.241 | 0.139 | 0.022 | 0.047 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 6 | 6 | 89.9 |
| Email Header | 600x200 | 7 | 7 | 84.3 |
| Facebook Cover | 820x312 | 8 | 8 | 85.8 |
| Facebook Post | 1200x630 | 7 | 7 | 91.1 |
| Instagram Portrait | 1080x1350 | 5 | 5 | 88.5 |
| Instagram Post | 1080x1080 | 9 | 9 | 90.0 |
| Instagram Story | 1080x1920 | 8 | 8 | 88.5 |
| Leaderboard | 728x90 | 8 | 8 | 78.9 |
| LinkedIn Banner | 1584x396 | 10 | 10 | 88.6 |
| Medium Rectangle | 300x250 | 10 | 10 | 88.8 |
| Pinterest Pin | 1000x1500 | 5 | 5 | 80.3 |
| Presentation 16:9 | 1920x1080 | 13 | 13 | 90.2 |
| Wide Skyscraper | 160x600 | 7 | 7 | 86.5 |
| X Post | 1600x900 | 10 | 10 | 89.4 |
| YouTube Thumbnail | 1280x720 | 7 | 7 | 88.6 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_58a3089795a7a863ddcc66de__pinterest_pin | 68.7 |  |
| crello_5889bb0195a7a863ddcc394f__email_header | 68.9 |  |
| crello_5db1a542abc8ea6d1cd835af__leaderboard | 70.0 |  |
| crello_5db1a542abc8ea6d1cd835af__wide_skyscraper | 72.3 |  |
| crello_5e563cae1cc98b350a78b20a__leaderboard | 72.4 |  |
| crello_5cf14d798cba87f9434fefb8__pinterest_pin | 74.1 |  |
| crello_5889bb0195a7a863ddcc394f__a4_poster__150_dpi | 74.9 |  |
| crello_5889bb0195a7a863ddcc394f__pinterest_pin | 75.6 |  |
| crello_5cf14d798cba87f9434fefb8__instagram_post | 75.7 |  |
| crello_5ab9076df07aee69770e9039__leaderboard | 76.2 |  |
| crello_5cf14d798cba87f9434fefb8__x_post | 76.5 |  |
| crello_5e4facf31cc98b350aeffeeb__facebook_cover | 76.6 |  |
| crello_5d691f00abc8ea6d1c396bbf__presentation_16_9 | 76.6 |  |
| crello_5d9cad46abc8ea6d1c234bd4__email_header | 77.4 |  |
| crello_5f05bdae499b85dcc767e8b7__youtube_thumbnail | 78.1 |  |
| crello_58a3089795a7a863ddcc66de__medium_rectangle | 78.1 |  |
| crello_5b756cf71cc8aa5429ba8033__wide_skyscraper | 78.6 |  |
| crello_5d691f00abc8ea6d1c396bbf__facebook_cover | 78.9 |  |
| crello_5d691f00abc8ea6d1c396bbf__instagram_story | 79.5 |  |
| crello_5ef32868499b85dcc76e66fc__medium_rectangle | 79.7 |  |
| crello_5d9f1ce1abc8ea6d1c98c087__leaderboard | 79.7 |  |
| crello_593118b995a7a863ddcdc93c__facebook_cover | 79.7 |  |
| crello_5bc09b7278e1194aa6496e3e__instagram_portrait | 80.2 |  |
| crello_59b26ae81350e8329300d444__leaderboard | 80.3 |  |
| crello_5e4facf31cc98b350aeffeeb__linkedin_banner | 80.3 |  |
| crello_5b756cf71cc8aa5429ba8033__leaderboard | 80.8 |  |
| crello_5954beee95a7a863ddce15ec__linkedin_banner | 81.0 |  |
| crello_5d371dae8cba87f943a63b67__leaderboard | 81.0 |  |
| crello_59535df595a7a863ddce1115__linkedin_banner | 81.2 |  |
| crello_589df8d495a7a863ddcc5e39__presentation_16_9 | 81.2 |  |

## Timings (per case, this machine, 4 worker processes in parallel)

- resize: mean 7101 ms, median 6841 ms, p95 12618 ms, max 15244 ms
- check: mean 3 ms, median 3 ms, p95 6 ms, max 9 ms
- score: mean 8 ms, median 6 ms, p95 20 ms, max 28 ms
- render: n/a
