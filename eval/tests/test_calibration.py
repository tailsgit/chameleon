import numpy as np

from eval.calibrate import agreement, load, totals
from eval.score import PENALTIES


def test_scorer_agrees_with_hand_labels():
    cases = load()
    a = agreement(totals(cases, np.array([w for _f, w, _r in PENALTIES.values()])), [c["label"] for c in cases])
    # the scores you labelled against: 0.65 / 0.70. Since key_size (weight 2.0, for the Crello labels, which are
    # not in the repo) the samples agree at 0.82 / 0.92, against 0.87 / 0.95 before: a deliberate trade, see NOTES §21
    assert a["pairwise"] >= 0.80 and a["auc"] >= 0.90


def test_agreement_metric():
    assert agreement([3, 2, 1], [2, 1, 0])["pairwise"] == 1.0
    assert agreement([1, 2, 3], [2, 1, 0])["pairwise"] == 0.0
    assert agreement([1, 1], [2, 0])["pairwise"] == 0.5
