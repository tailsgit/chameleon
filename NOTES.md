# Team notes: Chameleon starter repo

Summary of README.md, RULES.md, FAQ.md, `chameleon_design_schema_v0.9.json`,
`engine/main.py`, `engine/resize.py`, the 3 samples in `input/`, and the
vendored renderer (`renderer/converter/*` + `cr_renderer`). Line refs are to
those files.

## 1. Input and output format

### Input task file (`input/*.json`)

| Field | Notes |
|---|---|
| `task_id`, `difficulty`, `difficulty_label`, `notes` | Metadata only. `main.py` ignores them. |
| `source` | The design: `{canvas, elements}` (schema below). |
| `target_canvas` | `{width, height}` in px. |

`main.py` calls `resize(task["source"], task["target_canvas"])` (main.py:118-121).

### Design document (same shape for source and output). Schema v0.9, marked "provisional, pending Peter's sign-off"

Top level: `{"canvas": {...}, "elements": [...]}`, with `additionalProperties: false`, so
**no extra top-level keys are allowed** (schema:6-8). `elements` has `minItems: 1`.

`canvas`: `width`, `height`, both **integer** ≥ 1, px, with no other keys (schema:18-26).

Element. Required: `id, type, x, y, width, height` (schema:29). Elements do
**not** set `additionalProperties: false`, so extra keys such as the samples'
`_note`/`_adversarial_note` are allowed through. The baseline copies them as-is.

| Field | Type / default | Applies to | Meaning |
|---|---|---|---|
| `id` | string | all | Must be returned exactly once. Can't add, remove or invent ids. |
| `type` | `text` \| `image` \| `shape` | all | |
| `x`, `y` | number | all | Top-left of the **unrotated** box, px, from the canvas top-left |
| `width`, `height` | number ≥ 0 | all | px |
| `rotation` | number, default 0 | all | Degrees, clockwise, about the element centre |
| `opacity` | 0..1, default 1 | all | (but see renderer caveat for text below) |
| `z_index` | integer | all | Higher paints on top. Optional (renderer treats a missing value as 0) |
| `group_id` | string\|null, default null | all | Shared value = "designer-intended unit" |
| `content` | string, **required** | text | Literal string. Keep fixed for stage one |
| `font_family` | string, **required** | text | `Solstice Serif` / `Solstice Sans`. Keep fixed for stage one |
| `font_size` | number ≥ 1, **required** | text | px. **Engine may change it** |
| `font_weight` | `regular`\|`bold` | text | |
| `font_style` | `normal`\|`italic` | text | |
| `color` | string, **required** for text | text/shape | `rgba(r,g,b,a)` |
| `text_align` | `left`\|`center`\|`right`, default left | text | |
| `line_height` | number, default 1.2 | text | Multiplier |
| `letter_spacing` | number, default 0 | text | px |
| `max_lines` | int\|null | text | "Optional cap; the renderer wraps within width/height regardless" |
| `style_runs[]` | `{start, end, color?, font_weight?, font_style?}` | text | 0-based, **end-exclusive** char ranges |
| `asset_id` | string, **required** | image | Filename in `brand_kit/assets/` |
| `fit` | `contain`\|`cover`\|`fill`, default `contain` | image | See section 3 |
| `shape_type` | `rectangle`\|`ellipse`\|`line`, **required** | shape | |
| `fill_color` | string, **required** | shape | rgba. Its alpha is multiplied into opacity |
| `stroke_color`, `stroke_width` | null / 0 | shape | |
| `corner_radius` | number, default 0 | shape (rect) | |

### Output

`resize()` returns `{"canvas": {"width": W, "height": H}, "elements": [...]}`,
which is the same schema as the source. `main.py` writes
`output/<task_stem>_output.json` + `output/<task_stem>_output.png` (main.py:126-127).
Both are scored (RULES.md:13-20).

### Samples

| File | Elements | Resize | Interesting bits |
|---|---|---|---|
| level1_warmup | 4 | 1080² → 1080×1350 | bg, logo, headline, CTA text |
| level2_core | 11 | 1080² → 1600×400 | 2 groups (`badge`, `cta`), semi-transparent deco circles, one bleeding off canvas at (-100,-100), `style_runs` two-colour headline |
| level3_advanced | 17 | 1080×1350 → 728×90 | run-on headline, 3 badge groups, rotated ribbon group (-12°), **missing asset** `solstice_holiday_badge_2025.png` (no `fit` set, so it defaults to contain), legal text |

Assets: `solstice_bg_gradient.png` 1200×1500 (4:5, RGB), `solstice_logo_lockup.png`
900×300 (3:1, RGBA, white wordmark), `solstice_bottle.png` 800×800 (1:1, RGBA).

## 2. Hard rules and disqualifiers

**Disqualifying**
- **Regenerating, redrawing or replacing any asset's pixel content, including with
  generative AI, even for a background or minor decoration** (RULES.md:46-50,
  resize.py:30-32). Reposition and resize only.

**Hard requirements (structural JSON check, RULES.md:17)**
- Same element `id`s as the source, nothing added or removed.
- Required fields present (per type, see table above).
- Nothing off-canvas.
- Images kept in proportion. resize.py:33-35: *"Non-background image elements
  should be kept in proportion (matching the source aspect ratio within ~5%)
  unless they are a full-bleed / `fit: "cover"` element, which is expected to crop."*
- The PNG must render legibly. A good JSON with a bad render, or a good render
  with a "broken or dishonest" JSON, gets no credit (RULES.md:20).

**Stage-one constraints**
- `content` and `font_family` are fixed. `font_size` may change (RULES.md:42-44).
  Rewriting copy or swapping fonts is a finale idea only.
- Runs with **`--network none`**. Everything must be installed at Docker
  **build** time, and any model weights must be baked into the image (README:90-93).
- Any fine-tuned/LoRA weights must be **publicly accessible**, e.g. a public HF
  repo (RULES.md:26).
- Must run on the reference machine, "Apple M5 Pro", with exact limits TBD
  (RULES.md:32). The image is `linux/amd64`.
- Latency is not disqualifying. Quality comes first, and speed is a minor rubric row (RULES.md:11).
- Target sizes come from a fixed catalogue of real platform formats
  (Instagram Post, YouTube Thumbnail…). The hidden ones are unseen (RULES.md:36).
- Submission: code + Dockerfile + short README of the approach + an Express
  add-on viewer (required, not scored) (FAQ.md:105).
- We only need to edit `engine/resize.py` (README:3-5).

## 3. Images: crop, focal point, fit, and full-bleed backgrounds

**The schema has `fit` but no crop, focal-point, anchor or offset fields.**
The only image-specific fields are (schema:75-76):

```json
"asset_id": { "type": "string", "description": "image only — references a file in the design's /assets folder. The engine never invents pixels; it only repositions/resizes this asset." },
"fit": { "type": "string", "enum": ["contain", "cover", "fill"], "default": "contain", "description": "image only" },
```

What each `fit` does in the renderer (`renderer/converter/assets.py:49-66`):
cr-renderer itself just stretches an image into its box, so the converter
emulates fit before handing it over:
- `contain`: scale = `min(w/iw, h/ih)` and paste **centred** on a transparent box (letterboxed).
- `cover`: scale = `max(w/iw, h/ih)`, then crop **centred**:
  `left, top = (nw - w) // 2, (nh - h) // 2` (assets.py:62). The crop is always centred
  and there's no way to bias it.
- `fill` (or anything else): stretch to the box, which **distorts**.

**What a full-bleed background should do when the aspect ratio changes:** set the bg
element to `x=0, y=0, width=target.w, height=target.h`, keep `fit: "cover"`,
and the renderer scales the asset to cover the canvas and centre-crops it. This is
explicitly exempt from the proportion rule ("unless they are a full-bleed /
`fit: "cover"` element, which is expected to crop", resize.py:33-35), and it's
what `brand_kit/README.md:11` describes (`solstice_bg_gradient.png` = "full-bleed
background (`fit: cover`)"). Note the bg asset is 4:5, so even the 1080² source
is already centre-cropped. For 1600×400 (4:1) only the middle ~20% of the asset's height
survives, and for 728×90 only about the middle 7%.

Consequences:
- We **can't choose the crop window** through the schema. The only lever would be
  to oversize or offset the image box past the canvas edge, which breaks "nothing
  off-canvas". **Don't do that without asking** (see open questions).
- For `contain` images, a box with the wrong aspect won't look distorted
  (it's letterboxed), but the JSON check will still compare aspect ratios, so keep
  the box aspect equal to the source box aspect.
- Don't use `fill` on anything that changes aspect.

## 4. Grouping, z-order, opacity, rotation

- **Grouping**: flat `group_id` string on each element (schema:43-47), with no nesting
  and no group-level geometry. Samples: `badge` (shape + label), `cta`,
  `badge1..3`, `ribbon`. Labels sit inside their bg shape's box. Preserve the
  relative layout within a group and scale it as a unit.
- **Z-order**: `z_index` integer, higher on top. The converter does a stable sort by
  `z_index` with missing values as 0 (convert.py:55), so **ties paint in list order**.
  The samples use many ties (e.g. all text at 4 or 5).
- **Opacity**: `opacity` 0..1 per element. For shapes the converter multiplies
  `fill_color`'s alpha into it (convert.py:103). **For text, cr-renderer ignores
  element `opacity`**: `_render_to_surface` builds `TextElement` without passing
  opacity (default 1.0, cr_renderer/schema.py:23). Only the alpha in `color` /
  `style_runs` colour applies to text. Don't rely on text `opacity`.
- **Rotation**: degrees clockwise about the element's centre. `x, y, width,
  height` describe the **unrotated** box. The renderer translates to (x,y) and rotates
  around (w/2, h/2). The ribbon group is at -12°.

## 5. What `main.py`'s self-check validates (main.py:37-68)

It's not the official scorer. Warnings don't fail the run.
1. Output has top-level `canvas` and `elements`.
2. The set of output ids equals the set of source ids. Note it's a set check, so a
   **duplicated id would not be caught**.
3. Each element has `id, type, x, y, width, height` + per-type required fields.
4. Off-canvas: warns if `x < -0.5`, `y < -0.5`, `x+w > W+0.5` or `y+h > H+0.5`.
   It uses the **unrotated** box, so it ignores rotation.

It does **not** check aspect ratios, font sizes, text overflow, overlap, z-order,
schema types/enums, integer canvas, or legibility.

Baseline run (uniform stretch): L1 OK, L3 OK, L2 warns
`element 'deco_circle_1' is off-canvas (1600x400)`. That's because the source already
bleeds it to (-100,-100), and README:64-66 calls it "an expected one".

## 6. Renderer facts that will bite us

- Text wraps only at spaces, greedily, at real glyph widths (wrap.py). A single word
  wider than the box **overflows** and is never hard-broken. Text taller than its box
  is **not clipped or shrunk**: we must pick `font_size` ourselves. `max_lines`
  is ignored by the converter.
- `style_runs`: the converter treats `end` as **inclusive** (`range(start, end+1)`,
  convert.py:174-190), while the schema says end-exclusive. The result is that one extra
  character gets the run's style. (L2 sample: `start 6, end 16` on a 15-char string.)
- `stroke_color` / `stroke_width` are ignored for rectangles and ellipses (shapes.py).
  `line` is always drawn horizontally through the box's middle.
- The PNG is capped at 2048 px on the long side (`max_size=2048`, convert.py:270),
  so larger targets get downscaled. Uncovered canvas is white.
- Missing assets render as a grey "missing asset" placeholder and add a warning. They don't crash.
- **Text is top-aligned in its box.** There's no vertical centring: line *i* starts at
  `i * font_size * line_height` from the box top. A 15px label in a 26px box sits at
  y≈5–16, so centring text in a pill means positioning the box itself.
- Wrapping is measured at the float `font_size`, but glyphs are drawn at **`int(font_size)`**
  (cr_renderer `make_text_blob`). A 20.9px font renders as 20px, so use whole-number sizes.
- Wrapping ignores `letter_spacing`, but drawing applies it, so a spaced-out line can
  overflow its box. `eval/check.py` measures with the renderer's own widths and catches this.

## 7. Open questions for the organisers

1. **Off-canvas vs intentional bleed.** RULES says "nothing off-canvas", but the L2
   source bleeds `deco_circle_1` and README calls that warning "expected". Is
   bleed allowed for decorative shapes? And for images, to control a `cover` crop?
2. **Cover crop control.** There are no focal-point or crop fields, and the renderer always
   centre-crops. Will v1.0 add a focal point or anchor? If not, may a full-bleed
   image box extend past the canvas to shift the crop?
3. **"Source aspect ratio within ~5%"**: is that the source *element box* or
   the *asset file*? They differ: L1 logo box 320×100 = 3.2 vs asset 3.0 (6.7%
   apart). And which images count as "background"? Only `fit: cover`, or also full-canvas boxes?
4. **Off-canvas for rotated elements**: is the check on the unrotated box (like
   main.py) or the rotated bounding box?
5. **Missing-asset element** (L3 `holiday_watermark`): must it stay visible
   as a placeholder, or may we shrink or hide it (e.g. opacity 0 or size 0)? Is that
   "removing" an element?
6. **May we change `opacity`, `rotation`, `z_index`, `line_height`,
   `letter_spacing`, `text_align`, `corner_radius`**, or only position, size and `font_size`?
   (FAQ Q1 says "updated position/size (and, for text, optionally font size)".)
7. **Minimum legible font size** at scoring? (L3 → 728×90 forces tiny text, and the
   legal line is 12 px in the source.)
8. `style_runs` end: inclusive (renderer) or exclusive (schema)? Will the official
   renderer be fixed?
9. Text `opacity` is ignored by the renderer. Is that intended?
10. **Missing docs**: the "main brief" (Sections 3.3, 5, offline/**size-limit** rule)
    isn't in the repo. What's the image size limit? The FAQ's `transformer-convertor` app
    (`app.py`, port 5050) isn't in the repo either, only the vendored converter.
11. Reference hardware spec (cores/RAM/GPU) and whether arm64 images are accepted.
12. Is the target-size catalogue published?
13. Schema is v0.9 "provisional": when is it frozen?

## 8. Crello dataset (`cyberagent/crello` on Hugging Face)

- **Downloaded so far**: only the 3 validation shards (1.43 GB, 1,852 designs), in
  `/Volumes/Extreme/AdobeHackathon/data/crello/`, which is **outside the repo** on purpose.
- **Size**: ~18.2 GB of parquet (`download_size` 18,207,073,052 bytes) in 37 shards
  (31 train / 3 val / 3 test), plus `resources/fonts.pickle` (60 MB). 19,479 train,
  1,852 val and 1,971 test designs. Not gated.
- **Format**: one row per design, with columns per element (as sequences): `type`
  (Svg/Text/Image/ColoredBackground/SvgMask), `left/top/width/height` **normalised
  0-1**, `angle` (**in units of π**), `opacity`, `color`, `image` (pre-rendered PNG crop per
  element), `text`, `font` (class index into 260 fonts), `font_size`, per-char
  `font_bold/italic/text_color/text_line`, `text_align`, `line_height`,
  `letter_spacing`, plus design metadata: `canvas_width/height`, `format` (67 classes,
  e.g. "Instagram", "Youtube Thumbnail", "Leaderboard": useful as our target
  catalogue), `category`, `keywords`, `preview`. It's the same format cr-renderer reads (FAQ Q2).
  There is **no `group_id`**, and nothing tells you which element is the background.
- **Licence**: the dataset is distributed under **CDLA-Permissive-2.0**, but the card says
  the distributor doesn't own the template copyrights, and **"By using the Crello
  dataset, the user ... must agree to the VistaCreate License Agreements."**
  - CDLA-Permissive-2.0 explicitly allows using the data, including for training models,
    and puts no restrictions on the *results* (model outputs/weights).
  - The VistaCreate agreement says nothing about ML/training. It does prohibit
    "use Files, Elements separately from Designs", "Make Designs available for free
    download", "Transfer, resell, sub-license … Designs", and extracting elements.
  - **Reading:** training a layout model, or mining layout statistics/rules from it, is
    fine under CDLA, and VistaCreate's terms don't address it. **Shipping Crello
    designs or their image crops as templates in our repo or Docker image is risky**
    (redistribution or extraction of elements). Prefer deriving geometry-only
    templates (normalised boxes, no pixels or text) and ask the organisers. This also
    ties into the "no regenerated pixels" rule: never paste Crello imagery into outputs.

## 9. Docker timings (2026-10-17, Apple Silicon, linux/amd64 under emulation)

| Step | Time | Notes |
|---|---|---|
| `docker build --platform linux/amd64` | **770 s** (~12.8 min) | Image is 1.24 GB. Cold cache: base image, apt, pip incl. skia |
| `docker run --rm --network none …` | **228 s** (~3.8 min) | 3 samples. `resize()` itself takes ~0 s, so this is almost all emulated renderer start-up + rendering |
| Native `python -m engine.main` | ~4 s | Same 3 samples |

The JSON outputs were byte-identical to the native run. The PNGs differ by a few hundred
bytes, most likely from anti-aliasing. Under emulation the run averaged ~76 s per sample (including
start-up), against ~70 ms per render natively (see section 12).

## 10. Baseline (uniform stretch) review

The baseline scales x and width by `tw/sw`, y and height by `th/sh`, and font size by the smaller of the two.

- **Level 1 (1080² → 1080×1350)**: looks almost fine, which hides the problems. Every
  box is 20% taller than its proportions allow (logo `image_aspect` -20%; `contain` hides it
  visually). Nothing is re-laid-out to use the extra height: the headline–CTA gap grows
  to ~125 px and the bottom quarter is empty.
- **Level 2 (1080² → 1600×400)**: every box is 4× too wide. The deco circles become flat
  ovals, and the product box is 741×185, so the bottle is a small icon and the logo is tiny.
  Fonts drop to 20/8/6/8 px (int-rendered), so the subhead and badge are unreadable. Everything
  stays in one central column, leaving most of the banner empty. The subhead sits flush
  against the CTA pill. (Earlier I said it overlaps it; the scorer measured the drawn text
  and they only touch, and they nearly touch in the source too.)
- **Level 3 (1080×1350 → 728×90)**: unusable. Fonts are 1–2 px. Badges and the CTA become thin
  lines. The -12° ribbon becomes a 202×3.6 box that renders as a long red diagonal slash
  poking out above the canvas (`off_canvas_rotated`). The missing-asset placeholder is
  a grey strip.
- In all three, the background is fine: `cover` centre-crops whatever box it gets.

## 11. Assumptions (decided by the team, not confirmed by the organisers)

1. **Backgrounds**: full canvas (`x=0, y=0, w=W, h=H`), `fit: "cover"`, and the renderer's
   centre crop is accepted. `eval/check.py` enforces this (`background_not_full_canvas`).
2. **Bleeds**: elements that bleed off-canvas in the source (L2 `deco_circle_1`, L3
   ribbon's rotated corner) are pulled **fully inside** in our output. We check both the
   unrotated box (`off_canvas`) and the rotated bounding box (`off_canvas_rotated`).
3. **Crello is used only to learn from**: geometry and roles only, never pixels or text.
   Nothing from Crello is committed to the repo or baked into the Docker image.
4. **No model for now.** Any future model must be small (target well under 100M parameters).
5. **Rendering is expensive**, because scoring may run under amd64 emulation. The engine ranks
   most candidate layouts geometrically (`eval/score.py`, ~1 ms) and renders only the top few.
6. "Source aspect ratio within ~5%" = the **source element box's** aspect, not the asset file's.

## 12. Evaluation tooling (`eval/`)

```bash
pip install -r requirements-dev.txt     # pytest, jsonschema (dev only, not in Docker)
python -m pytest                        # 58 tests, ~1 s
python -m eval.bench                    # 3 samples x 15 formats: check + geometric score
python -m eval.bench --render --contrast  # + PNG per case, contact sheet, contrast penalty
```

- `eval/check.py` (`check(source, target_canvas, output)`) returns the hard-rule violations listed in
  its docstring. Text overflow is computed with the converter's own wrap and
  cr-renderer's own line layout, and is tested against real renders: the ink bbox stays within 3 px of
  the prediction across 24 cases, including fractional sizes, alignment, letter spacing,
  bold runs and overflow.
- `eval/score.py` (`score(...)`) gives 0–100 from weighted penalties: overlap, small_text,
  headline, space, alignment, reading_order, plus optional contrast, which renders once. Each
  penalty is a documented function with its weight in `PENALTIES`. All geometry uses
  what is drawn (laid-out text lines, letterboxed `contain` images), not raw boxes.
- `eval/bench.py` writes `eval/results/summary.md` + `cases.csv`. `--render` adds
  `renders/` + `contact_sheet.png` (both gitignored).

**Baseline floor (uniform stretch, 45 cases):** 1/45 cases pass every hard rule (the
identity case: L1 → Instagram Post). Average score 87.06 with contrast, 86.69 without.
Violations: `image_aspect` 84 (42 cases), `off_canvas_rotated` 20 (11), `off_canvas` 15 (15).
Weakest formats: Leaderboard (64–72), Email Header, Wide Skyscraper, Facebook Cover.

**Timings, native Apple Silicon:** render ≈ 70 ms/case (max 144 ms), check ≈ 1.1 ms,
geometric score ≈ 1.4 ms (≈ 105 ms with contrast, because it renders).

**Rules we can't turn into an automatic check:**
- "No regenerated pixels": we can only check the proxies, i.e. `asset_id` and `fit` unchanged
  and no invented elements. Writing new image files isn't visible in the JSON.
- "Renders legibly" and faithfulness to the design's intent: these are judged by the AI evaluator
  and its rubric. We only have proxies (small_text, overlap, contrast).
- "Dishonest JSON": only the `hidden_element` proxy (size < 1 px or opacity 0).
- Process rules: offline at run time, public LoRA weights, the reference-hardware
  budget and the (unknown) size limit. These are covered by the Docker run, not by `check`.
- Which aspect ratio counts (box or asset), and whether the off-canvas check uses rotated
  bounds: these are open questions, and both are handled by our assumptions above.
- Renderer quirks (text `opacity` ignored, inclusive `style_runs` end) aren't flagged.

## 13. Engine v1 (`engine/`)

`resize()` = `analyze` → `recipes.generate` (~12–90 candidate plans) → `fit.realize` →
`select`. It never raises: a failing recipe is skipped. If no candidate passes, they are
repaired and compared with a uniform-scale fallback; failing that, a repaired stretch is returned.

- **analyze.py**: background = bottom-of-stack elements covering the canvas. Rigid units come
  from `group_id`, text inside an opaque shape, and decorations tightly inside a unit. Roles
  come from rules with confidences (documented in `_assign_roles`), importance from role +
  confidence + area, and reading rows from the drawn boxes.
- **recipes.py**: stack, split, strip, overlay (stack in the quietest background region),
  compact (only primary units in flow). They share one column solver that searches for the
  largest common scale, with fonts never below the readable floor, and demotes the least
  important unit to "floating" when even the floor doesn't fit.
- **fit.py**: text gets the largest whole-number font that fits, measured with the checker's own
  layout code. Letter spacing scales with the font, and the box is narrowed when the
  renderer's spacing-blind wrapping would overflow. Images and groups use one uniform scale. Floating units
  go into the best free rectangle near their source position. Decorations are re-anchored inside the canvas.
- **select.py**: `check()` filter → geometric `score()` → render the top 10 → best full
  score including contrast.
- `eval/` is now copied into the Docker image (`COPY eval/*.py`) and `jsonschema` is in
  `requirements.txt`, because the engine ranks candidates with the same checker and scorer.
  The old stretch baseline lives on in `eval/baseline.py`.

**Results (45 cases):** 45/45 pass every hard rule (baseline 1/45). Average score **96.05**
(baseline 87.06). Native resize ≈ 1.3 s/case, of which ≈ 1 s is the 10 contrast renders.

**Robustness:** 40 seeded random designs are in the test suite, and all pass. A one-off run of 300
more gave 295 clean and 0 crashes. All 5 failures have a source text with letter spacing that
already overflows its own box inside a group or rotated unit.

### Five weakest cases (by eye)
1. **L3 → Leaderboard 728×90 (82.3)**: chaotic. The subhead is demoted into a separate text
   block on the far left, the ribbon floats between the bottle and the CTA, the CTA pill is
   oversized (held at a readable label size), the three badges become a tiny strip, the logo
   is barely visible, and the hierarchy is lost.
2. **L3 → Medium Rectangle 300×250 (83.2)**: the subhead floats to the top-left ahead of the
   headline, the logo is a speck, the badges are cramped in a column on the right, and the CTA dominates.
3. **L3 → Email Header 600×200 (87.2)**: no clear reading order. Badges are scattered top and
   left, the ribbon cuts across, the subhead is large on the right, and the legal text is in a thin column.
4. **L3 → Wide Skyscraper 160×600 (87.6)**: the text starves the images (the bottle and logo are
   icons at the top), the ribbon sits mid-flow and splits the badges, and the legal text takes the bottom.
5. **L1 → Leaderboard 728×90 (97.1)**: tiny content huddled left of centre, two-thirds of the
   banner empty, logo barely visible. A weak layout that scores well (see below).

### Where the scorer disagrees with the eye
- **Sparse layouts score too well.** L1 → Leaderboard 97.1 and L1 → Instagram Story 99.8: the
  content is clumped (left third, or top 40%) with the rest empty. `space` compares coverage and
  empty ninths *to the source*, and the L1 source is itself sparse (7% coverage, 5 empty
  ninths), so emptiness is "faithful". Fix: also penalise absolute empty bands and balance
  (centre of mass far from the canvas centre).
- **L3 → LinkedIn 92.0**: a big empty middle and unbalanced sizes (18 px text vs a huge bottle) only
  cost `space` 0.06. Same fix, plus a size-balance term between hero and text.
- **Headline dominance uses font_size only.** L2 → Medium Rectangle 95.3: the serif headline at
  14 px looks smaller than the 13 px sans subhead and the bold CTA label. Fix: compare rendered
  cap or x-height, or ink area, not the nominal size.
- **Contrast isn't relative to the source.** Every L3 case pays the same 0.14 for white on the
  source's own orange badges (3.2:1), which the engine can't change. Fix: penalise only
  contrast lost relative to the source.
- **Reading order punishes legitimate side-by-side layouts.** Split and strip layouts that read well
  (L3 → Facebook Post 93.0, LinkedIn) get 0.2–0.4 `reading_order`, because the row model
  puts the right-hand hero after the text. Fix: judge order within the text column and
  between primaries only.
- **Floating placement isn't judged.** Demoted units dropped into odd gaps (L3 leaderboard
  and email header) cost little, because `reading_order` and `alignment` barely see them.
