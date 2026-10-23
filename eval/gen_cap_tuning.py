"""Summarize immutable cap trials against the fixed pre-tuning regression set."""
from __future__ import annotations
import argparse
import json
from eval.gen_integration import OUT, atomic


def trial(mode: str, affected: set[str]) -> dict:
    data = json.loads((OUT / f"{mode}.json").read_text())
    rows = data["rows"]
    baseline = {r["case"]: r for r in json.loads((OUT / "eval_dev8_v3.json").read_text())["rows"]}
    deltas = [r["score"] - baseline[r["case"]]["rules_score"] for r in rows]
    recovered = [r["case"] for r, d in zip(rows, deltas) if r["case"] in affected and d >= -10]
    return dict(mode=mode, caps=rows[0].get("caps", [4, 4, 16]),
                cpu=data["summary"]["cpu_s"], mean_delta=sum(deltas)/len(rows),
                regressions=sum(d < -10 for d in deltas), recovered=recovered,
                recovered_count=len(recovered), cases=len(rows))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("modes", nargs="+")
    args = parser.parse_args()
    old = json.loads((OUT / "regressions_selected_k8.json").read_text())
    affected = {r["case"] for r in old["rows"] if r["off_delta"] < -10}
    assert len(affected) == 15
    rows = [trial(mode, affected) for mode in args.modes]
    atomic(OUT / "cap_tuning_comparison.json", dict(reference="eval_dev8_v3", cap_regressions=sorted(affected), trials=rows))
    print("| Caps (recipe/retrieval/base) | CPU p50/p95/max s | Mean vs rules | Regressions | Recovered / 15 |")
    print("|---|---|---|---|---|")
    for r in rows:
        c = r["cpu"]
        print(f"| {r['caps']} | {c['p50']:.3f}/{c['p95']:.3f}/{c['max']:.3f} | {r['mean_delta']:+.4f} | {r['regressions']} | {r['recovered_count']} |")


if __name__ == "__main__":
    main()
