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
