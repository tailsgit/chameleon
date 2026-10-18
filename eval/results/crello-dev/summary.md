# Benchmark summary: crello-dev

Engine commit `8cc9f28-dirty`, 600 cases (200 designs), render=yes, contrast=no, jobs=8.

- **Cases passing every hard rule: 594/600** (99.0%)
- **Average score: 90.13** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| background_not_full_canvas | 6 | 6 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | small_text | headline | scale | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.098 | 0.019 | 0.059 | 0.250 | 0.017 | 0.024 | 0.397 | 0.013 | 0.053 | 0.161 | 0.107 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 44 | 43 | 89.7 |
| Email Header | 600x200 | 42 | 42 | 88.2 |
| Facebook Cover | 820x312 | 46 | 45 | 89.7 |
| Facebook Post | 1200x630 | 32 | 32 | 92.0 |
| Instagram Portrait | 1080x1350 | 42 | 42 | 90.1 |
| Instagram Post | 1080x1080 | 35 | 35 | 89.5 |
| Instagram Story | 1080x1920 | 41 | 41 | 90.2 |
| Leaderboard | 728x90 | 36 | 36 | 90.3 |
| LinkedIn Banner | 1584x396 | 47 | 47 | 89.5 |
| Medium Rectangle | 300x250 | 38 | 37 | 89.5 |
| Pinterest Pin | 1000x1500 | 35 | 35 | 91.5 |
| Presentation 16:9 | 1920x1080 | 39 | 39 | 90.6 |
| Wide Skyscraper | 160x600 | 32 | 31 | 89.7 |
| X Post | 1600x900 | 47 | 47 | 91.8 |
| YouTube Thumbnail | 1280x720 | 44 | 42 | 90.1 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5d08ef5d8cba87f943e4586b__youtube_thumbnail | 93.8 | background_not_full_canvas:image0 |
| crello_5d08ef5d8cba87f943e4586b__medium_rectangle | 94.7 | background_not_full_canvas:image0 |
| crello_5d08ef5d8cba87f943e4586b__wide_skyscraper | 95.6 | background_not_full_canvas:image0 |
| crello_591421ae95a7a863ddcd760d__facebook_cover | 96.2 | background_not_full_canvas:image0 |
| crello_591421ae95a7a863ddcd760d__youtube_thumbnail | 98.0 | background_not_full_canvas:image0 |
| crello_591421ae95a7a863ddcd760d__a4_poster__150_dpi | 99.1 | background_not_full_canvas:image0 |
| crello_5df213199fea0cc374af016c__linkedin_banner | 70.6 |  |
| crello_5c8fb5a885ea3c16f94b98c1__wide_skyscraper | 71.0 |  |
| crello_5f916f8ea637ee11e3169da4__linkedin_banner | 72.9 |  |
| crello_5f5b3068a637ee11e383ae07__a4_poster__150_dpi | 73.0 |  |
| crello_5c8fb5a885ea3c16f94b98c1__instagram_story | 73.0 |  |
| crello_5f916f8ea637ee11e3169da4__instagram_portrait | 73.2 |  |
| crello_5f3bbac8a637ee11e3a8e3aa__email_header | 73.6 |  |
| crello_5888da2995a7a863ddcc2bc6__a4_poster__150_dpi | 74.3 |  |
| crello_5dadaa37abc8ea6d1cf0a669__facebook_cover | 74.4 |  |
| crello_58a4155595a7a863ddcc6dd1__linkedin_banner | 74.7 |  |
| crello_5f916f8ea637ee11e3169da4__medium_rectangle | 75.6 |  |
| crello_5888da2995a7a863ddcc2bc6__email_header | 75.8 |  |
| crello_5888da2995a7a863ddcc2bc6__instagram_story | 76.0 |  |
| crello_5a82c4a6f07aee6977be6291__medium_rectangle | 76.0 |  |
| crello_5f9171f7a637ee11e324ed2d__presentation_16_9 | 76.9 |  |
| crello_5c41e650048d064dbc96a71c__youtube_thumbnail | 77.0 |  |
| crello_5f5b3068a637ee11e383ae07__instagram_post | 77.0 |  |
| crello_5f9171f7a637ee11e324ed2d__youtube_thumbnail | 77.4 |  |
| crello_5f918f97a637ee11e3b0f5ab__facebook_cover | 77.7 |  |
| crello_59158aa295a7a863ddcd85c8__email_header | 78.2 |  |
| crello_5eec6cc3499b85dcc79f7b05__linkedin_banner | 78.3 |  |
| crello_5c8fb5a885ea3c16f94b98c1__facebook_cover | 78.6 |  |
| crello_59b266771350e8329300d02b__pinterest_pin | 78.6 |  |
| crello_5f9171f7a637ee11e324ed2d__pinterest_pin | 79.0 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 3813 ms, median 2910 ms, p95 10361 ms, max 18281 ms
- check: mean 4 ms, median 3 ms, p95 9 ms, max 17 ms
- score: mean 5 ms, median 4 ms, p95 15 ms, max 31 ms
- render: mean 296 ms, median 179 ms, p95 987 ms, max 1887 ms
