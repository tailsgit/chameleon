"""Training-only source-quality diagnostics; no human labels or raw content."""

from __future__ import annotations

from collections import Counter

import numpy as np

from eval.check import check
from eval.score import score


def quality(target_b: dict, source_a: dict, pair: dict) -> dict:
    violations = Counter(v["rule"] for v in check(target_b, source_a["canvas"], source_a))
    fonts = [e["font_size"] for e in source_a["elements"] if e["type"] == "text"]
    minimum = max(12.0, source_a["canvas"]["height"] * 0.015)
    distance = float(np.abs(np.asarray([g["box"] for g in pair["source_groups"]]) - np.asarray(pair["target_boxes"])).mean())
    return {"hard_pass": not violations, "violation_counts": dict(violations),
            "hand_score": float(score(target_b, source_a["canvas"], source_a, contrast=False)["total"]),
            "readable_text_fraction": sum(f >= minimum for f in fonts) / len(fonts) if fonts else 1.0,
            "group_membership_kept": 1.0 - float(np.mean(pair["target_regrouped"])),
            "identity_box_l1": distance, "source_groups": len(pair["source_groups"]),
            "source_has_outside_boxes": any(g["box"][0] < 0 or g["box"][1] < 0 or g["box"][0] + g["box"][2] > 1 or g["box"][1] + g["box"][3] > 1 for g in pair["source_groups"])}
