# Benchmark summary: crello-dev

Engine commit `v5-2-g5f57327-dirty`, 600 cases (200 designs), render=no, contrast=no, jobs=4.

- **Cases passing every hard rule: 598/600** (99.7%)
- **Average score: 89.41** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 2 | 2 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | text_over_image | relationships | groups | related_order | fill | share_drift | space | balance | floating | emphasis | siblings | alignment | reading_order | legibility | coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.218 | 0.023 | 0.055 | 0.062 | 0.154 | 0.211 | 0.041 | 0.257 | 0.205 | 0.006 | 0.007 | 0.141 | 0.031 | 0.034 | 0.340 | 0.039 | 0.078 | 0.218 | 0.118 | 0.016 | 0.165 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 44 | 44 | 92.0 |
| Email Header | 600x200 | 42 | 41 | 87.9 |
| Facebook Cover | 820x312 | 46 | 46 | 89.0 |
| Facebook Post | 1200x630 | 32 | 32 | 91.8 |
| Instagram Portrait | 1080x1350 | 42 | 42 | 90.9 |
| Instagram Post | 1080x1080 | 35 | 35 | 88.4 |
| Instagram Story | 1080x1920 | 41 | 41 | 92.4 |
| Leaderboard | 728x90 | 36 | 36 | 85.3 |
| LinkedIn Banner | 1584x396 | 47 | 47 | 87.0 |
| Medium Rectangle | 300x250 | 38 | 38 | 88.4 |
| Pinterest Pin | 1000x1500 | 35 | 35 | 91.9 |
| Presentation 16:9 | 1920x1080 | 39 | 39 | 88.5 |
| Wide Skyscraper | 160x600 | 32 | 31 | 86.7 |
| X Post | 1600x900 | 47 | 47 | 89.9 |
| YouTube Thumbnail | 1280x720 | 44 | 44 | 90.6 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5fabaa59a637ee11e3a88e87__email_header | 94.6 | hidden_element:svg1 |
| crello_5952967595a7a863ddce0220__wide_skyscraper | 95.1 | hidden_element:svg1 |
| crello_5bdc41119259f9ba5416c94c__instagram_post | 57.8 |  |
| crello_5f5b3068a637ee11e383ae07__email_header | 58.2 |  |
| crello_58b0124395a7a863ddcc91fa__linkedin_banner | 59.0 |  |
| crello_5db1a542abc8ea6d1cd835af__leaderboard | 60.8 |  |
| crello_5db1a542abc8ea6d1cd835af__wide_skyscraper | 63.8 |  |
| crello_5d371dae8cba87f943a63b67__leaderboard | 66.2 |  |
| crello_5888da2995a7a863ddcc2bc6__a4_poster__150_dpi | 66.3 |  |
| crello_5e7494a24b3890eb07a8b3da__email_header | 66.7 |  |
| crello_5889bb0195a7a863ddcc394f__email_header | 67.4 |  |
| crello_5889bb0195a7a863ddcc394f__a4_poster__150_dpi | 67.5 |  |
| crello_5947b6c395a7a863ddcdd9f0__instagram_post | 67.7 |  |
| crello_58898cb195a7a863ddcc3121__leaderboard | 68.0 |  |
| crello_5ef32868499b85dcc76e66fc__email_header | 68.4 |  |
| crello_5eec6cc3499b85dcc79f7b05__instagram_portrait | 68.5 |  |
| crello_5ef30e1a499b85dcc739d4b0__facebook_cover | 69.2 |  |
| crello_5e4facf31cc98b350aeffeeb__facebook_cover | 69.2 |  |
| crello_5eb53150499b85dcc702ff38__presentation_16_9 | 69.3 |  |
| crello_58b0124395a7a863ddcc91fa__email_header | 69.4 |  |
| crello_5eb9a87e499b85dcc709b1a3__youtube_thumbnail | 69.5 |  |
| crello_5c8fb5a885ea3c16f94b98c1__wide_skyscraper | 70.0 |  |
| crello_5952a15795a7a863ddce0a02__linkedin_banner | 70.0 |  |
| crello_5947b6c395a7a863ddcdd9f0__x_post | 70.4 |  |
| crello_5eb9a87e499b85dcc709b1a3__linkedin_banner | 70.5 |  |
| crello_5eb9695d499b85dcc73667f2__instagram_post | 71.1 |  |
| crello_5889bb0195a7a863ddcc394f__pinterest_pin | 71.3 |  |
| crello_5f05bdae499b85dcc767e8b7__email_header | 71.4 |  |
| crello_5ab9076df07aee69770e9039__leaderboard | 71.4 |  |
| crello_5e563cae1cc98b350a78b20a__leaderboard | 71.6 |  |

## Timings (per case, this machine, 4 worker processes in parallel)

- resize: mean 6326 ms, median 6073 ms, p95 11946 ms, max 15605 ms
- check: mean 2 ms, median 2 ms, p95 5 ms, max 11 ms
- score: mean 5 ms, median 4 ms, p95 14 ms, max 33 ms
- render: n/a
