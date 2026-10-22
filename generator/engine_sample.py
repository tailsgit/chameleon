"""Bounded 300-training-design comparison; engine outputs are cached once only."""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import logging
import math
import os
import pickle
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path

import numpy as np

from generator.campaigns import hashed
from generator.download import digest
from generator.make_data import atomic_json
from generator.pair_data import PHASE2, raw_rows
from generator.pair_geometry import METHODS, cheap_source, pair_record
from generator.pair_quality import quality
from generator.transient import render_assets

TIMEOUT_SECONDS = 20.0
MAX_CASES = 300


def bounded_process(command: list[str], payload: bytes, timeout: float = TIMEOUT_SECONDS,
                    env: dict[str, str] | None = None) -> dict:
    start = time.monotonic()
    child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             start_new_session=True, env=env)
    timed_out = False
    try:
        stdout, _ = child.communicate(payload, timeout=max(0.001, timeout - (time.monotonic() - start)))
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(child.pid, signal.SIGKILL)
        stdout, _ = child.communicate()
    if child.returncode == -signal.SIGALRM:
        timed_out = True
    return {"stdout": stdout, "elapsed": time.monotonic() - start, "timed_out": timed_out, "returncode": child.returncode}


def worker() -> None:
    # Parent enforces an end-to-end wall limit; this also prevents an orphaned
    # worker from living indefinitely if its controller is interrupted.
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.setitimer(signal.ITIMER_REAL, TIMEOUT_SECONDS)
    logging.disable(logging.CRITICAL)
    try:
        raw, fonts, formats, cached, canvas_a, seed = pickle.loads(sys.stdin.buffer.read())
        import random
        from engine.resize import resize
        from eval.crello_convert import convert
        random.seed(seed); np.random.seed(seed)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            target, _meta, images = convert(raw, fonts, formats)
            try:
                with render_assets(images):
                    started = time.monotonic()
                    source = resize(target, canvas_a)
                    seconds = time.monotonic() - started
                    record = pair_record(target, cached, source, "engine", 0)
                    metrics = quality(target, source, record)
            finally:
                for image in images.values():
                    image.close()
        result = {"status": "ok", "pair": record, "quality": metrics, "engine_seconds": seconds}
        encoded = json.dumps(result, allow_nan=False)
    except Exception as error:
        # Exception messages can contain private strings: report code locations,
        # exception class only, never the raw message or argument values.
        encoded = json.dumps({"status": "error", "exception": type(error).__name__,
                              "frames": [{"file": Path(f.filename).name, "line": f.lineno, "function": f.name}
                                         for f in traceback.extract_tb(error.__traceback__)]})
        print(encoded, flush=True)
        raise SystemExit(1)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    print(encoded, flush=True)


def version() -> str:
    paths = ["generator/engine_sample.py", "generator/pair_geometry.py", "generator/pair_quality.py",
             "generator/transient.py", "generator/extract.py", "engine/resize.py", "engine/analyze.py"]
    root = Path(__file__).resolve().parents[1]
    return hashed("".join(digest(root / p) for p in paths))


def comparison(out: Path) -> dict:
    cases = [json.loads(p.read_text()) for p in sorted((out / "cases").glob("*.json"))]
    by_method = {method: [] for method in [*METHODS, "engine"]}
    elapsed, resize_seconds = [], []
    for case in cases:
        for method in METHODS:
            by_method[method].append(case["cheap"][method])
        if case["status"] == "ok":
            by_method["engine"].append(case["engine"])
            resize_seconds.append(case["engine"]["seconds"])
        if case["engine_wall_seconds"] is not None:
            elapsed.append(case["engine_wall_seconds"])
    result = {"cases": len(cases), "timeouts": sum(c["status"] == "timeout" for c in cases),
              "interrupted_no_retry": sum(c["status"] == "interrupted" for c in cases),
              "hard_timeout_seconds": TIMEOUT_SECONDS,
              "engine_completed_median_resize_seconds": float(np.median(resize_seconds)) if resize_seconds else None,
              "engine_all_attempts_median_wall_seconds": float(np.median(elapsed)) if elapsed else None,
              "methods": {}}
    csv_rows = []
    for method, rows in by_method.items():
        if not rows:
            continue
        result["methods"][method] = {"n": len(rows), "median_seconds": float(np.median([r["seconds"] for r in rows])),
                                     **{key: float(np.mean([r["quality"][key] for r in rows])) for key in
                                        ["hard_pass", "hand_score", "readable_text_fraction", "group_membership_kept", "identity_box_l1"]}}
    # Paired success-only comparison avoids using different cheap/engine cohorts.
    completed = [c for c in cases if c["status"] == "ok"]
    result["completed_case_means"] = {method: {key: float(np.mean([(c["engine"] if method == "engine" else c["cheap"][method])["quality"][key] for c in completed]))
                                             for key in ["hard_pass", "hand_score", "readable_text_fraction", "group_membership_kept", "identity_box_l1"]}
                                      for method in [*METHODS, "engine"]} if completed else {}
    for c in cases:
        for method in [*METHODS, "engine"]:
            value = c["engine"] if method == "engine" else c["cheap"][method]
            if value is not None:
                csv_rows.append({"case": c["index"], "method": method, "seconds": value["seconds"],
                                 **{k: v for k, v in value["quality"].items() if k != "violation_counts"}})
    if csv_rows:
        with (out / "metrics.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0])); writer.writeheader(); writer.writerows(csv_rows)
    atomic_json(out / "summary.json", result)
    return result


def run(root: Path, limit: int) -> None:
    assert 0 < limit <= MAX_CASES
    plan = json.loads((root / "engine_plan.json").read_text())
    assert len(plan["cases"]) == MAX_CASES
    assert len({c["cached"]["design_hash"] for c in plan["cases"]}) == MAX_CASES
    assert all(c["cached"]["split"] == "train" and len(c["cached"]["groups"]) >= 2 for c in plan["cases"])
    out = root / "engine"; (out / "cases").mkdir(parents=True, exist_ok=True); (out / "attempts").mkdir(exist_ok=True)
    config = {"code_hash": version(), "plan_sha256": digest(root / "engine_plan.json"), "seed": plan["seed"],
              "max_cases": MAX_CASES, "timeout_seconds": TIMEOUT_SECONDS, "cpu_clock": 1, "critic": 0}
    config_path = out / "config.json"
    if config_path.exists():
        assert json.loads(config_path.read_text()) == config, "sample implementation changed; do not rerun engine cases"
    else:
        atomic_json(config_path, config)
    done = {int(p.stem) for p in (out / "cases").glob("*.json")}
    # A started-but-unfinished case consumed its attempt. Resume never reruns it.
    for marker in sorted((out / "attempts").glob("*.json")):
        index = int(marker.stem)
        if index not in done:
            row = json.loads(marker.read_text())
            row.update(status="interrupted", engine=None, engine_wall_seconds=None)
            atomic_json(out / "cases" / marker.name, row); done.add(index)
    wanted = { (c["cached"]["raw_shard"], c["cached"]["raw_row"]): c for c in plan["cases"] if c["index"] < limit and c["index"] not in done }
    logging.disable(logging.CRITICAL)
    from eval.crello_convert import convert
    from engine.analyze import analyze
    from generator.extract import group_features
    env = dict(os.environ, PYTHONHASHSEED=str(plan["seed"]), OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               CHAMELEON_CPU_CLOCK="1", CHAMELEON_CRITIC="0")
    for shard in sorted({s for s, _ in wanted}):
        for row_index, raw, fonts, formats in raw_rows(shard):
            case = wanted.get((shard, row_index))
            if case is None:
                continue
            cached, canvas_a, index = case["cached"], case["canvas_a"], case["index"]
            assert hashed(str(raw["id"])) == cached["design_hash"]
            cheap = {}
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                target, _meta, images = convert(raw, fonts, formats)
                try:
                    with render_assets(images):
                        assert group_features(analyze(target)) == cached["groups"], "target cache drift"
                        for method in METHODS:
                            start = time.monotonic()
                            source = cheap_source(target, cached["groups"], canvas_a, method, plan["seed"], cached["design_hash"], 0)
                            record = pair_record(target, cached, source, method, 0)
                            seconds = time.monotonic() - start
                            metrics = quality(target, source, record)
                            cheap[method] = {"pair": record, "quality": metrics, "seconds": seconds}
                finally:
                    for image in images.values(): image.close()
            marker = out / "attempts" / f"{index:03d}.json"
            assert not marker.exists(), "never repeat an engine attempt"
            saved = {"index": index, "design_hash": cached["design_hash"], "cheap": cheap}
            atomic_json(marker, saved)
            assert len(list((out / "attempts").glob("*.json"))) <= MAX_CASES
            result = bounded_process([sys.executable, "-u", "-m", "generator.engine_sample", "--worker"],
                                     pickle.dumps((raw, fonts, formats, cached, canvas_a, plan["seed"])), env=env)
            saved["engine_wall_seconds"] = result["elapsed"]
            if result["timed_out"]:
                saved.update(status="timeout", engine=None)
            else:
                response = json.loads(result["stdout"])
                assert result["returncode"] == 0 and response["status"] == "ok", response
                saved.update(status="ok", engine={"pair": response["pair"], "quality": response["quality"], "seconds": response["engine_seconds"]})
            atomic_json(out / "cases" / marker.name, saved)
            print(f"case {index:03d}: {saved['status']}; {result['elapsed']:.3f}s; {len(list((out / 'cases').glob('*.json')))}/{MAX_CASES}", flush=True)
    summary = comparison(out)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--root", type=Path, default=PHASE2)
    parser.add_argument("--limit", type=int, default=MAX_CASES)
    args = parser.parse_args()
    worker() if args.worker else run(args.root, args.limit)
