from generator.partial_pairs import forced_matching
from generator.tests.test_phase2b import record

def test_only_forced_correspondences_receive_loss() -> None:
    a, b = record(["unique", "same", "same", "other"]), record(["same", "unique", "same", "other"])
    assert forced_matching(a["cached"]["groups"], a["group_keys"], b["cached"]["groups"], b["group_keys"]) == {0: 1, 3: 3}

def test_partial_different_group_counts() -> None:
    a, b = record(["a", "b", "c"]), record(["b", "c", "d", "a"])
    assert forced_matching(a["cached"]["groups"], a["group_keys"], b["cached"]["groups"], b["group_keys"]) == {0: 3, 1: 0, 2: 1}
