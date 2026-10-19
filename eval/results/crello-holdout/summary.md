# Benchmark summary: crello-holdout

Engine commit `v4-5-g6a0f590-dirty`, 300 cases (100 designs), render=no, contrast=no, jobs=4.

- **Cases passing every hard rule: 300/300** (100.0%)
- **Average score: 91.19** / 100
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
| 0.279 | 0.040 | 0.045 | 0.042 | 0.142 | 0.184 | 0.031 | 0.415 | 0.139 | 0.024 | 0.039 | 0.371 | 0.043 | 0.058 | 0.221 | 0.126 | 0.010 | 0.035 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 24 | 24 | 93.9 |
| Email Header | 600x200 | 18 | 18 | 89.3 |
| Facebook Cover | 820x312 | 28 | 28 | 91.7 |
| Facebook Post | 1200x630 | 17 | 17 | 89.5 |
| Instagram Portrait | 1080x1350 | 20 | 20 | 89.7 |
| Instagram Post | 1080x1080 | 17 | 17 | 90.0 |
| Instagram Story | 1080x1920 | 20 | 20 | 92.1 |
| Leaderboard | 728x90 | 20 | 20 | 88.0 |
| LinkedIn Banner | 1584x396 | 16 | 16 | 93.8 |
| Medium Rectangle | 300x250 | 18 | 18 | 90.9 |
| Pinterest Pin | 1000x1500 | 19 | 19 | 93.4 |
| Presentation 16:9 | 1920x1080 | 18 | 18 | 90.3 |
| Wide Skyscraper | 160x600 | 23 | 23 | 89.6 |
| X Post | 1600x900 | 23 | 23 | 92.4 |
| YouTube Thumbnail | 1280x720 | 19 | 19 | 92.7 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5dee48ad9fea0cc374371a03__leaderboard | 67.8 |  |
| crello_5dee48ad9fea0cc374371a03__instagram_portrait | 70.0 |  |
| crello_5dcbd0779fea0cc374098ede__email_header | 71.6 |  |
| crello_588a0fc195a7a863ddcc4509__wide_skyscraper | 71.8 |  |
| crello_58ab127e95a7a863ddcc75f7__leaderboard | 71.9 |  |
| crello_5e6f7df04b3890eb0723ad45__facebook_cover | 72.0 |  |
| crello_5f3b7921a637ee11e3188a19__instagram_portrait | 72.2 |  |
| crello_5888cfbb95a7a863ddcc262c__x_post | 72.3 |  |
| crello_5e7c749c4b3890eb07230de5__email_header | 74.9 |  |
| crello_58898c8a95a7a863ddcc3102__instagram_post | 76.0 |  |
| crello_5888cfbb95a7a863ddcc262c__youtube_thumbnail | 76.3 |  |
| crello_5888cfbb95a7a863ddcc262c__presentation_16_9 | 76.5 |  |
| crello_5eb180ed499b85dcc75848d8__facebook_post | 76.6 |  |
| crello_5ef30fa9499b85dcc73cb20e__presentation_16_9 | 76.8 |  |
| crello_5ddd35239fea0cc374ef3ebf__instagram_portrait | 76.9 |  |
| crello_5f4ce0dea637ee11e3dd5cfa__email_header | 78.0 |  |
| crello_5c0a89da133a785392a7f992__medium_rectangle | 78.3 |  |
| crello_59528ca795a7a863ddcdfa21__leaderboard | 78.4 |  |
| crello_5b7150101cc8aa542916e2bd__wide_skyscraper | 78.5 |  |
| crello_5dee48ad9fea0cc374371a03__facebook_cover | 79.0 |  |
| crello_5e7c749c4b3890eb07230de5__facebook_post | 79.1 |  |
| crello_5ab908b7f07aee6977117cfe__leaderboard | 79.4 |  |
| crello_5f4ce0dea637ee11e3dd5cfa__facebook_cover | 79.5 |  |
| crello_5c6c325085ea3c16f9256af7__leaderboard | 79.5 |  |
| crello_5f5f3fdfa637ee11e3358fbe__facebook_cover | 79.8 |  |
| crello_5888d8c095a7a863ddcc2a06__presentation_16_9 | 80.2 |  |
| crello_5888d8c095a7a863ddcc2a06__x_post | 80.5 |  |
| crello_5aa91c86f07aee6977472083__instagram_post | 80.6 |  |
| crello_588a0fc195a7a863ddcc4509__instagram_post | 80.8 |  |
| crello_5f3b7921a637ee11e3188a19__facebook_post | 81.0 |  |

## Timings (per case, this machine, 4 worker processes in parallel)

- resize: mean 5805 ms, median 5431 ms, p95 11259 ms, max 13980 ms
- check: mean 3 ms, median 2 ms, p95 6 ms, max 13 ms
- score: mean 6 ms, median 4 ms, p95 16 ms, max 38 ms
- render: n/a
