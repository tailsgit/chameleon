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

## 8. Crello dataset (`cyberagent/crello` on Hugging Face). Not downloaded yet

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
