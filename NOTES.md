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
14. Is changing an element's `rotation` allowed? The rules don't forbid it. We only ever mirror the source angle (see §15).

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
   Since §20 (branch `retrieval`), one derived file ships in the repo and the image:
   `engine/data/layout_library.json`, which holds normalised unit boxes, roles and aspect ratios only,
   with no text, pixels, asset ids or Crello ids. §8 judged this form the low-risk one, but it is
   still worth confirming with the organisers before it is submitted.
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

**Results (45 cases):** 45/45 pass every hard rule (baseline 1/45). Average score **95.82**
(baseline 87.06). Native resize ≈ 1.3 s/case, of which ≈ 1 s is the 10 contrast renders.
Docker (amd64, emulated): cached build 113 s, run 15 s for the 3 samples (2.5–4.3 s per case);
all 45 cases in the container take ≈ 125 s.

**Cross-platform text metrics (important):** with the same skia-python 144.0.post2, glyph advances
differ by ~1% between macOS (CoreText) and Linux (FreeType). The L3 subhead at 22px wraps to 8
lines natively and 9 in Docker. We don't know where the official renderer runs, so text boxes
get at least one spare line of height (invisible, since text is top-aligned), tight boxes get a 3% width
margin, and group labels must fit in 97% of their width. Verified: all 45 outputs made natively pass
`check()` inside Docker, and all 45 made in Docker pass natively.

**Robustness:** 40 seeded random designs are in the test suite, and all pass. A one-off run of 300
more gave 295 clean and 0 crashes. All 5 failures have a source text with letter spacing that
already overflows its own box inside a group or rotated unit.

### Five weakest cases (by eye)
1. **L3 → Leaderboard 728×90 (82.8)**: chaotic. The subhead is demoted into a separate text
   block on the far left, the ribbon floats between the bottle and the CTA, the CTA pill is
   oversized (held at a readable label size), the three badges become a tiny strip, the logo
   is barely visible, and the hierarchy is lost.
2. **L3 → Medium Rectangle 300×250 (80.2)**: the subhead floats to the top-left ahead of the
   headline, the logo is a speck, the badges are cramped in a column on the right, and the CTA dominates.
3. **L3 → Email Header 600×200 (85.3)**: no clear reading order. Badges are scattered top and
   left, the ribbon cuts across, the subhead is large on the right, and the legal text is in a thin column.
4. **L3 → Wide Skyscraper 160×600 (87.3)**: the text starves the images (the bottle and logo are
   icons at the top), the ribbon sits mid-flow and splits the badges, and the legal text takes the bottom.
5. **L1 → Leaderboard 728×90 (97.0)**: tiny content huddled left of centre, two-thirds of the
   banner empty, logo barely visible. A weak layout that scores well (see below).

### Where the scorer disagrees with the eye
- **Sparse layouts score too well.** L1 → Leaderboard 97.0 and L1 → Instagram Story 100.0: the
  content is clumped (left third, or top 40%) with the rest empty. `space` compares coverage and
  empty ninths *to the source*, and the L1 source is itself sparse (7% coverage, 5 empty
  ninths), so emptiness is "faithful". Fix: also penalise absolute empty bands and balance
  (centre of mass far from the canvas centre).
- **L3 → LinkedIn 94.1**: a big empty middle and unbalanced sizes (18 px text vs a huge bottle) only
  cost `space` 0.06. Same fix, plus a size-balance term between hero and text.
- **Headline dominance uses font_size only.** L2 → Medium Rectangle 92.9: the serif headline at
  14 px looks smaller than the 13 px sans subhead and the bold CTA label. Fix: compare rendered
  cap or x-height, or ink area, not the nominal size.
- **Contrast isn't relative to the source.** Every L3 case pays the same 0.14 for white on the
  source's own orange badges (3.2:1), which the engine can't change. Fix: penalise only
  contrast lost relative to the source.
- **Reading order punishes legitimate side-by-side layouts.** Split and strip layouts that read well
  (L3 → Facebook Post 92.8, LinkedIn) get 0.2–0.4 `reading_order`, because the row model
  puts the right-hand hero after the text. Fix: judge order within the text column and
  between primaries only.
- **Floating placement isn't judged.** Demoted units dropped into odd gaps (L3 leaderboard
  and email header) cost little, because `reading_order` and `alignment` barely see them.

## 14. Scorer v2, calibrated against hand labels

All 45 engine-v1 outputs were labelled by hand: 11 Good, 12 Okay, 22 Bad (`eval/results/labels.json`).
Each label stores the exact output it was given on (see §15), so the scorer can keep
changing without the labels going stale. `python -m eval.calibrate [--fit]` reports agreement and
refits the weights. `eval/tests/test_calibration.py` fails if pairwise agreement drops below 0.85.

### Agreement with the labels (45 cases)

| scorer | pairwise, all | pairwise, within design | Kendall τ-b | AUC, good vs bad |
|---|---|---|---|---|
| v1 (the scores the labels were given against) | 0.730 | 0.698 | +0.37 | 0.82 |
| v2, fitted weights | **0.892** | **0.891** | **+0.63** | **1.00** |
| v2, weights fitted on 2 designs, tested on the 3rd | – | 0.885 | – | – |

Pairwise means: of the case pairs with different labels, the share the score orders the same
way (0.5 is chance). The leave-one-design-out row is the honest number, and it is close to
the in-sample one. Most of the gain comes from the penalty fixes, not the weights: v2 with
the old hand-set weights already reaches 0.887.

### What changed (each fixes a §13 disagreement)
- **space** is now judged against the target canvas, not the source:
  - half: the content box should span at least 60% of each side;
  - a quarter: the widest empty band through the content (the hole in a split layout), beyond 10%;
  - a quarter: empty ninths beyond 4.
- **balance** (new): the content centre sitting further off-centre than it did in the source.
- **headline** is judged on visual size: the x-height of the drawn font × √(weight/400).
  - The headline must lead every other text by min(1.4×, its lead in the source).
- **contrast**: the bar is min(WCAG, the element's contrast in the source), so the source's
  white-on-orange badges cost nothing. The source render is cached.
- **reading_order**: the output may be read row by row or column by column, whichever matches
  better. Floating units are left to `floating`.
- **floating** (new): a small unit that is rotated or sits within 12% of two adjacent edges must
  keep its gaps to that corner.
- **alignment** also counts source alignments the layout lost (a row of badges broken up).
  A row may become a column.

### Fitted weights
| penalty | weight |
|---|---|
| space | 2.6 |
| small_text | 1.5 |
| balance | 1.5 |
| headline | 1.2 |
| floating | 1.2 |
| overlap, alignment, reading_order, contrast | 0.5 each |

The weights sum to 10. Every weight is floored at 5% of the total: the labelled outputs barely
vary on overlap and contrast (the engine already avoids both), so the fit would zero them,
but they still have to guard the engine's choice between candidates.

### Engine changes
- **Same aspect** (within 2%): the uniform scale of the source is added as a preferred candidate.
  It loses only to a candidate more than 2 points better. L3 → Instagram Portrait is now the
  source layout (labelled Bad before).
- Because the engine ranks candidates with this scorer, the new weights change 31 of 45 outputs.
  Under the v2 scorer the average goes 90.2 (v1 outputs) → 94.4 (v2 outputs), still 45/45 passing.
  By eye most changes are better:
  - L1 wide formats are centred and larger;
  - the L2 LinkedIn hole is gone;
  - the L3 ribbon goes back to its corner.
  L3 → Email Header and Leaderboard are still chaotic, and the L1 skyscraper logo is tiny.
  **These v2 outputs are not labelled yet**: the agreement numbers above are for v1 outputs only.

## 15. Emphasis, attachments, tilt, label snapshots

### Rotation may change (by omission)
Neither the schema nor RULES.md forbids changing `rotation`. RULES.md lists the structural
checks (ids, required fields, off-canvas, image proportions) and fixes content and font family.
The schema describes rotation only as "Degrees, clockwise, about the element's center". Only
`font_size` is explicitly named as changeable. We therefore treat rotation as allowed but use it
minimally: the source angle, or its exact negation. This is added to the open questions (§7).

### Colour emphasis (`eval.score.emphasis`, shared by the engine and the scorer)
- An element's own colour (text colour or shape fill) is emphasised when it is saturated (CIELAB
  chroma ≥ 30) and at least 35 ΔE from every main-palette colour.
- Main palette = colour clusters covering ≥ 20% of the painted area. Images count towards the
  palette by their mean colour but are never emphasised themselves.
- White or black text is contrast, not emphasis.
- On the samples this flags the orange CTA in L1–L3, the orange badges, and the red ribbon.
  Badge 2 (dark) is not flagged.

What uses it:
- **Engine:** importance gets +0.15 × emphasis. A floating stand-out unit is centred in its free
  rectangle. Plans with such units are realised both centred and anchored, and the scorer picks.
  (Centring stand-out lines inside left-aligned columns was tried and dropped: it broke the
  column's alignment.)
- **Scorer, `emphasis` penalty:** a stand-out unit should be either at the end of the reading path,
  or centred in its column (5% free, full penalty at 25% of the column width). A row of
  side-by-side units counts as one block.
  - Weight 1.0. The fit leaves it at the floor because the labels predate it, and agreement is the
    same either way.

### Attachments and tilt
- A badge or decoration covering 15–90% of a bigger unit (any share, if rotated) is attached to it.
  The engine places it last, at the same relative spot on the host and scaled with it. The scorer
  measures drift inside the host box instead of from a canvas corner.
- Rotated units keep their source angle. It is negated only when the unit ends up on the mirrored
  side of its anchor on exactly one axis (anchor = host centre, else canvas centre). On both axes
  that is a half-turn, so the angle stays the same. No other angle is ever produced.
  - Only units whose rotated members share one centre are mirrored.
  - The scorer adds 0.5 to the floating penalty when a tilt points the wrong way.
- None of the three samples has an attached unit. A synthetic ribbon-on-card design in
  `test_engine.py` covers it.

### Label snapshots
- `bench` writes each output to `eval/results/outputs/<case>.json` (not committed).
- The review server stores that exact JSON inside the label, so calibration can use labels from
  any engine version.
- A verdict on a changed output moves the old one into the case's `history`.
- The page marks verdicts given on an earlier output. Clicking the same button confirms the verdict
  for the new output.
- The 45 existing labels were migrated with their frozen outputs, and `eval/calibration/` is gone.

### Effect (engine `9ca181f` vs `6203082`)
Five cases changed, all in L3, and all still pass. Average score 94.77 (not comparable to before:
there is a new penalty).
- **Leaderboard:** much tidier. Text block left, CTA and badges at the right end.
- **Email Header:** tidier. Badges in a top row, CTA at the right end.
- **Facebook Cover and Medium Rectangle:** about the same.
- **Presentation 16:9:** smaller content, slightly worse by eye, though it scores the same.

Raising emphasised badges' importance makes the solver drop the dark badge first on tiny
canvases, which splits the badge row. On Medium Rectangle and Facebook Cover the old layouts
score 0.6–1.4 points higher than any layout the engine now produces. This is a known trade-off;
the fix would be to drop row siblings together.

Agreement with the labels held: pairwise 0.892, AUC 1.00 (unchanged).

## 16. Sibling groups, scale, left edges

- **Siblings** (`eval.score.siblings`): a row of similar units, such as badges or buttons.
  - Membership: at least 2 units, each holding a shape or image, with the same member types.
  - They must have heights within 1.25× of each other and sit side by side in one row.
  - Gaps must be under their average width, with nothing else between them.
- **Emphasis within a group:** in a group of three or more, the one sibling whose colour differs from the others is the emphasised one, even when it is dark or light; the others are not.
  - The others must agree among themselves (ΔE < 15), and the odd one must be at least ΔE 35 from them.
  - A uniform group falls back to the palette rule. Units outside groups keep the palette rule.
  - In L3 the dark "AWARD WINNING" badge is now the emphasised one, not the orange badges.
- **Engine:** `analyze._merge_siblings` turns a group into one rigid unit. It is scaled, moved and demoted as one piece and never split.
  - If a sibling sat on the design's centre axis, the row's box is padded to be symmetric about that axis, so centring the row keeps the axis.
  - Cost: on tall canvases with a high readable minimum (Instagram Story/Post), the row no longer wraps into a readable stack. It shrinks as a whole, below the readable size (small_text 0.15–0.17).
- **Scorer:**
  - `siblings` penalty: 0.5 if the members are no longer one row with nothing between them, plus 0.5 if their scales differ by more than 10%.
  - `scale` penalty: the headline and the hero image, each judged against the scale the target affords (the square root of the area ratio, or less when the unit would not fit at that scale). None at 1.0×, full at 0.4×.
  - Alignment: a source-aligned pair that went from stacked to side by side, or back, is no longer counted as lost. Rotated units are left out of near misses.
- **Left edges:** in left-aligned columns the engine now lines up what is drawn with the column edge, not the box. Before, centred text in its slightly wider box and letterboxed images started 10–15px in, which read as ragged edges and near misses.
- **Presentation 16:9 (L3):** in the last round, two stacks were nearly tied: a bigger bottle with smaller text, or the reverse.
  - The scorer had no view on size and the tie flipped.
  - With `scale`, the transposition rule and straight left edges, the split (bottle left, text column right) wins. Both the text and the bottle are bigger.
- **Calibration** (52 labelled outputs):

  | weights | pairwise | within design | AUC |
  |---|---|---|---|
  | Current | 0.863 | 0.837 | 0.951 |
  | Leave-one-design-out (within design) | | 0.842 | |

  - The labels are indifferent to the scale thresholds (0.8–1.0 all give 0.863–0.864).
  - 1.0 was chosen because it makes the split win where it is clearly better by eye.
- **Restacking (follow-up):** a sibling row whose text would fall below the readable minimum may now rearrange into a grid or a single stack (`Sizer.arrangements`).
  - The grid keeps the row's gaps, centres each line, and keeps all members at one scale.
  - The row is used whenever it stays readable.
  - Scorer: a compact stack or grid with nothing in it costs 0.25 (`SIBLING_RESTACK`). Members spread apart (union box over 2× their area, or looser than in the source) or with anything between them count as split (0.5).
  - Agreement: 0.868 pairwise, good-vs-bad 0.953.
  - Instagram Story and Post are readable again. LinkedIn Banner and Wide Skyscraper score 1.5 points lower: a readable stack costs more than the unreadable row it replaced.

## 17. Crello test set (branch `crello`)

### Conversion (`eval/crello_convert.py`)
- **Input:** the three validation shards hold 1,852 designs. 1,794 converted; 58 were skipped:

  | reason | designs |
  |---|---|
  | text our two fonts can't draw (mostly Cyrillic) | 40 |
  | fewer than 3 elements | 12 |
  | more than 40 elements | 3 |
  | no text | 3 |
  | conversion errors | 0 |
  | schema violations | 0 |

  Every converted design passes the v0.9 schema.
- **Where things live:**
  - Output goes outside the repo, to `../data/crello_chameleon/` (`$CRELLO_CHAMELEON`): designs, PNG crops, previews and comparisons.
  - The renderer, scorer and engine find assets through `$CHAMELEON_ASSETS` (`eval.render.assets_dir()`). It defaults to `brand_kit/assets`, so Docker is unchanged.
  - Nothing from Crello is committed. Only `cases.csv` and `summary.md` of the Crello suites are, and they hold ids and numbers only.
- **Fonts:** each Crello family maps to Solstice Serif (serif and slab faces) or Solstice Sans (everything else). The mapping is in `eval/crello_fonts.json`.
  - Our sans is wider than Crello's condensed display faces (Bebas Neue, Oswald...). So 2,270 of 7,594 texts had their font size reduced until they wrap to Crello's own line count. The median factor was 0.84; 167 hit the 50% floor.
- **Images:**
  - An image that fills the canvas is `cover`; every other image is `contain`, so the checker's image-proportion rule applies.
  - Bleeding unrotated images are cut to the canvas, pixels included.
  - Rotations under 0.5° are treated as editor noise and become 0.
- **Visual check:** 20 conversions were rendered next to Crello's previews (`compare/_sheet.png`). Layout, colours, images and rotation match; the only differences are the substituted fonts.

### Test set (`eval/crello_testset.py`, `eval/crello_testset.json`: ids and sizes only)
- 300 designs, drawn round-robin over (format, element-count band, aspect band) buckets, covering 60+ formats, 3–40 elements, and aspect ratios 0.3–8.1.
- Each design is paired with 3 random catalogue sizes, never its own size.
- The split is by design:
  - **Dev:** 200 designs, 600 cases.
  - **Holdout:** 100 designs, 300 cases. Holdout is only ever run to check for overfitting; never tune on it.
- **Bench:** `python -m eval.bench --suite {samples,crello-dev,crello-holdout} [--render] [--jobs N]`.
- **Review page:** `python -m eval.review_server --results eval/results/crello-dev --worst 30`. Crello labels stay in that folder and are gitignored.

### First crello-dev run (engine `d7352fe`, no engine changes)

| measure | result |
|---|---|
| Pass rate | 589/600 (98.2%) |
| Average score | 90.17 (the samples suite: 95.78) |
| Crashes | 0 |
| Fallbacks | 0 |
| Failed layout candidates | 0 |

- **Failures:**
  - **`hidden_element`, 8 cases (13 elements):** full-width 1–2px hairline images scaled below 1px. Decorations are placed without the 1.5px minimum the other paths use.
  - **`background_not_full_canvas`, 3 cases (one design):** a full-canvas photo rotated 180°. The engine only recognises unrotated backgrounds.
- **Timing:**
  - Sequential, 30 cases: mean 2.2 s, median 1.7 s, max 7.6 s.
  - In the 8-process run: mean 3.7 s, p95 10 s, max 17.6 s.
  - Larger designs are slower: candidates × text layout.
- **What breaks, by eye (worst 30):**
  - Text on an image card or bubble (an SVG speech drop, paper card or photo frame) is separated from it: the engine only treats shapes as containers. Cards end up empty and text floats free.
  - Big photos that don't fill the canvas are not treated as background: they shrink, and text shrinks with them on wide banners.
  - Multi-column grid designs (storyboards, menus) collapse into one long column.
  - `floating` (0.40) and `scale` (0.25) are the largest mean penalties.

## 18. Crello fixes, measured on crello-dev

### Agreement with the Crello labels (worst 30)
- Before this round: pairwise 0.806, good-vs-bad 0.80; the samples are at 0.868 / 0.953.
- **Where it agrees:** all 19 passing cases scoring under 78.5 were labelled bad.
- **Where it disagrees:** on the 11 cases that broke a hard rule. They scored 79–98 because the score ignores rules (e.g. an unfilled background still scored 94–96).
- **New check:** "text leaves its card" (`holders`), added because of these labels. It raises Crello agreement to 0.829 / 0.88 and leaves the samples unchanged.
- **Caveat:** only 1 of the 30 is labelled good.

### Fixes (general rules, no design ids)
1. **Rule lines and turned backgrounds.**
   - Any non-text element at most 4px thick and 10× longer is a decoration. It is never pulled into a group, and is placed at least 1.5px thick when that still fits the canvas.
   - Backgrounds turned by a multiple of 90° are recognised. At 180° they fill the canvas.
   - At 90°/270° on a non-square canvas, filling would push the unrotated box off the canvas (the official self-check tests the box). So they fill the centred square, and our checker no longer asks the impossible.
   - The converter snaps rotations within 0.5° of a right angle.
2. **Text on images.** An image holds the text on it as one rigid group when it is:
   - compact (at most 4:1), and
   - under 20% of the canvas, or under 50% and flat (RGB std < 25: a card or bubble, not a photo).

   A photo inside a frame image is also one group. The thresholds were measured against the 50% limit first tried, which turned photos with a headline on them into rigid "cards" (−1.26).
3. **Big hero.** A photo covering at least 25% of the design gets the `anchor` recipe:
   - it keeps its share of the canvas, flush against one edge (at most 65% of the width or height);
   - the text is a column in the space left;
   - the photo is never demoted.

   An image-only group (a photo in a frame) now counts as an image for roles. Before, it fell through to a floating "decoration".
4. **Grids.** A grid needs at least 4 similar image units (width and height within 15%) on a lattice of at least 2×2.
   - The other units join the cell whose band they fall in. A band starts or ends at its photo, whichever gives the most even cells.
   - Each cell becomes rigid and the grid becomes one unit. It can re-flow to any column count, taking the shape closest to the canvas first.

### Results (crello-dev, 600 cases; "before" is engine d7352fe on the same conversion and scorer)

| | pass | average |
|---|---|---|
| before | 589 | 87.28 |
| after | 592 | 89.72 |

Leave-one-out (the score without each fix; full set 89.72):

| without | average | worth |
|---|---|---|
| image cards | 87.29 | +2.43 |
| frames | 89.62 | +0.10 |
| grids | 89.72 | 0 |
| anchor | 89.44 | +0.28 |

- **Grids** touch only 4 designs (11 cases: 5 better, 6 worse by the scorer). The storyboard is clearly better by eye.
- **Anchor:** 115 cases better, 2 worse.
- **Remaining failures:** 8 cases (13 elements), all `hidden_element`. 11 of the 13 are hairlines that can't be ≥ 1px within the canvas without breaking their proportions. The other 2 are thin parts of a larger group squeezed into a 90px leaderboard.
- **Holdout (run once):** 295/300 (98.3%), average 89.39, against dev's 98.7% / 89.72. No sign of overfitting. All 12 of its hidden elements are the impossible-in-proportion kind.
- **Samples:** outputs identical (0 of 45 changed), 96.15 under the current scorer.
- **Synthetic:** 299/300, 0 crashes; same as before.
- **Still poor by eye:**
  - A tall text column on a wide banner shrinks to unreadable; it needs multi-column text flow.
  - A large flat card (86% of the Love poster) still ends up empty beside its photo.

## 19. Text columns and oversized panels; Docker re-check

### Fixes (general rules, no design ids)
1. **Columns.** `solve_column` tries 2 and 3 columns when both of these hold:
   - the text box is at least 1.5× wider than tall;
   - one column hits the readable floor: something was demoted, or some flowing text is at its minimum size.

   The units go in reading order down each column, columns left to right. The cut points give the most even column heights.

   Columns win when they demote fewer units, or raise the shared scale by at least 15%. A single text element is never split; it takes its column's full width, so it wraps into fewer lines instead of shrinking.

   I chose newspaper order over filling row by row because rows split each name from its subtitle (VAGANZO | OKLAHOMA) into different columns. The scorer accepts both orders.
2. **Panels.** A panel is a flat shape or flat image with text on it that is:
   - too big to be a card (`_holder` fails on size alone);
   - compact (at most 4:1; a long bar is a backdrop the text reflows over);
   - unrotated, and not off the canvas.

   It leaves the layout and is fitted around wherever its content lands: the content's box plus the source padding, scaled like the content. A non-cover image keeps its aspect, as the `image_aspect` rule requires (105 of 107 such panels on dev are `contain` images), and it never grows larger than the canvas.

   Two narrower versions came first:
   - **Any content, not just text:** −0.31. An illustration with a cloud on it became a "panel", blew up to its aspect and covered the headline.
   - **Long bars allowed:** −0.18.

### Results ("before" is 5c5316c)

| | before | after |
|---|---|---|
| crello-dev pass | 592/600 | 592/600 |
| crello-dev average | 89.72 | **89.85** |
| crello-holdout pass (run once) | 295/300 | 295/300 |
| crello-holdout average | 89.39 | **89.55** (43 better, 25 worse) |
| samples | 45/45, 96.15 | 45/45, 96.26 |
| synthetic | 299/300 | 299/300 |

- **On dev:** columns alone give 89.80; panels add a further +0.05 (64 cases better, 40 worse).
- **Remaining failures:** all are hidden hairlines, as before.
- **By eye:**
  - Football banner: 78.71 → 95.34; all its text is readable, in 3 columns.
  - Sacramento: the panel follows its text instead of staying an empty purple block.
  - Herbs circle: worse. Its text is split up by the layout, and the fitted circle covers a herb sprig. Fixing that needs the text laid out inside the panel.
  - Love poster: unchanged. Its panel holds a photo, not text.

### Docker (image `chameleon-engine`, 304 MB, built in 188 s; `--network none`, amd64 emulated on Apple silicon)
- **All 45 samples:** 172 s in total, every self-check OK.
  - Per case: median 3.41 s, mean 3.53 s, slowest 9.40 s (L3 leaderboard).
  - By level (median / max): L1 1.81 s / 3.69 s; L2 3.36 s / 5.03 s; L3 5.38 s / 9.40 s.
- **Outputs are not byte-identical to native** (2/45 are).
  - Same fonts, fields and sizes everywhere; 38 cases differ only by small moves.
  - 5 cases pick a different candidate. This is the known ~1% CoreText/FreeType glyph-width difference (section 12): text boxes measure differently, so ties between candidates break differently.
- **What matters holds:**
  - native outputs pass `check()` inside Docker (45/45, 95.51 scored there);
  - Docker's outputs pass natively (45/45, 95.83 scored natively);
  - each platform's own outputs score 96.26 (native) and 96.15 (Docker).
- **Docker Desktop's disk image** is now on the external drive, which is exFAT: no sparse files, so `Docker.raw` takes its full size (228 GB).

## 20. Layout library and retrieval (branch `retrieval`)

### Library (`eval/build_library.py` -> `engine/data/layout_library.json`)
- **Contents:** our analyzer runs on every converted Crello design outside crello-dev and crello-holdout, giving **1,494 layouts** (9,836 units) in **0.77 MB**.
- **Per layout:** the aspect ratio; per unit, its role, kind (text/image/rigid) and box as fractions of the canvas; role counts.
- **Left out:** text, pixels and ids. The list is ordered by aspect.
- **Coverage:** every dev and holdout target has at least one layout within the aspect tolerance; 115 of 600 dev targets have fewer than 30.

### Retrieval (`engine/retrieve.py`)
- **Selection:** library layouts within |ln aspect| <= 0.2 of the target, ranked by role-count L1 distance to ours (ties go to the closer aspect). The top 30 are used.
- **Mapping:** our flow units go to their slots by a minimum-cost assignment (Hungarian, numpy only, tested against brute force).
  - The cost adds role (same 0, same family 0.6, other 1.5), kind (text into a non-text slot +1), size (0.5 |ln area-share ratio|) and, for fixed-aspect units, 0.5 |ln aspect ratio|.
  - A unit whose best slot costs more than 2.5 goes to free space (engine.fit's floating placement); unused slots are ignored.
  - **Never into a slot where it would be unreadable:** text that can't fit a slot at its readable size, or a group whose text would fall below readable size there.
- **Sizing inside a slot:** the same Sizer as the recipes, with the same scale caps (`k_cap(1.2)`, 1.4x that for images). Without the caps a short title grew 3.2x into a big headline slot.
- **Selection:** unchanged. `resize` logs `winner: <recipe>` at INFO, and `eval.bench` records it in a new `winner` column.
- **Panel fix found on the way:** `place_panel` now uses an even padding (the source's tightest side) scaled like the content's own scale (font or width ratio).
  - Before, it kept each side's padding scaled by the content's area, so a title at the top of a big panel kept the empty bottom.
  - Neutral on dev: 89.85 -> 89.85, 27 cases better and 31 worse.
  - The panel test from §19 had an invalid shape (`shape`/`fill` instead of `shape_type`/`fill_color`), so every candidate failed `missing_field`. It passed only via the repair path; it is fixed now.
- **Speed:** the first version took 265 s on one case, because the slot-feasibility test measured text the slow way (font stepped down 1px at a time, plus a 40-width search for letter-spaced text). It is now a direct "fits at readable size" test.

### Results

| | v1-submittable | + retrieval |
|---|---|---|
| crello-dev pass | 592/600 | 592/600 |
| crello-dev average | 89.85 | **91.31** |
| crello-holdout pass (run once) | 295/300 | 295/300 |
| crello-holdout average | 89.55 | **90.88** |
| samples | 45/45, 96.26 | 45/45, 96.57 |
| synthetic | 299/300 | 299/300 |

- **How often retrieval wins:** dev 263/600 (44%, in 144 of 200 designs; on those cases 254 better, 9 worse). Holdout 141/300 (47%; against v1, 146 cases better and 7 worse).
- **Runtime per case** (native, 8 workers in parallel):
  - dev: median 4.1 s -> 5.8 s, mean 5.2 -> 6.9 s, p95 12.9 -> 17.4 s, max 30.2 -> 32.7 s;
  - holdout max 58 s.
- **By eye (not by score):** the top 8 changed cases are mixed.
  - Better: Sangria x2, the storyboard, "Best value".
  - Worse: the Beauty email header (headline shrinks to a corner), the Health Matters banner (photo nearly gone, logo block dominates), the apartment poster (photo a sliver beside an empty panel).
  - Mixed: one.

  The scorer calls 29 of the top 30 better (+3.69 on average). Its verdict on retrieved layouts needs hand labels before we trust it. The 30 are on the review page (`eval/results/crello-retrieval-review`, middle column = same engine without retrieval).

## 21. Key-content penalty, retrieval guard, time budget (branch `retrieval`, not merged)

### Labels on the 30 retrieval cases (§20)
- **Verdicts:** 28 bad, 1 okay, 1 good.
- **The old scorer barely agreed:** pairwise 0.632 (0.5 = chance), AUC 0.39 (the one good case scored below most bad ones). It scored the bad cases at up to 98.2.
- **What separates the labels best** (all 105 labels: 45 samples, 30 crello-dev, 30 retrieval) is the main image's share of the canvas against the source's:
  - good: median 1.06, none below 0.5;
  - bad: median 0.52, half below 0.5.

  Next comes the headline's share: good median 1.42, bad 0.88.

### Scorer: `key_size` (eval/score.py)
- **What it measures:** the headline (biggest-looking text) and the main image (largest non-background image, alone or in a group; the old `scale` penalty only saw single-image units).
- **How:** each one's scale against what the target affords. Free at 0.85 or more, full at 0.5 or less, rising fast in between. A cover-cropped main image whose box aspect fell below 0.6 of the source's also counts.
- **Penalty:** the worst of these. Decorations aren't measured.
- **`key_elements()`** is shared with the engine's guard.

### Weights
Refitted on all three label sets together (`eval.calibrate --fit --suite samples,crello-dev,crello-retrieval-review`, which can now take several sets at once).

| key_size weight | samples | crello-dev | retrieval | all |
|---|---|---|---|---|
| 0 | 0.868 | 0.829 | 0.632 | 0.856 |
| 1 | 0.835 | 0.853 | 0.754 | 0.855 |
| **2 (chosen, with the refit)** | 0.820 | 0.868 | 0.789 | 0.850 |

- **Why pinned:** the free fit leaves `key_size` at its floor (pooled 0.862) because the sample labels pull the other way.
- **Why 2.0:** it agrees best with the Crello and retrieval labels, at a cost of 0.05 on the samples and 0.01 pooled. emphasis stays at 0.95, as requested earlier.
- **Test change:** the calibration test's threshold for the samples moves from 0.84 / 0.94 to 0.80 / 0.90.

### Engine
- **Guard** (`resize._guard`): a retrieved layout is dropped if the headline's or the main image's drawn share of the canvas falls below 0.7 of what the best-scoring passing recipe layout gives it.
- **Budget** (`resize.BUDGET_S = 15`): checked between recipe plans, between retrieved layouts, between realisations and between contrast renders. Past the deadline nothing new is made or rendered, and the best so far is chosen.
  - Without the render check, one case took 38 s under load: 10 contrast renders at about 1.1 s each on a 1080x1920 canvas.
  - The test sets a 0 s budget, and the output is still valid.
- **Missing library:** `library()` returns [] and the recipes alone run. Tested: the output is valid, no errors are logged, and the winner isn't a retrieved layout.
- **Bench columns:** `budget_hit`, `guard_dropped`.

### Results (v1 outputs rescored with the current scorer, so both are judged the same way)

| | v1-submittable | current |
|---|---|---|
| crello-dev | 592/600, 85.98 | 592/600, **90.45** (362 better, 27 worse) |
| crello-holdout (run once) | 295/300, 85.45 | 295/300, **89.90** (186 better, 10 worse) |
| samples | 45/45 | 45/45, 96.83 |
| synthetic | 299/300 | 299/300 |

- **Retrieved layouts win:** dev 304/600, holdout 148/300.
- **Budget reached:** dev 35 cases, holdout 23.
- **Native runtime** (8 workers): dev median 6.5 s, p95 15.2 s, max 18.3 s; holdout max 22.8 s.
- **Docker** (amd64 emulated, `--network none`): all 45 samples pass, average 96.71.
  - Total 350 s, against v1's 167 s.
  - Per case: median 8.2 s (L1 2.4 s, L2 9.0 s, L3 11.2 s), slowest 18.0 s (L3 leaderboard).

### By eye: not merged
`eval/results/crello-retrieval-review-2` holds the 30 dev cases that changed most against v1 (middle column = v1).
- **Better:** Australia, Capsule wardrobe, Perfect hideout, Internships, Kindest Heart, Big Sale.
- **Still bad, as labelled in §20:** Beauty header (headline small), Apartment (photo a sliver), Sangria, Health Matters.
- **Worse:**
  - Anti-frizz: the headline sits on top of the bamboo.
  - Self care: body text runs over the photo.
  - Warme Dusche: the headline shrank.

The scorer and the selection it drives now share the same blind spots. So the merge condition ("looks better by eye") isn't met: main stays at v1-submittable.

## 22. Text newly over images; retrieval switch; v2

### Text newly over an image (eval/score.py)
- **`text_over_image` penalty:** per text, the share of its drawn box newly covered by non-background images (output share minus source share, summed over images, capped at 1). 0.05 is free, 0.5 is full; the worst text sets the penalty.
- **Weight 3.0, pinned:** the free fit gives 0.63. Agreement on the retrieval labels rises with the weight and plateaus at 3: 0.789 (weight 0) -> 0.825. Samples and crello-dev don't change; pooled 0.851 -> 0.857.
- **Rejection:** `busy_text_over_image` rejects a candidate when a text newly sits 20% or more on one image and that image's pixels under it are busy: mean |gradient| > 0.02 on 0-1 grey, measured on the asset through its fit, with transparent pixels counting as flat. `engine.select` drops such candidates unless all are like that.
- **Why 0.02:** text that designers put on images measures median 0.000 and 75th percentile 0.008 (400 sources). The overlaps judged bad by eye measure: anti-frizz headline on bamboo 0.035, "SELF CARE" on a photo 0.057, storyboard captions on photos 0.20-0.28.
- **Switch:** `CHAMELEON_RETRIEVAL=0` turns retrieval off (tested). It is read on every call, so `docker run -e` works.

### Results, both ways (v1 = v1-submittable outputs rescored with the current scorer)

| | v1 | retrieval on | retrieval off |
|---|---|---|---|
| crello-dev | 592/600, 87.64 | 592/600, **90.92** (346 better, 29 worse) | 592/600, **88.76** (179 better, 32 worse) |
| crello-holdout (once per mode) | 295/300, 87.46 | 295/300, **90.78** (183 better, 10 worse) | 295/300, **88.67** (94 better, 15 worse) |
| samples | 45/45, 96.82 | 45/45, 97.49 | 45/45, 97.36 |
| dev native runtime (8 workers) | | median 5.8 s, p95 14.1 s, max 21.9 s | median 3.8 s, p95 11.6 s, max 16.6 s |
| Docker, 45 samples, offline | 167 s | 272 s (median 5.0 s, max 15.1 s) | 177 s (median 3.6 s, max 10.4 s) |

- **Retrieved layouts win:** dev 264/600, holdout 126/300.
- **Budget reached:** retrieval on: dev 20 cases, holdout 14. Retrieval off: dev 4, holdout 6.
- **Average `text_over_image` on dev:** v1 0.060, on 0.035, off 0.037. Average `key_size`: v1 0.365, on 0.179, off 0.300.

### By eye (the 30 dev cases that changed most against v1, per mode)
- **Retrieval on** (`eval/results/crello-review-retrieval-on`): about 18 better, 3 worse, 9 the same.
  - Better: storyboard, Australia x2, Save 10%, Capsule wardrobe, Perfect hideout, Warme Dusche x2, Beauty portrait, Internships, Kindest Heart, Green Party, Ocean x3, Paris.
  - Worse: Fashion Talks x2 (a big circle crowds out the photo), Beauty email header (slightly).
  - Still poor in both: Apartment, Sangria, Health Matters.
- **Retrieval off** (`eval/results/crello-review-retrieval-off`): about 9 better, 3 worse, 18 the same.

### Decision
All three conditions hold: dev and holdout beat v1 in both modes, and the retrieval-on review shows clearly more better than worse. `retrieval` is merged into main and tagged **v2**, with retrieval on by default. `CHAMELEON_RETRIEVAL=0` gives recipes only.

The organisers still haven't confirmed that shipping a geometry-only library derived from Crello is fine (assumption 3, §8).

## 24. Preserve-first candidates, share drift (branch `preserve`, merged as v3)

### Labels on the 30 structure cases (§23)
- **Verdicts:** 27 bad, 2 okay, 1 good.
- **Agreement:** the scorer agrees pairwise 0.807 (AUC 1.0: the good case scored highest), but it rated most of the bad cases 80-90.
- **All 135 labels:** 0.863.

### What was built (from main v2; structure's `relations()`, relationships penalty and structure suite brought over, its block tree in the recipes not)
- **`engine/preserve.py`:** CP-SAT, single-threaded, fixed seed, 0.5 deterministic seconds per variant.
  - Items: units joined by strength-1 relations (at most 60% of the canvas).
  - Variables: x, y and a scale per item. Width and height follow the scale exactly.
  - Hard constraints: inside the canvas; readable text; a large item (10% of the source or more) keeps at least 0.7 of its share-keeping scale; no new overlap between items that didn't overlap in the source (4-way disjunction).
  - Objective: share-weighted |move| + |resize| (shrinking costs 3x), plus penalties for a changed left/right or above/below order and for broken shared edges.
  - Variants: share, fit, edges, between.
  - Dependency: `ortools==9.12.4544`, chosen over scipy for its native disjunctions and deterministic limits. The image is 331 MB (+27 MB).
- **Share drift (`eval.score`):** each element's canvas share against the share it can keep (its source share; less for an image whose aspect can't fill that much of the target). Weighted by source share. **Shrinking only:** penalising growth as well agreed less with the labels (pooled 0.849 vs 0.867), which favour an enlarged headline or product.
- **Large-share floor:** select drops candidates that leave an element of 10% or more of the source with under half the share it can keep, unless every candidate does.
- **Weights** (all 135 labels): share_drift 1.0, relationships 0.5.
  - Pooled agreement 0.864 -> 0.867; crello-dev 0.876 -> 0.938.
  - Costs: samples 0.820 -> 0.805, structure labels 0.807 -> 0.783 (calibration test threshold 0.79).
- **Budget:** 14.5 s in all, in three stages.
  - Generation stops at half of it.
  - Realising stops while the rest still covers judging every candidate made (4x the measured per-candidate check+score).
  - Contrast renders stop at the deadline.
  - Why: with a plain 13.5 s generation budget, one Docker case still took 16.4 s, because judging 100 candidates under emulation took 3.6 s.

### Results (v2 outputs rescored with the current scorer; final code fd055f9)

| | v2 | v3 |
|---|---|---|
| crello-dev score | 88.74 | **89.24** (232 better, 73 worse) |
| crello-holdout score (once) | 88.60 | **89.20** (102 better, 24 worse) |
| structure suite score | 83.80 | 82.49 (34 better, 29 worse) |
| relationships kept dev / holdout / structure | 40.7% / 42.2% / 50.3% | **59.7% / 53.5% / 62.2%** |
| largest element's share ratio (median) dev / holdout / structure | 0.80 / 0.81 / 0.71 | **0.84 / 0.86 / 0.79** |
| largest element under half its share, dev / holdout | 151 / 68 cases | 131 / 58 |
| samples | 45/45, 96.85 | 45/45, 97.21 |
| synthetic | 299/300 | 299/300 |
| Docker 45 samples | | 278 s, median 5.3 s, max 12.8 s, none over 15 s |

- Pass counts are unchanged (592/600, 295/300, 118/120).
- **Native runtime** (8 workers sharing the CPU): dev median 6.3 s, max 16.3 s.
- **Winners by aspect change** (dev, |ln aspect ratio| buckets):

| aspect change | cases | preserve | retrieved | recipes | uniform | repaired |
|---|---|---|---|---|---|---|
| same (< 0.1) | 48 | 12 | 7 | 11 | 18 | 0 |
| moderate (0.1-0.5) | 161 | 61 | 38 | 59 | 0 | 3 |
| large (0.5-1.2) | 243 | 57 | 74 | 110 | 0 | 2 |
| extreme (> 1.2) | 148 | 12 | 52 | 76 | 0 | 8 |

  Holdout has the same pattern: preserve wins 26 of 78 moderate changes and 7 of 91 extreme ones.
- **By eye** (30 most changed vs v2, `eval/results/crello-review-preserve`): about 15 better, 6 worse.
  - Better: Save 10%, Pharmacy, Health Matters, Ocean x3, Office, Apartment x2, Fashion Talks, Family festival, Menu, Bowling.
  - Worse: storyboard, Capsule wardrobe, Marmillon, Warme Dusche, South American birds, Howard Love.
- **Not fixed:** white text half off its dark backdrop (South American birds, Summer coffee). Both come from recipe or retrieved winners and also happen in v2. Next: reject a candidate when a text that sat fully on an element now sits mostly off it.

### Decision
Dev and holdout both beat v2, and by eye it is clearly better: merged into main and tagged **v3**.

## 25. Faster iteration loop (tooling, on main)

- **Quick suite** (`crello-quick`, `eval/crello_quick.json`, `build_quick`): 100 crello-dev cases, a share of each of 16 strata (4 aspect-change buckets x 4 element-count bands, at least 2 each), fixed seed.
  - `python -m eval.bench --suite quick --jobs 8` runs it, then the 45 samples.
- **Snapshots** (`eval/snapshots.py`): outputs of earlier versions, stored once in `cache/snapshots/<version>/<suite>/` next to `data/` (Crello content, never in git).
  - Their scores are computed once per scorer (hash of `score.py` + `check.py`) and kept beside them.
  - `compare` diffs a fresh run against them without regenerating anything.
  - v3 is stored for dev, structure, holdout, quick and samples (1,165 outputs; scoring all of them once took 22 s).
- **Timings** (idle Mac, 8 workers):

| Run | Time |
|---|---|
| quick suite | 122 s (87 s Crello + 34 s samples) |
| snapshot compare | under 1 s |
| crello-dev | 553 s |
| crello-holdout | 310 s |
| crello-structure | 142 s |
| Docker build + 45 samples | about 5-6 min |

  - A pre-merge round (dev + structure + holdout + samples + Docker) is about 23 min, against 60-70 min when baselines were regenerated every round.
- **Noise floor:** the same code run twice changed 2 of the 100 quick outputs (-0.32 average). The time budget cuts at different points under different load, so differences that small are noise.
- **Process:** quick suite + snapshot compare while iterating; full suites and the Docker check only before a merge; with/without switches only on request.

## 26. Legibility rules (branch `contrast`, not merged); extreme shape changes on v3

### Rules
- **Backdrop rule:** a text that sat at least 95% on an element (its smallest non-text, non-background backdrop) must stay at least 90% on it.
- **Contrast rule:** a text's contrast must not fall below half the source's and below 3:1. Contrast is estimated without rendering: the layers under the text's box are composited at 32x8 points, images sampled from their assets through their fit, and the 25th percentile of the WCAG ratios is taken. Against real renders: log correlation 0.93, 95% agreement on whether a text is under 3:1, 8 ms per design.
- **Selection:** tiered, so the filters no longer trap each other: legible first, then not on a busy image, then large elements keep their share. If nothing is legible: fewest texts that lost contrast, then the other tiers, then mean contrast kept.

### Results
- **As specified** (full suites; v3 = the same engine without the rules): dev 89.28 -> 86.77, holdout 89.18 -> 86.51, structure 82.74 -> 79.38, samples unchanged. Docker: 45/45, slowest 13.1 s.
  - The rules fired in 358 of 600 dev cases (87 with no legible candidate) and changed 174, of which 171 scored worse (-8.2 each).
  - In v3's own outputs, text leaves its backdrop in 157 dev cases but contrast is lost in only 72. Almost every backdrop left is a large image (40-100% of the canvas): photos and illustrations, where leaving them usually doesn't matter.
- **Narrowed:** the backdrop rule only for compact backdrops (under 40%: cards, labels, panels); contrast still guards the rest. Quick suite: 90.12 -> 88.24. The rules changed 17 cases (plus 2 from timing noise); the scorer calls all 17 worse.
- **By eye** (`eval/results/crello-review-legibility`): about 7 better, 3 worse.
  - Better: Lumos fashion (text back on its card), Circus, Valentine's (button label back), Makeup notes, Day of forests, Ocean, Pharmacy.
  - Worse: Best value x2 (a poor fallback when nothing is legible), Fresh smoothie.
- **Why the scorer disagrees:** `eval.bench` scores without the contrast penalty (it renders, so it's off by default), so the benchmark doesn't see white-on-white at all, and it does see the alternatives' smaller images.

### Decision
Not merged: dev and holdout drop. Next: a cheap contrast penalty in the default score (the no-render estimate), so the benchmark sees the failure the rules fix, and a better fallback than "best contrast" when nothing is legible.

### Extreme shape changes on v3 (crello-dev, from the v3 snapshot)

| aspect change | cases | average | pass | most frequent winners |
|---|---|---|---|---|
| same (< 1.1x) | 48 | 90.63 | 48 | uniform, preserve |
| moderate (1.1-1.65x) | 161 | 90.66 | 159 | preserve, retrieved, stack |
| large (1.65-3x) | 222 | 89.18 | 222 | retrieved, preserve, stack |
| **extreme (>= 3x)** | **169** | **87.71** | **163** | retrieved 60, stack 41, preserve 16 |

- **Points lost per case,** extreme vs the rest: key_size 3.24 vs 1.89, small_text 0.58 vs 0.23, relationships 1.43 vs 1.10, space 0.34 vs 0.15, reading_order 0.58 vs 0.40.
- **10 worst** (score, case, source -> target aspect, winner):

| score | case | aspect | winner |
|---|---|---|---|
| 50.8 | CV (Maya Rouge) | 0.71 -> 8.1, leaderboard | stack |
| 51.4 | CV (Howard Love) | 0.71 -> 4.0, LinkedIn | stack |
| 54.3 | Smart Cities | 3.0 -> 1.0 | preserve |
| 57.7 | pistaliar sale tag | 1.0 -> 8.1, leaderboard | split |
| 63.0 | Travel Gear | 1.78 -> 8.1, leaderboard | retrieved |
| 63.1 | pistaliar | 1.0 -> 0.27, skyscraper | anchor |
| 67.3 | Save 10% | 3.0 -> 0.27, skyscraper | stack |
| 68.4 | Dessert | 0.71 -> 3.0, email header | strip |
| 70.6 | Invoice | 0.71 -> 3.0, email header | stack |
| 71.2 | The Ocean | 0.5 -> 1.78, X post | anchor |

- **What goes wrong:**
  1. **The canvas stays mostly empty:** Smart Cities, both pistaliar, Save 10%. Rigid groups (a price tag, a photo with its frame) and aspect-locked images can't grow into a canvas of the opposite shape. Nothing reflows to use the length, so the design shrinks to a small cluster.
  2. **Photos lose their subject:** Travel Gear 1.78 -> 8.1 shows only a thin centred band (faces cut). Pistaliar's knit photo is a small fragment. The renderer's centred cover crop and the image aspect lock leave no other option.
  3. **Text-heavy documents into banners:** CVs and the invoice. Columns, tables and panels are torn apart or crushed, and body text drops to the minimum. These have more text than a 728x90 strip can hold readably, and nothing may be removed.
  4. **The scorer may be harsh:** Dessert and Ocean look reasonable but score about 70. key_size measures the headline by area share, which a headline can't keep on a 3:1 or 8:1 strip, so part of that penalty is unavoidable there.
- **Failures:** 6 of the 8 dev failures are in this bucket, all hidden hairlines (as before).
