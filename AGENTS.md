# Chameleon generator: training work (Codex)

## Goal
Build a small source-conditioned, group-level layout generator for an offline layout-reflow engine (Adobe hackathon "Project CHAMELEON"). It takes a design's groups plus a target canvas shape and proposes several candidate group boxes. The existing engine then fits text, enforces hard rules and picks the best candidate. The model only adds candidates; it never replaces the rules.

## Final-system constraints
- Runs offline in Docker (--network none), CPU only, deterministic (same input, same output), about 13.5 s per case in total, so the model must run in a few ms.
- Export to ONNX (onnxruntime in the final image; PyTorch only in dev). Target size under 10 MB. Weights go on a public Hugging Face repo later.
- Geometry and roles only. Never ship or commit Crello text, pixels or ids.

## Where things are (absolute paths)
- Your working repo (git worktree, branch `generator`): /Volumes/Extreme/AdobeHackathon/chameleon-gen
- Main checkout (READ ONLY, another agent works there): /Volumes/Extreme/AdobeHackathon/chameleon
- Python (use this, do not create another venv): /Volumes/Extreme/AdobeHackathon/chameleon/.venv/bin/python
- Crello data: /Volumes/Extreme/AdobeHackathon/data/crello_chameleon (env var CRELLO_CHAMELEON)
- Earlier critic work (reference only): /Volumes/Extreme/AdobeHackathon/data/critic and critic/ in the repo
- Human labels (TEST ONLY, read only): /Volumes/Extreme/AdobeHackathon/chameleon/eval/results/*/labels.json, failure_tags.json, recall_tags.json, recall2_tags.json
- Put all generated data, checkpoints and logs in /Volumes/Extreme/AdobeHackathon/data/generator (outside git).
- export TMPDIR=/Volumes/Extreme/AdobeHackathon/tmp before running anything.

## Rules
1. Work only inside chameleon-gen (and the data folder above). Never edit, delete or checkout anything in the main checkout, never touch main, any tag (v1..v4, submission-fallback), or the branches critic, diagnose, rules, setup, eval, crello, retrieval, structure, preserve, contrast, extreme.
2. The human labels are a TEST SET. Never train on them, tune on them, or copy them. Read them only for evaluation.
3. No leakage. Designs that appear in any label file, the dev or holdout suites, or the benchmark must be excluded from training. Reuse the exclusion logic in critic/make_data.py, and also dedupe the training split against those designs by element structure and text overlap (same campaign in other formats).
4. Determinism: seed everything (python, numpy, torch), log the seeds, and make data ordering reproducible.
5. Environment: use the venv python above. Do not upgrade, downgrade or uninstall packages there. If a package is missing, tell me the exact install command and wait.
6. Disk and data: before downloading or converting anything large, check free space on /Volumes/Extreme and report the expected size first. Do not commit data, checkpoints or weights. Commit only small code, configs and docs.
7. Work in small steps, each with a check that must pass: print shapes and value ranges, decode and print a few examples, run an "overfit 20 training examples" test, compare with a trivial baseline.
8. Training: log to a CSV, checkpoint every epoch (best and last), support --resume, print time per epoch. Run long jobs with `caffeinate -i` and write output to a log file.
9. Honesty: never say something works unless you ran the check and saw it pass. If a check fails, stop and show me the output. Do not weaken a check or change the spec or hyperparameters silently. List every deviation.
10. Do not run Docker, the engine benchmarks or any full test suite unless I ask. They compete for the CPU.
11. No network use unless I approve it. Never write tokens or secrets into files or commands.
12. Python 3.11, type hints, small modules, tests with pytest under generator/tests.

## Report format
Short. What ran, the numbers, what failed, what you need from me. No recaps.
