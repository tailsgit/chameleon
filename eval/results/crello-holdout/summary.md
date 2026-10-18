# Benchmark summary: crello-holdout

Engine commit `v1-submittable-1-gf0338a2-dirty`, 300 cases (100 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 295/300** (98.3%)
- **Average score: 89.90** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 12 | 5 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | key_size | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.290 | 0.048 | 0.059 | 0.028 | 0.106 | 0.128 | 0.016 | 0.031 | 0.423 | 0.025 | 0.056 | 0.217 | 0.153 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 24 | 24 | 91.7 |
| Email Header | 600x200 | 18 | 18 | 85.9 |
| Facebook Cover | 820x312 | 28 | 28 | 90.6 |
| Facebook Post | 1200x630 | 17 | 17 | 90.2 |
| Instagram Portrait | 1080x1350 | 20 | 20 | 90.6 |
| Instagram Post | 1080x1080 | 17 | 17 | 91.2 |
| Instagram Story | 1080x1920 | 20 | 20 | 89.4 |
| Leaderboard | 728x90 | 20 | 20 | 86.5 |
| LinkedIn Banner | 1584x396 | 16 | 16 | 90.3 |
| Medium Rectangle | 300x250 | 18 | 16 | 89.4 |
| Pinterest Pin | 1000x1500 | 19 | 19 | 91.0 |
| Presentation 16:9 | 1920x1080 | 18 | 18 | 91.9 |
| Wide Skyscraper | 160x600 | 23 | 20 | 85.3 |
| X Post | 1600x900 | 23 | 23 | 92.2 |
| YouTube Thumbnail | 1280x720 | 19 | 19 | 92.1 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5dee3d5b9fea0cc374173de6__wide_skyscraper | 70.4 | hidden_element:svg10;hidden_element:svg14 |
| crello_58a1e88995a7a863ddcc657e__wide_skyscraper | 77.4 | hidden_element:svg7;hidden_element:svg8;hidden_element:svg9;hidden_element:svg11 |
| crello_590af4b195a7a863ddcd68ac__wide_skyscraper | 88.8 | hidden_element:svg3;hidden_element:svg4 |
| crello_59b26bab1350e8329300d51a__medium_rectangle | 90.5 | hidden_element:svg1;hidden_element:svg2 |
| crello_5dee3d5b9fea0cc374173de6__medium_rectangle | 92.2 | hidden_element:svg10;hidden_element:svg14 |
| crello_5e7c749c4b3890eb07230de5__email_header | 58.7 |  |
| crello_588a0fc195a7a863ddcc4509__wide_skyscraper | 61.6 |  |
| crello_5dcbd0779fea0cc374098ede__email_header | 66.2 |  |
| crello_5c0a89da133a785392a7f992__leaderboard | 68.1 |  |
| crello_59528ca795a7a863ddcdfa21__leaderboard | 68.3 |  |
| crello_5e7c749c4b3890eb07230de5__facebook_post | 71.3 |  |
| crello_5c6c325085ea3c16f9256af7__leaderboard | 72.0 |  |
| crello_5ef30fa9499b85dcc73cb20e__linkedin_banner | 72.3 |  |
| crello_5f5f3fdfa637ee11e3358fbe__instagram_story | 72.8 |  |
| crello_5dee48ad9fea0cc374371a03__leaderboard | 73.5 |  |
| crello_5930148c95a7a863ddcdc199__email_header | 74.2 |  |
| crello_5f48b46da637ee11e3373119__wide_skyscraper | 74.5 |  |
| crello_58898c8a95a7a863ddcc3102__wide_skyscraper | 74.6 |  |
| crello_5930129195a7a863ddcdc014__wide_skyscraper | 75.1 |  |
| crello_5928047f95a7a863ddcd90c7__email_header | 75.7 |  |
| crello_5936854d95a7a863ddcdd0e5__instagram_story | 75.8 |  |
| crello_5953611d95a7a863ddce13e0__linkedin_banner | 75.9 |  |
| crello_5953611d95a7a863ddce13e0__email_header | 75.9 |  |
| crello_5930129195a7a863ddcdc014__facebook_cover | 76.0 |  |
| crello_5f46326aa637ee11e3c88605__medium_rectangle | 76.7 |  |
| crello_5f48b46da637ee11e3373119__email_header | 77.1 |  |
| crello_5eb180ed499b85dcc75848d8__medium_rectangle | 78.1 |  |
| crello_58a1e88995a7a863ddcc657e__youtube_thumbnail | 78.6 |  |
| crello_5f5f3fdfa637ee11e3358fbe__x_post | 78.9 |  |
| crello_5f48b46da637ee11e3373119__linkedin_banner | 79.6 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 7498 ms, median 6931 ms, p95 15454 ms, max 22750 ms
- check: mean 5 ms, median 4 ms, p95 11 ms, max 22 ms
- score: mean 7 ms, median 5 ms, p95 20 ms, max 38 ms
- render: n/a
