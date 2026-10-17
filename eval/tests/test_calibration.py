import numpy as np

from eval.calibrate import agreement, load, totals
from eval.score import PENALTIES


def test_scorer_agrees_with_hand_labels():
    cases = load()
    a = agreement(totals(cases, np.array([w for _f, w, _r in PENALTIES.values()])), [c["label"] for c in cases])
    assert a["pairwise"] >= 0.85 and a["auc"] >= 0.95  # old scorer: 0.73 / 0.82


def test_agreement_metric():
    assert agreement([3, 2, 1], [2, 1, 0])["pairwise"] == 1.0
    assert agreement([1, 2, 3], [2, 1, 0])["pairwise"] == 0.0
    assert agreement([1, 1], [2, 0])["pairwise"] == 0.5
