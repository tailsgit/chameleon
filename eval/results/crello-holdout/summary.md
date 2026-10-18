# Benchmark summary: crello-holdout

Engine commit `v1-submittable-dirty`, 300 cases (100 designs), render=no, contrast=no, jobs=8.

- **Cases passing every hard rule: 295/300** (98.3%)
- **Average score: 90.88** / 100
- Crashes (resize raised): 0
- Engine fell back to a plain uniform scale: 0 cases
- Cases where some layout candidate raised (others used): 0

## Violations by rule

| rule | violations | cases |
|---|---|---|
| hidden_element | 12 | 5 |

## Average penalty (0 = perfect, 1 = worst)

| overlap | holders | small_text | headline | scale | space | balance | floating | emphasis | siblings | alignment | reading_order |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.187 | 0.034 | 0.063 | 0.021 | 0.165 | 0.018 | 0.022 | 0.379 | 0.018 | 0.053 | 0.218 | 0.139 |

## By target format

| target | size | cases | passed | mean score |
|---|---|---|---|---|
| A4 Poster (150 dpi) | 1240x1754 | 24 | 24 | 91.5 |
| Email Header | 600x200 | 18 | 18 | 89.9 |
| Facebook Cover | 820x312 | 28 | 28 | 91.5 |
| Facebook Post | 1200x630 | 17 | 17 | 90.5 |
| Instagram Portrait | 1080x1350 | 20 | 20 | 91.8 |
| Instagram Post | 1080x1080 | 17 | 17 | 90.8 |
| Instagram Story | 1080x1920 | 20 | 20 | 90.6 |
| Leaderboard | 728x90 | 20 | 20 | 88.4 |
| LinkedIn Banner | 1584x396 | 16 | 16 | 91.2 |
| Medium Rectangle | 300x250 | 18 | 16 | 89.3 |
| Pinterest Pin | 1000x1500 | 19 | 19 | 89.5 |
| Presentation 16:9 | 1920x1080 | 18 | 18 | 92.2 |
| Wide Skyscraper | 160x600 | 23 | 20 | 90.2 |
| X Post | 1600x900 | 23 | 23 | 93.4 |
| YouTube Thumbnail | 1280x720 | 19 | 19 | 91.7 |

## 30 worst cases (failures first)

| case | score | violations |
|---|---|---|
| crello_5dee3d5b9fea0cc374173de6__wide_skyscraper | 83.7 | hidden_element:svg10;hidden_element:svg14 |
| crello_590af4b195a7a863ddcd68ac__wide_skyscraper | 88.4 | hidden_element:svg3;hidden_element:svg4 |
| crello_59b26bab1350e8329300d51a__medium_rectangle | 89.0 | hidden_element:svg1;hidden_element:svg2 |
| crello_58a1e88995a7a863ddcc657e__wide_skyscraper | 91.8 | hidden_element:svg7;hidden_element:svg8;hidden_element:svg9;hidden_element:svg11 |
| crello_5dee3d5b9fea0cc374173de6__medium_rectangle | 93.8 | hidden_element:svg10;hidden_element:svg14 |
| crello_588a0fc195a7a863ddcc4509__wide_skyscraper | 77.0 |  |
| crello_5f041ec0499b85dcc7b152b6__leaderboard | 78.3 |  |
| crello_5ef30fa9499b85dcc73cb20e__pinterest_pin | 78.8 |  |
| crello_5ddd35239fea0cc374ef3ebf__instagram_story | 79.1 |  |
| crello_5f041ec0499b85dcc7b152b6__email_header | 79.7 |  |
| crello_5dcbd0779fea0cc374098ede__email_header | 80.4 |  |
| crello_5ddd35239fea0cc374ef3ebf__instagram_portrait | 81.0 |  |
| crello_5f4ce0dea637ee11e3dd5cfa__facebook_cover | 81.8 |  |
| crello_59528ca795a7a863ddcdfa21__leaderboard | 81.8 |  |
| crello_5e7c749c4b3890eb07230de5__email_header | 82.1 |  |
| crello_5f154115499b85dcc75cb87d__linkedin_banner | 82.2 |  |
| crello_5f154115499b85dcc75cb87d__instagram_story | 82.8 |  |
| crello_58ab127e95a7a863ddcc75f7__instagram_portrait | 82.8 |  |
| crello_5f041ec0499b85dcc7b152b6__pinterest_pin | 82.9 |  |
| crello_5f4ce0dea637ee11e3dd5cfa__email_header | 82.9 |  |
| crello_5db2b83aabc8ea6d1c443e7b__instagram_post | 83.1 |  |
| crello_5c0a89da133a785392a7f992__medium_rectangle | 83.2 |  |
| crello_5f34db3ea637ee11e32b7aac__instagram_portrait | 83.3 |  |
| crello_5928035b95a7a863ddcd8ff7__facebook_post | 83.7 |  |
| crello_5c0a89da133a785392a7f992__leaderboard | 83.7 |  |
| crello_5f34db3ea637ee11e32b7aac__presentation_16_9 | 83.7 |  |
| crello_588a0fc195a7a863ddcc4509__a4_poster__150_dpi | 83.8 |  |
| crello_5e7c749c4b3890eb07230de5__facebook_post | 84.1 |  |
| crello_58ab127e95a7a863ddcc75f7__instagram_story | 84.2 |  |
| crello_5dee48ad9fea0cc374371a03__leaderboard | 84.2 |  |

## Timings (per case, this machine, 8 worker processes in parallel)

- resize: mean 6848 ms, median 5505 ms, p95 15769 ms, max 58294 ms
- check: mean 4 ms, median 3 ms, p95 10 ms, max 33 ms
- score: mean 7 ms, median 5 ms, p95 17 ms, max 69 ms
- render: n/a
