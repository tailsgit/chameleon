# Generator data

Phases 1 and 2 only. No generator model or training implementation is present.

Use the existing Chameleon venv and set `TMPDIR=/Volumes/Extreme/AdobeHackathon/tmp`.
Set `PYTHONHASHSEED=2026` before launching Python as well; Python and NumPy RNGs
are seeded inside the preprocessing command.
Run long commands under `caffeinate -i` with output redirected to a log under
`/Volumes/Extreme/AdobeHackathon/data/generator`.

- `python -m generator.download`: pinned raw train download, four transfers,
  partial-file HTTP resume, SHA256 verification, dataset-card row-count check.
- `python -m generator.make_data --follow-download`: processes verified shards as
  they arrive, then builds the global exclusion closure and campaign split.
- `python -m generator.make_data`: resumes completed sanitized shards after
  checking code/input metadata and output checksums. An interrupted extraction
  shard is rebuilt; completed shards are reused. Final outputs are replaced
  atomically and the summary is written last.
- `python -m generator.verify_data`: checks schemas, hashes, finite geometry,
  counts and design/campaign leakage against exclusions.

The existing converter's `convert()` and `engine.analyze.analyze()` run unchanged.
The converter's file-writing CLI is never invoked. A scoped image adapter serves
decoded image copies from RAM to analyzer/scorer reads. Source text, images and
source-dependent caches are discarded between designs. Arrow reads one raw row
at a time; sanitized output is flushed in batches of 32.

Saved rows contain hashed design identity, raw shard/row locators, canvas geometry,
hashed campaign fingerprints and groups. No literal design IDs, text, font/color
payloads, image assets, previews or encoded image bytes are saved. Groups include
engine units and decorations plus background/panel records; member references
are source element indices. Rows/grids preserve their parts and column count.
Coordinates are normalized source geometry, including original bleeds and rotated
bounds outside [0,1]. `flow_text` identifies rewrappable text; `engine_kind` keeps
the analyzer's text/image/rigid classification. Panels reference content indices
without counting that content twice. Cache files include rejected rows' hashes
and fingerprints, so a rejected design can still link a campaign component.

Campaign edges require an identical ordered element-type sequence and Jaccard
over nonempty text-element prefix hashes >=0.5. Prefixes are NFKC-normalized,
casefolded, whitespace-collapsed and truncated to 30 characters. Empty text sets
do not establish a match. Both raw and converted representations are checked
conservatively: conversion can drop elements and turn flat images into shapes.
Equal template IDs are equal hashed identities. `cluster_index` is documented
as a dataset-splitting debug cluster, not a campaign identifier; it is not used
as campaign identity. The dataset has no separate campaign/template-family ID.

Connected components include excluded designs, all raw training designs, and
rejected conversion records. Any component touching a labelled/dev/holdout or
organizer-sample design is excluded in full, including transitive links. The
remaining components are sorted by SHA256(seed:component); 5% (rounded to the
nearest component) go to validation. The design percentage may differ slightly.
Seed: 2026. Fingerprint caches are output data, never model inputs containing
text hashes or design identity. No human verdict is used as a training target.

## Phase 2 pairs

Run `python -m generator.pair_data` once to select a seeded 300-design training
sample and count inferred real cross-format candidates. These candidates are
not training examples; there is no authoritative campaign-family field.
Run `python -m generator.engine_sample --limit 300` under caffeinate, redirecting
output to `data/generator/phase2/engine.log`. Each sample gets at most one engine
attempt, with a hard 20-second process timeout. Interrupted attempts count toward
the cap and are never retried. The first engine output is cached; engine search
uses time budgets, so this cache does not imply engine rerun reproducibility.
Comparison metrics include hard-rule passes, readable text, unchanged group
membership, and normalized identity-box L1. The hand score is the engine's own
objective (contrast disabled), not an independent human quality assessment.

`python -m generator.build_pairs` streams four different source canvases per
real target: three real catalogue sizes and one aspect sampled between 0.25 and
4. Both cheap constructions are emitted: stretched group centers with uniform
internal scaling, and centered whole-layout uniform fit. Both use seeded small
group jitter. The unchanged analyzer extracts the resulting source groups.
The target is the original human layout, aligned by element membership. Exact
original groups reuse their cached real boxes, including row padding; changed
groups use unions of their members' real target bounds and are flagged.
No target coordinates are clipped. `target_outside_unit` flags coordinate
channels outside [0,1]; `target_outside_canvas` also flags right/bottom overflow.

Original designs and derived sources with fewer than two groups are omitted.
Train/validation membership remains the Phase 1 assignment; coverage is reported
separately. Shards resume after code/input/output checksum checks. Engine pairs
are cached separately and never mixed into the cheap pair dataset. The scoped
asset adapter supplies real images to renderer reads in memory without writing
assets or previews.

`python -m generator.verify_pairs` independently checks every target against its
original raw design in memory, group membership, char counts, overflow flags,
coverage, and Phase 1 exclusion/campaign leakage. For a fresh validation-only
reproduction, run `python -m generator.build_pairs --split val --out <qa-path>`
and compare the validation Parquet checksums. Only the focused tests under
`generator/tests` are needed; do not run repository benchmarks or the full suite.

## Phase 2b

The versioned `data/generator/phase2b` dataset adds `source_kind` to every pair:
`stretch`, `whole_fit`, `engine`, or `real`. The manifest declares `real` as the
future inference token. No model code or training is part of these commands.
The old 300-case engine diagnostic is excluded from this dataset.

- `python -m generator.reflow_data --workers 4`: choose 3,000 train and 300 val
  designs using seeded, balanced round-robin sampling across native format labels.
  Use the previous seeded schedule's first source canvas for each design.
  Four processes supervise at most four concurrent reflows, each killed after
  20 seconds. Timed-out and fewer-than-two-group outputs are omitted and counted.
  Case outputs are checkpointed; completed shard directories are never replaced.
  Every shard records the engine commit, checkout commit, UTC creation date,
  seed, input-plan/code hashes, and Parquet checksum. Reflows use cached outputs
  as the source of truth: fresh reruns may differ because engine search is timed.
- `python -m generator.real_pairs`: reproduce the 18,492 unordered cross-format
  candidates from Phase 2, then require complete, unique group correspondence.
  Keep the hashed-ID order as one canonical direction per unordered candidate;
  do not double the count by emitting both directions. Group kind, role and
  element-type multiset must agree. Text groups require equal multisets of full
  NFKC/casefold/whitespace-normalized text hashes. Image members must have equal
  relative stacking-order ranks, and each corresponding aspect ratio must differ
  by at most a factor of 1.25. Missing or ambiguous assignments reject the whole
  pair. Every group, including backgrounds and panels, must participate exactly
  once. Distinct native formats with equal canvas sizes are retained and counted.
  All conversion and unchanged engine analysis happen in RAM; only hashed text
  descriptors and sanitized geometry are cached. The output includes ten plain
  geometry tables in `matched_examples.md` and per-role match/retention rates.
- `python -m generator.pack_pairs`: create new cheap shards with `source_kind`
  and verify that every prior field remains equal. The Phase 2 cache is untouched.
- `python -m generator.audit_phase2b`: check exclusion/split leakage, immutable
  shard checksums/provenance, all four source kinds, exact real and engine target
  boxes, overflow flags, fixed reflow-plan membership, and pair uniqueness.
  An independent alternating-cycle check rejects ambiguous real assignments.
  Write `manifest.json` and `report.json`, including train/val counts and the
  median per-pair normalized box L1 for each source kind.

Run the jobs under `caffeinate -i`, with seed 2026 and logs under Phase 2b.
Completed shards are verified and reused on resume, never overwritten; incomplete
publication directories may be rebuilt. Do not install packages, use network,
change `engine/`, or start Phase 3 as part of this workflow.

## Phase 2c and Phase 3

`python -m generator.partial_pairs` uses existing descriptors only (no downloads,
conversion, or engine runs). A retained edge must occur in every maximum-cardinality
one-to-one matching. Keep a pair only when these forced edges cover at least 60%
of both designs. All source groups remain present; unmatched target placeholders
are zero with `matched=False` and target index -1, and never enter losses/metrics.
Keep `real_strict` separately for evaluation; it uses the `real` model token and
is not sampled as a fifth training kind. Aspect buckets use absolute log2(B/A).

Run `python -m generator.features`, then `python -m generator.baselines` before
training. The numeric cache and baseline tables live in `data/generator/phase3`.
The copy baseline uniformly fits all source boxes into B. Geometry retrieval uses
the existing library, aspect filter, composition ranking, role/kind/size/aspect
Hungarian assignment, and its first 16 ranked layouts. Unassigned groups use copy;
fewer than sixteen layouts are repeated. This baseline does not invoke text fitting,
rendering, or full engine reflow. Metrics average masked per-pair box L1.

The 1.95M-parameter CVAE embeds raw continuous features with Linear before every
LayerNorm path, including canvas and posterior target features. A 3-block transformer
conditions on the canvas and source-kind tokens. During training a posterior block
sees matched target boxes; inference uses only sixteen fixed standard-normal latent
vectors stored in the checkpoint/ONNX. The shared decoder predicts unbounded x/y
and positive sizes; real target boxes are never clipped. No text, fingerprints or
design identity enters the model.

The config is `generator/configs/cvae.yaml`. Each 100,000-example epoch has 1,250
batches of 80: exactly 24 stretch, 24 whole-fit, 16 engine and 16 real per batch.
Cheap kinds are sampled without replacement (30k each); engine/real with replacement
(20k each). Seeds depend on epoch; posterior noise depends on global step. Every
step checks all loss terms and all gradients for finiteness before clipping/update.
Box L1 and excess-over-target overlap use matched groups only; KL warms up over
5,000 steps. Model selection/early stopping uses only partial-real val best-of-16.

Run artifacts use `/Volumes/Extreme/AdobeHackathon/data/generator/runs/<name>`:

- `python -m generator.training --mode overfit --name cvae_overfit20`
- `python -m generator.training --name cvae_smoke --seconds 300`
- `python -m generator.training --name cvae_full --seconds 20700`
- Resume: add `--resume <run>/last.pt` with the same config/name. Time budget is
  cumulative across resumes. Exact epoch/batch position, optimizer state and steps
  are restored. `last.pt` is saved every ten minutes and every epoch; `best.pt` on
  significant real-val improvement. Step and validation CSVs record progress and
  epoch time. Run all jobs under `caffeinate -i`, with redirected logs outside Git.

`python -m generator.verify_training_data` prints exclusion/campaign leakage and
checks forced correspondence masks and feature-cache alignment against pair shards.
`python -m generator.evaluate --checkpoint <run>/best.pt` writes every kind/bucket's
best-of-16, median-of-16, copy/retrieval baseline and latent-diversity table.
`python -m generator.export --checkpoint <run>/best.pt` exports opset 17, under 10 MB,
checks all validation pairs against CPU PyTorch at max absolute error <1e-5, runs two
identical ONNX passes, saves the latent table, and times one-thread CPU inference.
The proposed real-val collapse threshold is mean pairwise box distance 0.005, about
40% of observed median training variation for same-source/similar-aspect examples.
Never extend the authorized compute budget or continue after non-finite training
without the user's decision. Do not integrate the model into `engine/`.

The validated `cvae_full` run stopped after 61 epochs; its selected checkpoint is
step 51,250 (41 completed epochs), using minimum-improvement tolerance 1e-4.
Artifacts are in `data/generator/runs/cvae_full`: `generator.onnx`, `latents.npy`,
`interface.json`, `evaluation.md`, `export.json`, the final report and CSV curves.
The interface metadata documents exact tensor shapes, feature/category ordering,
normalization, padding and the fixed `real` inference token. All 16 candidates are
returned in a single call; only valid group positions should be consumed.
