# Benchmark summary: crello-dev

Engine commit `v2-2-g2e4c9a5`, 600 cases (200 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 592/600** (98.7%)
- **Average score: 88.78** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 13 | 8 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.228 | 0.023 | 0.057 | 0.056 | 0.160 | 0.228 | 0.061 | 0.239 | 0.033 | 0.032 | 0.352 | 0.026 | 0.095 | 0.231 | 0.137 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 44 | 43 | 90.5 |
| Email Header | 600x200 | 42 | 41 | 87.7 |
| Facebook Cover | 820x312 | 46 | 46 | 87.8 |
| Facebook Post | 1200x630 | 32 | 31 | 91.8 |
| Instagram Portrait | 1080x1350 | 42 | 42 | 91.6 |
| Instagram Post | 1080x1080 | 35 | 35 | 89.4 |
| Instagram Story | 1080x1920 | 41 | 41 | 90.4 |
| Leaderboard | 728x90 | 36 | 34 | 83.9 |
| LinkedIn Banner | 1584x396 | 47 | 47 | 86.9 |
| Medium Rectangle | 300x250 | 38 | 38 | 89.0 |
| Pinterest Pin | 1000x1500 | 35 | 34 | 88.1 |
| Presentation 16:9 | 1920x1080 | 39 | 39 | 88.1 |
| Wide Skyscraper | 160x600 | 32 | 30 | 87.3 |
| X Post | 1600x900 | 47 | 47 | 89.5 |
| YouTube Thumbnail | 1280x720 | 44 | 44 | 89.5 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5952967595a7a863ddce0220__wide_skyscraper | 79.2 | hidden_element:svg1 |
| crello_59b266771350e8329300d02b__a4_poster__150_dpi | 85.8 | hidden_element:svg12;hidden_element:svg13 |
| crello_59b266771350e8329300d02b__pinterest_pin | 86.0 | hidden_element:svg12;hidden_element:svg13 |
| crello_5dc3c996abc8ea6d1cbcc226__leaderboard | 86.5 | hidden_element:svg1 |
| crello_59b266771350e8329300d02b__facebook_post | 87.0 | hidden_element:svg12;hidden_element:svg13 |
| crello_5b756cf71cc8aa5429ba8033__leaderboard | 89.3 | hidden_element:svg7;hidden_element:svg10 |
| crello_5ac4a8ce4b568b8eece2fd9b__wide_skyscraper | 94.6 | hidden_element:svg3;hidden_element:svg4 |
| crello_5fabaa59a637ee11e3a88e87__email_header | 98.5 | hidden_element:svg1 |
| crello_5e563cae1cc98b350a78b20a__leaderboard | 48.4 |  |
| crello_5ef32868499b85dcc76e66fc__email_header | 50.4 |  |
| crello_5e4facf31cc98b350aeffeeb__linkedin_banner | 51.3 |  |
| crello_5e4facf31cc98b350aeffeeb__facebook_cover | 56.4 |  |
| crello_5db1a542abc8ea6d1cd835af__leaderboard | 60.1 |  |
| crello_5ab9076df07aee69770e9039__leaderboard | 61.3 |  |
| crello_5ef32868499b85dcc76e66fc__linkedin_banner | 61.5 |  |
| crello_5db1a542abc8ea6d1cd835af__wide_skyscraper | 63.9 |  |
| crello_5d691f00abc8ea6d1c396bbf__presentation_16_9 | 65.4 |  |
| crello_5d08e5d48cba87f943d052da__instagram_story | 67.2 |  |
| crello_58a4155595a7a863ddcc6dd1__linkedin_banner | 67.8 |  |
| crello_5c8fb5a885ea3c16f94b98c1__wide_skyscraper | 68.0 |  |
| crello_5d691f00abc8ea6d1c396bbf__facebook_cover | 68.6 |  |
| crello_5ef30e1a499b85dcc739d4b0__pinterest_pin | 69.2 |  |
| crello_5f3bbac8a637ee11e3a8e3aa__email_header | 69.2 |  |
| crello_5d691f00abc8ea6d1c396bbf__instagram_story | 69.3 |  |
| crello_5f5b3068a637ee11e383ae07__email_header | 69.6 |  |
| crello_5d9cad46abc8ea6d1c234bd4__x_post | 69.7 |  |
| crello_5eb9a87e499b85dcc709b1a3__youtube_thumbnail | 69.9 |  |
| crello_5889bb0195a7a863ddcc394f__pinterest_pin | 69.9 |  |
| crello_5d9cad46abc8ea6d1c234bd4__presentation_16_9 | 70.1 |  |
| crello_5889bb0195a7a863ddcc394f__a4_poster__150_dpi | 70.2 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 7536 ms, median 6559 ms, p95 15512 ms, max 21784 ms
- check: mean 4 ms, median 3 ms, p95 10 ms, max 28 ms
- score: mean 7 ms, median 5 ms, p95 19 ms, max 68 ms
- render: n/a
