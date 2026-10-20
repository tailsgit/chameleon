# HANDOFF: training the layout critic

This file is for whoever trains the critic, person or AI assistant. It assumes you have this repo and none of
the conversations that produced it. Everything below was run end to end on a small sample on 2026-10-19
(branch `critic`). Full-scale data generation and training have **not** been run.

## 1. What this is

Chameleon resizes a design (Chameleon JSON v0.9) to a new canvas size. The engine (`engine/`) analyses
the source, generates layout candidates (recipes, retrieved layouts, preserve layouts, finishing variants)
and picks one with a hand-written scorer (`eval/score.py`) plus hard rules (`eval/check.py`).

The new direction is a **trained critic plus search**:
- **Critic:** a small transformer reads a laid-out design and returns one score (higher = better).
- **Search:** a hill climber (`engine/search.py`) nudges the chosen layout and keeps a move only when the
  critic's score improves and every hard rule still holds.
- **Switch:** both are off unless `CHAMELEON_CRITIC=1`. With no trained model installed, the critic falls
  back to the hand scorer.

**Your job:** generate the full training data, train the critic, beat the bar in section 7, export it to
ONNX, publish the weights, and turn it on.

**Fallback:** git tag `submission-fallback` (= v4) is the frozen submission. Its no-cache Docker build ran
all 45 organiser samples offline OK (slowest case 12.95 s). If the critic work goes nowhere, ship that tag.

## 2. Rules you must keep

- **No network at run time.** Scoring runs `docker run --network none`. The ONNX model is downloaded at
  Docker BUILD time (`--build-arg CRITIC_URL=...`, see section 8) or copied into `engine/data/critic.onnx`
  before building. Never fetch anything inside `resize()`.
- **Weights must be public.** The organisers' rule (RULES.md, "Models and fine-tuning") requires any
  trained weights to sit somewhere judges can pull them, e.g. a public Hugging Face model repo. Publish
  `critic.onnx`, its config and a model card there.
- **Crello data is never committed.**
  - Crello's licence is CDLA-Permissive-2.0 plus the VistaCreate licence agreement (details in NOTES.md
    §8). Training on it is fine; shipping its designs, texts or image crops is not.
  - Converted designs, assets, training shards, renders, checkpoints, review pages and label files all
    stay outside git: `../data/`, gitignored folders, or `/Volumes/Extreme/AdobeHackathon/tmp`.
  - `.gitignore` already covers `engine/data/critic.onnx`, `*.pt` and the Crello result folders. Commit
    only code, configs and docs.
- **Hand labels are evaluation only.** `critic/make_data.py` drops every design that appears in any
  `eval/results/**/labels.json` and every dev/holdout design (`eval/crello_testset.json`). Never train,
  tune or early-stop on the labels. `critic/eval.py` asserts that no labelled design is in the training
  index.
- **The engine contract.**
  - `resize()` must always return a valid output within the time budget. The brief allows 15 s; we aim for
    under 13.5 s in Docker.
  - The search stops 12.5 s after the start (`SEARCH_END_S` in `engine/resize.py`).
  - Never alter image pixels: no outpainting, blurring or duplicated elements.
- **Keep the hand scorer's numbers honest.** With no model, the search optimises the same hand scorer the
  benchmark measures with. Its hand-score "gains" are therefore not evidence (see section 10).

## 3. Files

| File | What it does |
|---|---|
| `critic/features.py` | Design to model input: one token per element plus a global token, padded to 41 (section 5). No torch; the engine imports it. |
| `critic/damage.py` | The 8 damage functions that make negatives, plus naive stretch. Its geometry helpers (`box`, `move`, `scale`, `clamp`) are reused by the search. |
| `critic/make_data.py` | Builds ranking groups from Crello training designs; writes shards and a review page (section 4). |
| `critic/model.py` | Small transformer, 1.84M parameters with `layout_small.yaml`. |
| `critic/configs/layout_small.yaml` | Model sizes and training hyperparameters. |
| `critic/train.py` | Pairwise ranking training: MPS or CPU, fixed seed, checkpoints, `log.csv`, `--smoke`. |
| `critic/eval.py` | Agreement with the hand labels, side by side with the hand scorer; disagreement review page. |
| `critic/export.py` | Checkpoint to ONNX, then checks onnxruntime against PyTorch. |
| `engine/critic_score.py` | Loads `engine/data/critic.onnx` (or `$CHAMELEON_CRITIC_MODEL`) with onnxruntime and scores layouts. Falls back to the hand scorer when the model is missing or doesn't match. |
| `engine/search.py` | Hill-climbing search: moves, a hard-rule check after every move, keeps only critic improvements, fixed seed, deadline. |
| `engine/resize.py` | Runs the search after selection when `CHAMELEON_CRITIC=1`. |
| `eval/tests/test_critic.py` | Plumbing tests: features, damages, fallback, search keeps the hard rules. |

**Dependencies:**
- `requirements.txt` (Docker) adds `onnxruntime==1.20.1`.
- `requirements-dev.txt` adds `torch==2.5.1`, `onnx==1.17.0` and `pyyaml`. PyTorch is never in the image.

## 4. Training data (`critic/make_data.py`)

**Source designs:**
- The converted Crello designs are in `$CRELLO_CHAMELEON/designs` (default `../data/crello_chameleon`,
  1,794 designs from Crello's validation split).
- Minus the 300 dev/holdout test designs, and minus every labelled design, that leaves **1,494 training
  designs**. 140 of them are val, chosen by md5(id) % 10 == 0.
- The split is by design, so all of a design's groups land in one split.

**Groups.** Each group is one positive plus its negatives, for a ranking loss. Per design:

| Group | Positive | Negatives |
|---|---|---|
| `original` | The design at its own size. | Each damage of it. |
| `near` | Uniform scale to a random canvas within 5% of the source aspect, 0.6-1.6x the size (`engine.select.fallback`). | Each damage of it. |
| `engine0`, `engine1` | The engine's output for 2 random catalogue sizes (`eval/canvas_catalogue.json`), only when it passes `check()` and scores at least 88 (POS_MIN). | Each damage of it; the naive stretch (only when ln aspect change ≥ 0.15); and up to 3 engine candidates that score at least 8 points lower. |

On the 40-design sample, 50 of the 80 engine groups qualified.

**Kinds**, with indices as stored in the shards (`critic.damage.KINDS`):
- `0 positive`
- `1 bare_canvas`: background shrunk to part of the canvas, or the content shrunk to the middle.
- `2 text_off_panel`: text moved off its flat card. Rare: only 4 of 40 designs have such panels.
- `3 shrunken_hero`: hero image scaled to 35-60%.
- `4 split_group`: one member of a group or sibling row pulled 15-35% away.
- `5 corner_crowding`: all content scaled to 40-60% toward a corner.
- `6 random_overlap`: one unit moved onto another.
- `7 misalignment`: aligned units nudged 2-6% sideways, each independently.
- `8 reading_order`: a first-row unit and a last-row unit swap vertical positions.
- `9 naive_stretch`
- `10 engine_low`

Moved elements are pulled back inside the canvas where they fit. Some damages are subtle (a small nudge),
which is label noise you may want to filter, e.g. by requiring the hand score to drop. Each example's hand
score is stored as `hand`.

**Commands and runtimes** (measured on this Mac, Apple Silicon, 4 workers):

```bash
cd chameleon
export TMPDIR=/Volumes/Extreme/AdobeHackathon/tmp        # keep temp files on the external drive
.venv/bin/python -m critic.make_data --limit 40 --jobs 4 # sample: ~4 min, 136 groups, 8 MB
.venv/bin/python -m critic.make_data --jobs 4            # all 1,494 designs: ~2 h (≈19 s per design per worker), ~300 MB
.venv/bin/python -m critic.make_data --review            # data/critic/review/index.html: 20 examples per kind
python3 -m http.server 8770 --bind 127.0.0.1 -d ../data/critic/review   # then open http://127.0.0.1:8770
```

- The engine runs inside make_data use the CPU-time clock (`CHAMELEON_CPU_CLOCK=1`), so parallel workers
  keep the full engine budget.
- Rerunning make_data deletes the old shards in `train/` and `val/` first.

**Output** (in `$CRITIC_DATA`, default `../data/critic`, outside git):
- `{train,val}/shard_NNNN.npz`:
  - `cont` [M, 41, 36] float16, `cat` [M, 41, 3] int8, `mask` [M, 41] bool;
  - `group` [M] int32, unique within its shard; `kind` [M] int8; `hand` [M] float32; `design` [M] int32.
- `{train,val}/shard_NNNN.jsonl.gz`: per example, the design id, group, kind, hand score, target and the
  full output JSON. Use it to re-render, or to re-featurise if you change `features.py`.
- `index.json`: designs per split, kinds, feature names, counts and settings.

**More data** (optional, about 13x). Crello's train split has 19,479 designs. Download its 31
`train-*.parquet` shards from Hugging Face (`cyberagent/crello`, about 16 GB) into a folder outside the
repo, then:

```bash
CRELLO_DATA=/path/to/crello_train CRELLO_SHARDS='train-*.parquet' CRELLO_CHAMELEON=../data/crello_chameleon_train \
  .venv/bin/python -m eval.crello_convert
CRELLO_CHAMELEON=../data/crello_chameleon_train CRITIC_DATA=../data/critic_train .venv/bin/python -m critic.make_data --jobs 4
```

- These are different designs from the test set, so the dev/holdout exclusion still applies by id.
- Budget about 25 h of make_data at 4 workers, or lower `--targets` to cut the engine runs.
- If you go this way, point `data.dir` in the config at `../data/critic_train`.

## 5. Model input (`critic/features.py`)

- **Tokens:** token 0 is the global token; tokens 1..40 are output elements in stacking order (the 40
  largest, if there are more); the rest is padding (`mask` 0).
- **Analysis:** roles, groups, panels and reading order come from `engine.analyze` of the **source**;
  element ids are shared between source and output.
- **Boxes:** `x, y, width, height`, not rotated bounds.

`cat` (embedded):
- **type:** `pad, global, text, image, shape`.
- **role:** `none, background, decoration, headline, subhead, body, fineprint, cta, hero, logo, badge`.
- **group:** 0 = none or background. 1..40 = the layout unit it belongs to, in reading order, then
  decorations. Group indices are arbitrary labels: only "same group as" matters.

`cont`:

| # | name | meaning |
|---|---|---|
| 0 | `x` | output box left / target width |
| 1 | `y` | output box top / target height |
| 2 | `w` | output box width / target width |
| 3 | `h` | output box height / target height |
| 4 | `src_x` | source box left / source width |
| 5 | `src_y` | source box top / source height |
| 6 | `src_w` | source box width / source width |
| 7 | `src_h` | source box height / source height |
| 8 | `z` | stacking rank in the output, 0 = bottom, 1 = top |
| 9 | `rot_sin` | sin(rotation) |
| 10 | `rot_cos` | cos(rotation) |
| 11 | `r` | colour red 0-1: text colour, shape fill, or an image's alpha-weighted mean pixel |
| 12 | `g` | colour green 0-1 |
| 13 | `b` | colour blue 0-1 |
| 14 | `lum` | relative luminance of that colour (WCAG), 0-1 |
| 15 | `alpha` | colour alpha x element opacity (images: mean pixel alpha x opacity) |
| 16 | `texture` | images: RGB std of the pixels / 128 (photos high, flat cards near 0); else 0 |
| 17 | `font` | text: font size / target height; else 0 |
| 18 | `src_font` | text: source font size / source height; else 0 |
| 19 | `area` | output area / target area |
| 20 | `src_area` | source area / source area of the canvas |
| 21 | `read` | reading rank of its unit in the source (engine.analyze rows), 0-1; 0 when it has none |
| 22 | `has_read` | 1 when the element belongs to a unit in reading order |
| 23 | `contains` | 1 when its output box fully contains another element's box |
| 24 | `inside` | 1 when its output box lies fully inside another element's box |
| 25 | `overlaps` | number of other elements its output box overlaps, / 5, capped at 1 |
| 26 | `on_panel` | 1 when it sat on a panel (flat card) in the source |
| 27 | `panel_kept` | 1 when it sat on a panel and is still >= 80% inside that panel's output box |
| 28 | `off_canvas` | share of its output box outside the target canvas |
| 29 | `floating` | 1 when the analyzer placed its unit as floating (badges, stickers) |
| 30 | `emphasis` | unit colour emphasis 0-1 (engine.analyze) |
| 31 | `g_src_aspect` | global token only: ln(source width / height) |
| 32 | `g_tgt_aspect` | global token only: ln(target width / height) |
| 33 | `g_change` | global token only: ln(target aspect / source aspect) |
| 34 | `g_scale` | global token only: ln(target area / source area) / 4 |
| 35 | `g_count` | global token only: element count / 40 |

**Cost:** encoding takes ~74 ms per design including the source analysis; reusing one analysis per case
costs a few ms per layout.

**Changing features:** update `CONT`, regenerate the data (or re-featurise from the jsonl), retrain and
re-export. `engine/critic_score.py` refuses a model whose feature count doesn't match and falls back to
the hand scorer. `critic/export.py` refuses a checkpoint trained on different feature names.

**Known shortcut risk:** in `original` groups the positive's output box equals its source box. The model
could learn "unchanged = good", but the `near` and `engine` groups have changed boxes in both positives
and negatives. Check the per-kind validation accuracy and the label agreement, not just the training loss.

## 6. Training (`critic/train.py`)

```bash
.venv/bin/python -m critic.train --smoke                       # 200 train / 50 val groups, 20 epochs: ~20 s
.venv/bin/python -m critic.train                               # full: config critic/configs/layout_small.yaml
.venv/bin/python -m critic.train --resume                      # continue from out_dir/last.pt
.venv/bin/python -m critic.train --device cpu --max-minutes 60
```

- **Loss:** pairwise logistic, mean softplus(score_neg − score_pos), over each group's positive and up to
  `max_negatives` sampled negatives.
- **Optimiser:** AdamW with linear warmup (capped at 10% of steps) and cosine decay; gradient clipping 1.0.
- **Seed** is fixed: `train.seed`.
- **Each epoch:**
  - writes val loss and val pairwise accuracy (overall and per kind) to `out_dir/log.csv`;
  - saves `out_dir/last.pt`, and `out_dir/best.pt` whenever val accuracy improves.
- **Output paths:** `out_dir` defaults to `../data/critic/runs/layout_small`; smoke runs write to
  `..._smoke`.
- **Expected time:** about 1 s per epoch per 200 groups on MPS. The full ~5,000 groups take ~25-30 s per
  epoch, so the 40-epoch config runs in about 20 min. This is an estimate, not a measurement.
- **Things to try:**
  - weight negatives by kind, or drop the noisiest kinds;
  - a margin on hand-score differences;
  - horizontal-flip augmentation (mirror every box);
  - larger models (`d_model` 256, 6 layers ≈ 5M parameters);
  - attention biases from the relation flags.

## 7. Evaluation (`critic/eval.py`) and the success bar

```bash
.venv/bin/python -m critic.eval --model ../data/critic/runs/layout_small/best.pt            # checkpoint
.venv/bin/python -m critic.eval --model engine/data/critic.onnx --page                     # exported model + page
python3 -m http.server 8771 --bind 127.0.0.1 -d ../data/critic/eval/disagreements          # the 20 worst disagreements
```

**Labels:** every `eval/results/**/labels.json` (Good / Okay / Bad on review pages), 245 labelled outputs
in 8 files:
- organiser samples, 63;
- crello-dev, retrieval-review, review-structure, review-v5 and review-v5-random, 30 each;
- review-extreme, 15;
- review-legibility, 17.

Each label stores the exact output it was given on. A further 15 labels from an abandoned experiment were
lost when their worktree was deleted.

**Metrics** (from `eval.calibrate.agreement`):
- **pairwise:** the share of differently-labelled pairs that the score orders the same way as the labels.
- **within:** the same, but only for pairs from the same design. The critic is trained only to compare
  layouts of one design, so this is its fairer number.
- **auc:** Good vs Bad.

The hand scorer and the critic are printed side by side, pooled and per label file. Hand scores include the
rendered contrast and are cached in `../data/critic/eval/hand_scores.json`; the first run takes ~70 s.

**Success bar:**
- **Target:** pooled pairwise agreement above **0.866**, the hand scorer's figure when this work started
  (on 185 labels).
- **Same-label reference:** on today's 245 labels with today's scorer, the hand scorer gets **0.830**
  pooled (auc 0.903). Beating 0.830 on the same labels is the minimum; 0.866 is the target.
- **Robustness:** also check that the critic doesn't lose badly on any single label file. With 245 labels,
  a 0.02 difference is noise.
- **End to end:** run the engine with the critic on and look at the outputs (section 9). Never tune on the
  labels.

## 8. Export and publish

```bash
.venv/bin/python -m critic.export --checkpoint ../data/critic/runs/layout_small/best.pt --out engine/data/critic.onnx
```

- The ONNX file is ~7 MB for `layout_small`; opset 17, dynamic batch.
- Export runs onnxruntime on random inputs and fails if it differs from PyTorch by more than 1e-3. It
  matched within 3e-8 on the smoke model.

Publish on Hugging Face (a public model repo):
1. Upload `critic.onnx`, the config yaml, `log.csv` and a model card.
   - The model card states: trained on Crello (CDLA-Permissive-2.0); contains no Crello pixels or text,
     only learned weights; the input format is `critic/features.py` at the commit it was trained on.
2. Build the image with the model baked in at BUILD time:

```bash
docker build --platform linux/amd64 \
  --build-arg CRITIC_URL=https://huggingface.co/<user>/<repo>/resolve/main/critic.onnx \
  -t chameleon-engine:critic .
```

Alternatively, copy the file to `engine/data/critic.onnx` before `docker build`. `COPY engine/` picks it
up. It is gitignored, so it never gets committed.

## 9. Enabling it in the engine

- **Switch:** `CHAMELEON_CRITIC=1`. `CHAMELEON_CRITIC_MODEL=/path/critic.onnx` overrides the model path;
  the default is `engine/data/critic.onnx`.
- **What happens:**
  1. After the normal selection, `engine/resize.py:_critic_search` starts the search from the chosen
     layout, the 3 best other candidates by hand score, and the best preserve layout.
  2. `engine/search.py` climbs until 12.5 s after the start.
  3. The result replaces the chosen layout only if it passes `check()`, is in no worse a safety tier
     (`engine.select._tier`), and the critic scores it above the chosen layout.
- **Search moves:** each move acts on one layout unit; the move list and step sizes are in the module
  docstring and constants. The search is a skeleton: expect to improve the moves once the critic is good.

```bash
# native, the 45 organiser cases (3 samples x 15 sizes); writes eval/results/{cases.csv,summary.md}
CHAMELEON_CRITIC=1 .venv/bin/python -m eval.bench --jobs 4
.venv/bin/python -m eval.snapshots compare v5 --suite samples
# the Crello suites (iterate on crello-quick; dev / structure / holdout before any merge)
CHAMELEON_CRITIC=1 .venv/bin/python -m eval.bench --suite crello-quick --jobs 4
# Docker, offline
docker run --rm --network none -e CHAMELEON_CRITIC=1 -v $PWD/input:/app/input -v $PWD/output:/app/output chameleon-engine:critic
```

- `eval.bench` overwrites the tracked `eval/results/cases.csv` and `summary.md`. Restore them with
  `git checkout eval/results/cases.csv eval/results/summary.md` unless you mean to commit a new baseline.
- **Run times:** with the critic on, every case runs until ~12.5 s, because the search uses the whole
  remaining budget. Expect ~2 min natively for the 45 samples at 4 jobs, and ~10 min in Docker under
  amd64 emulation.

**Review page for outputs:**
```bash
.venv/bin/python -m eval.bench --suite crello-dev --render --jobs 4
.venv/bin/python -m eval.review_server --results eval/results/crello-dev
```
The review server listens on http://127.0.0.1:8765. Labels you give there go into that suite's
`labels.json`, which is evaluation data for the next critic, never training data.

## 10. Plumbing check results (2026-10-19, smoke scale; not a model result)

| Step | Result |
|---|---|
| `make_data --limit 40` | 36 train / 4 val designs, 122 + 14 groups, 0 errors, 8 MB |
| `train --smoke` | 1.84M parameters on MPS, 20 epochs in ~20 s, best val pair accuracy 0.70 (14 val groups) |
| `export` | 7.4 MB ONNX; matches PyTorch within 3e-8 |
| `eval` | 245 labels: hand scorer 0.830 pooled pairwise, auc 0.903; smoke critic 0.647, auc 0.672 |
| Engine, `CHAMELEON_CRITIC=1` with the smoke model, samples | 45/45 pass hard rules, slowest 12.1 s; hand score 97.94 → 82.28 (38 outputs replaced). The untrained critic is bad, as expected. |
| Engine, `CHAMELEON_CRITIC=1` with no model (hand-scorer fallback) | 45/45 pass, 97.94 → 98.62. This only means the search climbs the scorer it is measured with; it is not evidence of better layouts. |
| `pytest` | 191 passed (including `eval/tests/test_critic.py`) |
| Docker (`critic` branch, amd64 emulated, `--network none`) | onnxruntime installs; build 123 s. Critic off: 45/45 OK, slowest 15.2 s. Critic on (smoke model mounted): 45/45 OK, slowest 16.5 s. **Both timings were taken while a full `make_data` run kept 4 CPU workers busy**: the same v5 code took 12.9 s alone. Re-measure with the machine idle before trusting or shipping anything. |

## 11. Known limitations

- **Positives come from rules, not designers.** Engine-group positives and `engine_low` negatives are
  chosen with the hand scorer, so the critic partly learns the hand scorer's taste. The damages and the
  original/near groups don't depend on it. Hand labels show the engine's own top outputs are often bad on
  extreme aspect changes (21 of 30 on the v5 review page).
- **Some damages are no-ops or mild** (a small nudge, a hero that was already small). Filter them by
  `hand` if they hurt.
- **`text_off_panel` is rare,** because few designs have flat panels holding text.
- **Scores compare layouts of one design only.** The pooled agreement still compares across designs,
  where an uncalibrated critic can lose. Watch both the pooled and within numbers.
- **The search is greedy and short** (whatever time is left before 12.5 s), with simple moves. Its gains
  depend entirely on the critic.
