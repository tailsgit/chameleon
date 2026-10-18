# CHAMELEON — layout-aware resizing engine

Given a design (a JSON list of text, image and shape elements on a canvas) and a target canvas
size, the engine returns the same design re-laid-out for the new size. It moves and scales the
existing elements, picks new font sizes, and never adds, removes, rewrites or redraws anything.

A naive resize stretches the picture; this engine moves the furniture. It works out what the
design is made of (background, headline, hero photo, logo, call to action, groups that belong
together, reading order), generates many candidate layouts for the target shape (from layout
recipes, and from the layouts of real designs of a similar shape), measures every text box with
the renderer's own text layout, and keeps the candidate that breaks no rule and scores best.

```
input/<task>.json  (source design + target_canvas)
        |
        v
  analyze  ->  recipes  ->  fit  ->  select          engine/resize.py: resize()
        |
        v
output/<task>_output.json   (resized design, same schema)
output/<task>_output.png    (rendered with the bundled renderer)
```

No machine-learning model, no network access at run time, no generated pixels. Pure Python on
top of the provided renderer, plus a 0.8 MB library of layout geometry; the Docker image is
about 300 MB.

## Results

Measured with our own checker and scorer (`eval/`, described below), not the official ones.
Retrieval (see How it works) is on by default; the right-hand column is the same engine with it off.

| Test set | Cases | Pass every hard rule | Average score (0-100) | Retrieval off |
|---|---|---|---|---|
| The 3 provided samples x 15 real platform formats | 45 | 45 (100%) | 97.5 | 97.4 |
| 200 real designs from the Crello dataset x 3 formats (development set) | 600 | 592 (98.7%) | 90.9 | 88.8 |
| 100 further Crello designs x 3 formats (held out) | 300 | 295 (98.3%) | 90.8 | 88.7 |
| 300 random synthetic designs | 300 | 299 | – | – |

For comparison, a uniform stretch passes 1 of the 45 sample cases. Every remaining failure is a
hairline (a line 1-3 px thick) that cannot stay at least 1 px thick without breaking its
proportions on a much smaller canvas; see Known limitations.

Docker, `linux/amd64` emulated on Apple silicon, `--network none`: all 45 sample cases in
272 s, median 5.0 s per case, slowest 15.1 s (retrieval off: 177 s, median 3.6 s, slowest
10.4 s). A time budget keeps every case to about 15 s; see Select.

## Run it

### Docker (how the engine is meant to run)

```bash
docker build --platform linux/amd64 -t chameleon-engine .
docker run --rm --network none \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  chameleon-engine
```

Every `*.json` task file in `input/` (a `source` design and a `target_canvas`) produces
`<task>_output.json` and `<task>_output.png` in `output/`, plus a one-line self-check per task.
Everything is installed at build time; nothing is downloaded at run time.

To run with recipes only (no retrieved layouts), add `-e CHAMELEON_RETRIEVAL=0` to `docker run`
(or set it in the environment without Docker). If the layout library file is missing, the engine
runs with recipes only by itself.

### Without Docker

```bash
pip install -r requirements.txt        # Python 3.11
python -m engine.main                   # same input/ -> output/ behaviour
```

From Python: `from engine.resize import resize; resize(source_design, {"width": 1080, "height": 1350})`.

## How it works

`engine/resize.py` runs four stages. It never raises: a stage that fails for one candidate only
loses that candidate, and if every candidate fails the checks, the best repaired one is returned
(failing that, a uniform scale, then a repaired stretch).

### 1. Analyze (`engine/analyze.py`)

Reads the source design once and describes its structure:

- **Background**: the bottom-of-stack elements that cover the canvas. On the target it fills the
  whole canvas (`fit: cover` crops; any other fit keeps its aspect, centred).
- **Units**: elements that must move as one. These come from `group_id`, text sitting on a
  card, button, label or speech bubble (a shape, or a compact image: small, or flat-coloured and
  under half the canvas), a photo inside a frame, and small decorations layered on a unit.
  A unit is scaled uniformly, so nothing inside it shifts relative to the rest.
- **Grids and sibling rows**: repeated similar units (a row of icons with captions, a 2x2 grid
  of photos with their captions) become one unit that can re-flow to a different number of
  columns.
- **Roles**: headline, body, fine print, call to action, logo, hero image, badge, decoration,
  each from documented rules with a confidence. Importance follows role, confidence and size.
- **Reading order**: rows top to bottom, left to right within a row.
- **Special cases**: rule lines (at most 4 px thick and 10x longer) are decorations that keep a
  visible thickness. Flat panels too large to be a card are fitted around their text after
  layout. Backgrounds turned by a multiple of 90 degrees are recognised.

### 2. Recipes (`engine/recipes.py`)

Turns the analysis into candidate layouts ("plans": a box for each unit) for the target shape.
Each recipe runs over a small grid of knobs (alignment, spacing, image share, scale cap), giving
roughly 12-90 candidates per task:

| Recipe | Layout | Used when |
|---|---|---|
| stack | one column over the canvas | always |
| split | hero image in one column, everything else in the other | there is a hero, canvas not tall |
| anchor | a big hero keeps its share of the canvas against one edge; the rest is a column beside it | hero covers >= 25% of the design |
| strip | one row: logo, hero, text column, call to action | very wide banners (>= 2:1) |
| overlay | a stack confined to the quietest part of the background photo | there is a background photo |
| compact | only the essentials (headline, CTA, logo, hero) in the layout; the rest fills leftover space | tiny canvases |

All recipes share one column solver. It keeps the source reading order and finds the largest
common scale at which everything fits, with fonts never below a readable minimum. If even that
does not fit, the least important unit (never the headline, never a big hero photo) is taken out
of the column and placed later into free space. In a wide box where one column would hit the
readable minimum, the solver also tries 2 and 3 newspaper-style columns.

**Retrieved layouts** (`engine/retrieve.py`) are added alongside the recipes. A library of 1,494
layouts (`engine/data/layout_library.json`) holds the geometry of real designs as our analyzer
sees them: canvas aspect ratio, and each unit's role, kind and box as fractions of the canvas. It
holds no text, images or identifiers. For each task, the 30 library layouts with a similar aspect
ratio and the closest mix of roles are taken. Our units are mapped into their slots by an optimal
assignment on role, kind and size; text never goes into a slot where it would be unreadable, and
units without a good slot go into free space. Each mapped layout is sized by the same code as the
recipes, with the same scale limits. A retrieved layout is dropped when it gives the headline or
main image under 70% of the canvas share that the best recipe layout gives it.

### 3. Fit (`engine/fit.py`)

Turns each plan into a real output design:

- **Text** gets the largest whole-number font size that fits its box, measured with the
  renderer's own wrapping and line layout (`eval/check.py:text_layout`). Letter spacing scales
  with the font. Boxes get one spare line of height, because text metrics differ by about 1%
  between macOS and Linux renderers (text is top-aligned, so the spare space is invisible).
- **Images and units** use one uniform scale, so aspect ratios are exact.
- **Floating units** (corner badges, stickers, units taken out of the column) go into the best
  free rectangle near where they sat in the source, never overlapping what is already placed.
- **Rotated elements** keep their source angle (mirrored only when they ended up on the
  mirrored side of their anchor), and their rotated bounds stay on the canvas.
- **Decorations** keep their relative position, pulled fully inside the canvas.

### 4. Select (`engine/select.py`)

1. Drop duplicates and every candidate that breaks a hard rule (`eval/check.py`).
2. Drop candidates that put text newly on top of a busy part of an image (a headline over a photo
   or illustration it was not on in the source), unless every candidate does.
3. Rank the rest by a geometric score (`eval/score.py`, about 1 ms each), render the top 10 and
   re-rank with a text-contrast check. Rendering is the expensive step under emulation, so only
   those few are rendered.
4. When the target has the source's aspect ratio, the plain uniform scale of the source is
   preferred unless another candidate is clearly better (by 2 points).

**Time budget.** Each case has 15 seconds of wall-clock time (`engine/resize.py:BUDGET_S`). When
it runs out, no new candidates are generated or rendered and the best one so far is chosen, so the
engine always returns a valid output in about that time.

### Checking and scoring (`eval/`)

The engine ranks candidates with the same code we evaluate it with, so `eval/*.py` is copied
into the image.

- `eval/check.py`: the hard rules as we read them: same element ids, required fields, nothing off
  the canvas (unrotated box and rotated bounds), images in proportion (within 5%) unless `fit:
  cover`, `fit` unchanged, text inside its box (measured with the renderer's own layout), nothing
  shrunk out of sight, backgrounds still filling the canvas.
- `eval/score.py`: 0-100 from weighted penalties: overlaps, text newly on top of an image, the
  headline or main image losing its share of the canvas (the heaviest), text below a readable
  size, headline no longer leading, wasted or unbalanced space, floating elements drifting from
  what they sat on, text leaving its card, broken sibling groups, lost alignments, reading order,
  colour emphasis, and (optional, renders once) text contrast. The weights are fitted to 105
  cases labelled good, okay or bad by eye.

```bash
pip install -r requirements-dev.txt
python -m pytest                          # 177 tests
python -m eval.bench                      # 45 sample cases: check + score -> eval/results/
python -m eval.bench --render             # + a PNG per case and a contact sheet
python -m eval.synthetic                  # 300 random designs, robustness
```

The Crello test sets need the dataset converted locally first (`eval/crello_convert.py`,
`eval/crello_testset.py`). No Crello design, image or text is in the repository or the image;
the layout library is geometry and roles only (`eval/build_library.py`), built from Crello
designs that are not in either test set.

## Assumptions

The rules leave some points open. Where the organisers have not answered, we decided as follows.

1. **Backgrounds** fill the full target canvas with `fit: cover`, accepting the renderer's
   centred crop (the schema has no crop or focal-point field).
2. **Bleeds**: elements that bleed off the canvas in the source are pulled fully inside, and we
   check both the unrotated box and the rotated bounds against the canvas.
3. **"Source aspect ratio within ~5%"** means the source element box's aspect, not the asset
   file's.
4. **Only position, size and font size change.** Letter spacing scales with the font size.
   Rotation keeps the source angle or its mirror; content, fonts, colours, opacity, z-order and
   `fit` never change.
5. **Readable minimum** font size: 12 px, or 1.5% of the canvas height if larger. Text goes
   below it only when nothing else fits.
6. **A background turned 90 or 270 degrees** on a non-square canvas fills only the centred
   square: filling the canvas would push its unrotated box off the canvas.
7. **Crello is used only to test against and learn from**: geometry and roles, never pixels or
   text. The shipped layout library is derived geometry (normalised boxes and roles) with no
   text, pixels or identifiers. We consider this outside the dataset licence's restrictions on
   redistributing designs or their elements, but have not had that confirmed by the organisers.
8. **No model.** Quality comes from analysis, layout rules and selection, which keeps the image
   small and deterministic and the run fully offline.

## Known limitations

- **Hairlines on much smaller canvases.** A 1-3 px line on a design 3-4x larger than the target
  cannot stay at least 1 px thick and keep its proportions; we keep proportions, and our checker
  reports it as hidden. This is every remaining failure in our test sets.
- **Text inside groups shrinks with its group.** Text on a card or in a grid scales with it
  rather than re-wrapping, so a big card on a much smaller canvas can make its text small.
- **Retrieved layouts can still misjudge.** Some layouts of real designs suit our content
  poorly (e.g. a big decorative circle crowding out a photo). The scorer, guard and rejection
  rules catch most of these but not all; `CHAMELEON_RETRIEVAL=0` gives recipes only.
- **Panels with a lot of text.** A large flat panel is fitted around its text after layout; when
  the layout splits that text apart, the panel can grow over nearby decoration.
- **No crop control for photos.** The renderer always centre-crops `cover` images, so the subject
  of a background photo can be cut on extreme formats (e.g. 728x90).
- **Platform text metrics.** Glyph widths differ by about 1% between macOS and Linux, so the same
  task can produce slightly different (equally valid) layouts on each. Outputs from either
  platform pass the other's checks; byte-identical output across platforms is not guaranteed.
- **Renderer quirks we work around but do not fix**: text `opacity` is ignored by the renderer,
  `style_runs` ends are treated as inclusive, and a single word wider than its box is never
  broken, so the engine lowers the font size instead.
- **The scores above are our own.** They are calibrated against our labels, not the official
  rubric, which we have not seen.

## Repository

```
engine/            the engine: resize, analyze, recipes, retrieve, fit, select; main.py is the provided orchestrator
engine/data/       the layout library (geometry and roles only)
eval/              checker, scorer, benchmarks, test suites, Crello conversion, review page
renderer/          the provided renderer (transformer-convertor + cr-renderer), vendored
brand_kit/         fonts and assets for the sample designs
input/             the 3 sample task files
chameleon_design_schema_v0.9.json, RULES.md, FAQ.md   the provided spec and rules
NOTES.md           working notes: rules as read, renderer facts, decisions and measurements per round
```
