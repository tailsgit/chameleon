# Generator data

Phase 1 only. No generator model or training implementation is present.

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
