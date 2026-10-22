# Chameleon generator: integration work (Codex)

## Goal
Build a small source-conditioned, group-level layout generator for an offline layout-reflow engine (Adobe hackathon "Project CHAMELEON"). It takes a design's groups plus a target canvas shape and proposes several candidate group boxes. The existing engine then fits text, enforces hard rules and picks the best candidate. The model only adds candidates; it never replaces the rules.

## Final-system constraints
- Runs offline in Docker (--network none), CPU only, deterministic (same input, same output), about 13.5 s per case in total, so the model must run in a few ms.
- Export to ONNX (onnxruntime in the final image; PyTorch only in dev). Target size under 10 MB. Weights go on a public Hugging Face repo later.
- Geometry and roles only. Never ship or commit Crello text, pixels or ids.

## Where things are (absolute paths)
- Your working repo (git worktree, branch `gen-integration`): /Volumes/Extreme/AdobeHackathon/chameleon-int
- Generator checkout (READ ONLY): /Volumes/Extreme/AdobeHackathon/chameleon-gen
- Main checkout (READ ONLY, another agent works there): /Volumes/Extreme/AdobeHackathon/chameleon
- Python (use this, do not create another venv): /Volumes/Extreme/AdobeHackathon/chameleon/.venv/bin/python
- Crello data: /Volumes/Extreme/AdobeHackathon/data/crello_chameleon (env var CRELLO_CHAMELEON)
- Earlier critic work (reference only): /Volumes/Extreme/AdobeHackathon/data/critic and critic/ in the repo
- Human labels (TEST ONLY, read only): /Volumes/Extreme/AdobeHackathon/chameleon/eval/results/*/labels.json, failure_tags.json, recall_tags.json, recall2_tags.json
- Put all generated data, checkpoints and logs in /Volumes/Extreme/AdobeHackathon/data/generator (outside git).
- export TMPDIR=/Volumes/Extreme/AdobeHackathon/tmp before running anything.

## Rules
1. Work only inside chameleon-int (and the data folder above). Never edit either chameleon or chameleon-gen, including their engine/ files. Work only on gen-integration, branched from rules; never merge or change other branches or tags. Engine changes here are limited to a new engine/gen_candidates.py, one minimal candidate-pool hook, the requested count-based determinism fix, and tests/evaluation scripts. Do not change the scorer or its weights or make other behavior changes. GEN_OFF=1 disables generator proposals but retains the calibrated count budgets; the generator is ON by default here. The user explicitly authorized this change from rules behavior.
2. The human labels are a TEST SET. Never train on them, tune on them, or copy them. Read them only for evaluation.
3. No leakage. Designs that appear in any label file, the dev or holdout suites, or the benchmark must be excluded from training. Reuse the exclusion logic in critic/make_data.py, and also dedupe the training split against those designs by element structure and text overlap (same campaign in other formats).
4. Determinism: seed everything (python, numpy, torch), log the seeds, and make data ordering reproducible.
5. Environment: use the venv python above. Do not upgrade, downgrade or uninstall packages there. If a package is missing, tell me the exact install command and wait.
6. Disk and data: before downloading or converting anything large, check free space on /Volumes/Extreme and report the expected size first. Do not commit data, checkpoints or weights. Commit only small code, configs and docs.
7. Work in small steps, each with a check that must pass: print shapes and value ranges, decode and print a few examples, run an "overfit 20 training examples" test, compare with a trivial baseline.
8. Training: log to a CSV, checkpoint every epoch (best and last), support --resume, print time per epoch. Run long jobs with `caffeinate -i` and write output to a log file.
9. Honesty: never say something works unless you ran the check and saw it pass. If a check fails, stop and show me the output. Do not weaken a check or change the spec or hyperparameters silently. List every deviation.
10. Phase 4 authorizes the requested focused tests, 50-case flag-off comparison, 200-design feature/output parity, K=4/6/8 timing, 40-case repeat/load determinism test, 40 recall and 600 crello-dev evaluations, and recall3 page generation. Do not run Docker, unrelated benchmarks or a full test suite. No new downloads. Keep commits small; stop and report when done.
11. No network use unless I approve it. Never write tokens or secrets into files or commands.
12. Python 3.11, type hints, small modules, tests with pytest under generator/tests.

## Report format
Short. What ran, the numbers, what failed, what you need from me. No recaps.

## Phase 4 artifacts and gates
- Copy only generator.onnx and interface.json from data/generator/runs/cvae_full into engine/data/. Keep weights out of commits under rule 6.
- Runtime uses onnxruntime CPU, one thread, the exported fixed latent table and source_kind real; reuse the training feature builder.
- Keep both reference checkouts read only. No training or label changes. Test-only recall previews are authorized evaluation artifacts; never commit them.
- Stop and report any conflict between the requested behavior and the existing repo instead of guessing.

- User resolved repair scope: use existing fit/check/local repair only. Leave CP-SAT preserve candidates unchanged; no generator CP-SAT projection. Report hard-rule passes after local repair for all 16 samples by aspect-change bucket, including rejected/deduplicated samples in the diagnostic denominator.

- Latest user budget: calibrate recipe/retrieval/realization caps from per-operation costs on all 600 dev cases; K=6 worst case must be at most 10 CPU seconds on this Mac. Compare capped GEN_OFF and enabled scores to original rules. Historical flag-off equivalence uses identical recorded clocks, with the two ordinary-clock mismatches retained. Report K=4/6/8 time and candidate recall, 40-case repeats under 2x CPU load, all-16 pass rates and recall3.
