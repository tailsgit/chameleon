# Generator integration

Worktree `chameleon-int`, branch `gen-integration`, based on rules
`6e80cddee95dd5aa8d0718c96f4efdf45d02750a`. Both reference checkouts remain unchanged.

The generator adds proposals; existing fitting, hard checks, local repair, safety
tiers and scoring choose the output. No scorer formula/weight or CP-SAT solver
change. The shared training continuous/canvas/group feature builders are imported
by the ONNX adapter. CPU only, one thread, fixed 16 latent vectors, source kind
`real`; no Torch import in the complete inference path.

## Runtime policy

- Generator **OFF by default**. `GEN_ON=1` opts in; `GEN_OFF=1` overrides it.
  The default resize path imports neither the generator nor ONNX Runtime and
  reads no model files. Explicit opt-in retains K=8 and the fixed latent table.
- One feasible representative for each applicable recipe family. Flow splits
  prefer plain analysis with centered justification; other recipes retain tight
  groups, with fallback when inapplicable. No case-specific paths or IDs.
- Every feasible existing preserve variant (share/fit/edges/between) from each
  distinct analysis is realized. CP-SAT code/settings are unchanged.
- Retrieval gets seven representatives from fixed strata over the existing
  top-30 ranking, plus a plain-analysis head representative when distinct. A
  full list uses ranks 0/4/9/14/19/24/29; shorter lists fill from available ranks
  without rescaling all strata. This keeps tail coverage as library size varies.
- Every required plan and every applicable focal/panel realization mode has a
  representative before the shared budget of **four additional realizations**.
  The 600-case run realizes 9–27 base candidates per case. All work is count
  bounded; there are no machine-speed cutoffs.
- Existing scorer weights, safety tiers, local repair, finishing and contrast
  cap of 3 are unchanged. There is no generator CP-SAT projection.
- Rigid fitting retains `Sizer.floor_scale()` and uniform group scaling.

## Current validation

Default-OFF 600 dev cases: process CPU p50/p95/max **1.293 / 3.491 / 6.821 s**;
normal <=9 s gate passes. Mean hand-score delta versus the committed rules CSV
is **-0.614150**, with **17 drops >10 points** (prior capped-OFF: -1.000050 and
21 drops). All final hard-rule outcomes match the prior run: 598/600 pass.

The three diagnosed lost accepted layouts return pixel-exact, pass hard rules
and survive the existing guard. Two appear in the top eight; only the LinkedIn
layout is the final pick. The preserved portrait is below the display cutoff.
This establishes pool recovery, not three newly labelled recall successes.

Same 40 cases twice normally and once with four CPU-burn processes: **zero
output-byte and candidate-pool mismatches**. Loaded recall maximum: 8.893 s.
The <=9 s timing claim is the full-600 normal default-OFF run.

15 focused tests pass. A fresh-process test forbids and records attempted
ONNX/generator imports and model reads, then asserts no attempts occurred.
Explicit `GEN_ON=1` smoke still fits 8/8 passing proposals with no Torch import.

Frozen scorer evidence uses the labelled generator-ON state at d3aedcc and two
accepted comparator layouts verified against original pixels. For LinkedIn,
the accepted layout already scores higher (92.67 vs 90.46); its old failure is
exclusion. For the portrait, the bad layout scores higher (90.03 vs 80.88),
mainly through coverage and key-size terms. Ten other cases have no confirmed
acceptable comparator and remain unknown. No scorer changes were made.

Full per-case scores, 17 regressions, exact recovery checks and term tables are
outside git at `data/generator/integration/path_budget/`. Reproduce with
`python -m eval.path_budget_eval NEW_MODE` (add `--suite recall`, then repeat
with a fresh mode and `--load`) and `python -m eval.scorer_pair_evidence`.
Use the existing venv, TMPDIR, PYTHONHASHSEED=2026 and caffeinate. Completed
result shards validate their engine/evaluator fingerprints and are immutable.

Model weights are local and ignored at `engine/data/generator.onnx` (6,039,539
bytes); copy source is `data/generator/runs/cvae_full`. interface.json declares
and verifies the original fixed latent table and model checksum. No data or
weights are committed.

## Earlier generator-ON checks

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

## Earlier flat-cap tuning pass

K=8 and the contrast cap of 3 stayed fixed. Trials used the same 600 dev cases,
seed 2026, four workers, full-resize process CPU time and committed rules CSV
scores. The current normal measurement below is the accepted pre-tuning run.
Recovery means a former caps-sufficient regression now drops at most 10 points;
the same original 15-case set is used for both trials.

| Recipe / retrieval / base caps | Normal CPU p50 / p95 / max, s | Mean score vs rules | Drops >10 | Recovered /15 |
|---|---|---|---|---|
| 4 / 4 / 16 | 1.613 / 3.968 / 7.165 | -0.6749 | 24 | 0 |
| 6 / 6 / 24 | 1.749 / 4.289 / 8.344 | -0.4749 | 20 | 4 |
| 8 / 8 / 32 | 2.063 / 4.895 / 10.187 | -0.3619 | 19 | 5 |

Under doubled load (four workers plus four CPU burns), all 600 cases measured
2.982 / 7.566 / 14.445 s with current caps, and 3.142 / 7.649 / 15.913 s at
1.5x caps. Both loaded runs have zero output-byte mismatches against their normal
runs. No loaded 2x-cap trial was needed after its normal maximum exceeded 9 s.

**Outcome at that stage: retain the old flat caps. No tested setting met both
the normal <=9 s and loaded <=12 s gates.** The 1.5x score gain is real, but misses the loaded limit;
2x misses the normal limit. This pass does not claim the loaded timing gate
passed, or change the scorer, preserve solver, generator, or recall candidates.
Further tightening was not part of this requested loosening pass.

Fresh final checks: 40 cases twice normally and once under doubled load have
zero output-byte and candidate-pool mismatches. The loaded 40-case maximum is
9.667 s; this smaller suite passes 12 s, while the full 600-case loaded suite
fails. All 10 focused tests pass. Recall3 was not regenerated: engine/caps are
unchanged, all 40 saved outputs and markers match, 352 referenced images and
JavaScript syntax verify. It retains 14 generator winners and 38 unique
contributions.

A reporting-only failure after the first 40-case run (`KeyError: delta`) came
from mixed dev-CSV baseline coverage in the recall suite. Optional summary
metrics now require all rows to contain them; every case and byte comparison
is retained. A focused regression test covers this case.

Reproduce a trial with, for example:

```sh
PYTHONHASHSEED=2026 caffeinate -i /Volumes/Extreme/AdobeHackathon/chameleon/.venv/bin/python -m eval.gen_budget_eval NEW_MODE --caps 6 6 24 --k 8 --jobs 4
```

Add `--load` for doubled load. Use a fresh mode name for each immutable trial.
`python -m eval.gen_cap_tuning eval_dev8_v3 tune_1p5_normal tune_2_normal`
rebuilds the score/recovery comparison. Detailed trial data, recovered case IDs,
and the final verification report stay under `data/generator/integration/`.

## Labeling

Recall3 has the same 40 cases/order as recall2. It marks **GENERATOR WON** cases
and unique generator contributions. Source/output PNGs and tags are ignored.

The existing recall3 page remains the frozen, labelled generator-ON comparison;
it was not replaced by the new default-OFF pool. From this worktree:

```sh
export TMPDIR=/Volumes/Extreme/AdobeHackathon/tmp
/Volumes/Extreme/AdobeHackathon/chameleon/.venv/bin/python -m eval.tag_server --port 8781
```

Open `http://127.0.0.1:8781/recall3/`. Tags save only in this worktree's
`eval/results/recall3_tags.json`. No labeling server was started by this task.

No Docker runs, downloads or merges were performed.
