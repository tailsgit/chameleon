# Generator integration

Worktree `chameleon-int`, branch `gen-integration`, based on rules
`6e80cddee95dd5aa8d0718c96f4efdf45d02750a`. Both reference checkouts remain unchanged.

The generator adds proposals; existing fitting, hard checks, local repair, safety
tiers and scoring choose the output. No scorer formula/weight or CP-SAT solver
change. The shared training continuous/canvas/group feature builders are imported
by the ONNX adapter. CPU only, one thread, fixed 16 latent vectors, source kind
`real`; no Torch import in the complete inference path.

## Runtime policy

- Default **K=8**, selected after the full 600-case max CPU was 7.165 s.
- Per case: 4 recipe attempts on tight groups, 4 retrieval plans shared across
  analyses, 16 base realizations, at most K generator realizations, 3 contrast
  renders. Existing 4 preserve variants per analysis and solver settings stay intact.
- `GEN_OFF=1` disables generator proposals and retains these count caps. It is
  deliberately different from rules; capped-OFF quality is measured separately.
- `GEN_K=4/6/8` overrides the fit cap. Fixed count budgets replace runtime elapsed
  cutoffs. Optional critic search, still off by default, uses 8 fixed rounds.
- Rigid fitting uses the existing `Sizer.floor_scale()` so thin members remain
  visible when the canvas permits it. Entire rigid groups scale uniformly.
- Backgrounds, panels, attachments, decorations and rotations keep engine fitting
  semantics. There is no generator CP-SAT projection.

Model weights are local and ignored at `engine/data/generator.onnx` (6,039,539
bytes); copy source is `data/generator/runs/cvae_full`. interface.json declares
and verifies the original fixed latent table and model checksum. No data or
weights are committed.

## Measured checks

- 9 focused tests pass. 200 held-out raw designs reanalyze to the cached training
  groups; shared features and engine/training ONNX outputs are exact. Float32
  PyTorch checkpoint versus ONNX: max absolute difference 9.536743e-7 (<1e-6).
- Historical pre-cap flag-off adapter: 50/50 exact JSON bytes with identical
  recorded clocks. Two ordinary-clock mismatches remain recorded as evidence of
  legacy timing sensitivity. Current capped-OFF is compared by score instead.
- 600 dev, K=8: CPU p50/p95/max 1.613 / 3.968 / 7.165 s. Mean hand-score change
  versus the committed rules CSV -0.674917; 24 drops greater than 10 points.
  Capped-OFF: -1.000050, 21 drops. Generator proposals rescue 6 of those and
  introduce 9 new drops; 15 remain caps-sufficient. Generator wins 193/600.
- Same 40 cases repeated normally and with four extra CPU-burn processes:
  zero exact-output-byte mismatches in either comparison.
- Restoring the existing rigid-member floor fixes all 16 near-aspect failures.
  Remaining generator visibility failures are 64/9600 samples across four cases,
  where the current rigid arrangement cannot meet the 1px floor on that canvas.
  Checks were not weakened. Final outputs pass 598/600, the same count as rules.

Full timing, all-16 pass rates, original 25-case and selected 24-case regression
tables, and all case IDs are outside git at `data/generator/integration/`.
Completed per-case result files are immutable and validate their engine-code
fingerprint; use a new mode name after source changes.

## Labeling

Recall3 has the same 40 cases/order as recall2. It marks **GENERATOR WON** cases
and unique generator contributions. Source/output PNGs and tags are ignored.

From this worktree, using the existing venv:

```sh
export TMPDIR=/Volumes/Extreme/AdobeHackathon/tmp
/Volumes/Extreme/AdobeHackathon/chameleon/.venv/bin/python -m eval.tag_server --port 8781
```

Open `http://127.0.0.1:8781/recall3/`. Tags save only in this worktree's
`eval/results/recall3_tags.json`. No labeling server was started by this task.

No Docker runs, downloads or merges were performed.
