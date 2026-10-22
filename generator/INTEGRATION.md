# Integration checkpoint

Worktree: `chameleon-int`, branch `gen-integration`, based on `rules` at
`6e80cddee95dd5aa8d0718c96f4efdf45d02750a`. Neither reference checkout is edited.

`engine/data/generator.onnx` is a local, ignored artifact copied from
`data/generator/runs/cvae_full`. Its checksum is validated against interface.json.
The interface also declares the original fixed latent table, whose checksum is
validated; those same vectors are embedded in ONNX. Runtime never samples.

The adapter imports the exact shared training continuous/canvas/group builders.
Training-only data imports are lazy. Runtime uses ONNX Runtime CPU with one thread
and does not import Torch. Existing fitting handles backgrounds, attachments,
panels, decorations and rotations. Unit proposals are projected to the canvas;
rigid members scale uniformly. The existing local repair runs after realization.
No generator CP-SAT projection is added; preserve solver settings remain unchanged.

The enabled prototype uses 24 base realizations, round-robin by recipe family,
plus at most GEN_K generator realizations (default 6). Selection and its scorer
are unchanged, with no elapsed-time gate. Optional critic search uses 8 rounds
when enabled. GEN_OFF=1 retains legacy timing, generation and selection semantics.

## Checks and remaining gates

- Six focused integration/diagnosis tests passed.
- 200 held-out designs: raw reanalysis equals cached training groups; features
  byte-identical; engine/training ONNX output maximum difference 0.0; repeats exact.
- Normal-clock flag-off comparison: 48/50 byte-identical. Two mismatches must
  remain reported. The legacy cutoff depends on measured execution speed/cache
  state. Clock replay is a supplementary diagnostic, not a replacement pass.
- K=6 on 40 recall cases: median CPU 3.936502 s, max 22.526669 s. Budget FAIL.
  Profiling identifies upstream recipe/retrieval generation, which runs before
  the realization cap, as the main cost. Its work still needs a fixed count cap.
- K=4/8 timing, full repeat/load determinism, 600 dev evaluation, all-16
  post-repair hard-rule diagnostics, regression comparison, and recall3 page
  generation have NOT run. The recall3 builder and marker are implemented only.

Logs and per-case results are outside git under `data/generator/integration`.
This is an incomplete integration checkpoint; do not treat it as release-ready.
