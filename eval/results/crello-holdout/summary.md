# Benchmark summary: crello-holdout

Engine commit `v3-12-g49abc60-dirty`, 300 cases (100 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 295/300** (98.3%)
- **Average score: 90.45** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 12 | 5 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | share_drift | space | balance | floating | emphasis | siblings | alignment | reading_order | legibility | coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.261 | 0.037 | 0.060 | 0.049 | 0.142 | 0.202 | 0.042 | 0.413 | 0.146 | 0.024 | 0.041 | 0.380 | 0.028 | 0.056 | 0.225 | 0.127 | 0.022 | 0.053 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 24 | 24 | 91.5 |
| Email Header | 600x200 | 18 | 18 | 88.8 |
| Facebook Cover | 820x312 | 28 | 28 | 90.7 |
| Facebook Post | 1200x630 | 17 | 17 | 88.0 |
| Instagram Portrait | 1080x1350 | 20 | 20 | 90.7 |
| Instagram Post | 1080x1080 | 17 | 17 | 90.1 |
| Instagram Story | 1080x1920 | 20 | 20 | 90.4 |
| Leaderboard | 728x90 | 20 | 20 | 88.5 |
| LinkedIn Banner | 1584x396 | 16 | 16 | 91.5 |
| Medium Rectangle | 300x250 | 18 | 16 | 90.0 |
| Pinterest Pin | 1000x1500 | 19 | 19 | 92.8 |
| Presentation 16:9 | 1920x1080 | 18 | 18 | 90.0 |
| Wide Skyscraper | 160x600 | 23 | 20 | 88.8 |
| X Post | 1600x900 | 23 | 23 | 92.1 |
| YouTube Thumbnail | 1280x720 | 19 | 19 | 92.3 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5dee3d5b9fea0cc374173de6__wide_skyscraper | 81.7 | hidden_element:svg10;hidden_element:svg14 |
| crello_58a1e88995a7a863ddcc657e__wide_skyscraper | 85.7 | hidden_element:svg7;hidden_element:svg8;hidden_element:svg9;hidden_element:svg11 |
| crello_590af4b195a7a863ddcd68ac__wide_skyscraper | 92.0 | hidden_element:svg3;hidden_element:svg4 |
| crello_59b26bab1350e8329300d51a__medium_rectangle | 92.3 | hidden_element:svg1;hidden_element:svg2 |
| crello_5dee3d5b9fea0cc374173de6__medium_rectangle | 95.5 | hidden_element:svg10;hidden_element:svg14 |
| crello_5f3b7921a637ee11e3188a19__facebook_cover | 68.4 |  |
| crello_5888cfbb95a7a863ddcc262c__youtube_thumbnail | 69.3 |  |
| crello_5888cfbb95a7a863ddcc262c__x_post | 69.4 |  |
| crello_5888cfbb95a7a863ddcc262c__presentation_16_9 | 69.9 |  |
| crello_5dee48ad9fea0cc374371a03__leaderboard | 70.2 |  |
| crello_5f4ce0dea637ee11e3dd5cfa__a4_poster__150_dpi | 71.3 |  |
| crello_5dcbd0779fea0cc374098ede__email_header | 71.5 |  |
| crello_5f3b7921a637ee11e3188a19__instagram_portrait | 71.7 |  |
| crello_5e6f7df04b3890eb0723ad45__facebook_cover | 71.8 |  |
| crello_5f3b7921a637ee11e3188a19__facebook_post | 73.2 |  |
| crello_588a0fc195a7a863ddcc4509__wide_skyscraper | 73.3 |  |
| crello_5ddd35239fea0cc374ef3ebf__instagram_story | 74.2 |  |
| crello_5c6c325085ea3c16f9256af7__leaderboard | 74.6 |  |
| crello_5ddd35239fea0cc374ef3ebf__instagram_portrait | 75.3 |  |
| crello_58ab127e95a7a863ddcc75f7__leaderboard | 75.3 |  |
| crello_5e7c749c4b3890eb07230de5__email_header | 75.9 |  |
| crello_5b9ba84f18654940f73161c4__facebook_post | 76.3 |  |
| crello_5dee48ad9fea0cc374371a03__instagram_portrait | 76.5 |  |
| crello_5c6c325085ea3c16f9256af7__wide_skyscraper | 77.0 |  |
| crello_5c6c325085ea3c16f9256af7__pinterest_pin | 77.4 |  |
| crello_5b7150101cc8aa542916e2bd__wide_skyscraper | 77.4 |  |
| crello_5c0a89da133a785392a7f992__medium_rectangle | 78.3 |  |
| crello_5dee48ad9fea0cc374371a03__facebook_cover | 78.3 |  |
| crello_59528ca795a7a863ddcdfa21__leaderboard | 78.4 |  |
| crello_5eb180ed499b85dcc75848d8__medium_rectangle | 78.5 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 6705 ms, median 6349 ms, p95 12588 ms, max 15404 ms
- check: mean 4 ms, median 3 ms, p95 8 ms, max 17 ms
- score: mean 6 ms, median 5 ms, p95 15 ms, max 34 ms
- render: n/a
