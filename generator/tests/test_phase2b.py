from pathlib import Path

import pytest

from generator.phase2b import promote, publish, verified
from generator.reflow_data import balanced
from generator.match_real import match, text_hash
from generator.real_pairs import prepare_descriptors
from generator.audit_phase2b import unique_by_cycles


def test_balanced_selection_is_seeded_and_covers_rare_formats() -> None:
    rows = [{"design_hash": f"{i:064x}", "format": "common" if i < 90 else "rare"} for i in range(100)]
    first = balanced(rows, 20, 2026, "train")
    assert first == balanced(list(reversed(rows)), 20, 2026, "train")
    assert len({r["design_hash"] for r in first}) == 20
    assert sum(r["format"] == "rare" for r in first) == 10


def test_completed_shard_cannot_be_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "shard"
    identity = {"seed": 2026}
    original = publish(path, [], identity)
    assert verified(path, identity) == original
    assert len(original["engine_commit"]) == 40
    assert original["created_utc"]
    with pytest.raises(AssertionError, match="never overwrite"):
        publish(path, [], identity)
    assert verified(path, identity) == original


def test_source_kind_names_are_explicit() -> None:
    for old, new in (("stretch_uniform", "stretch"), ("uniform_fit", "whole_fit"), ("engine", "engine")):
        assert promote({"method": old, "design_hash": "a" * 64})["source_kind"] == new


def record(texts: list[str]) -> dict:
    return {"cached": {"groups": [{"kind": "flow_text", "role": "body", "types": ["text"]} for _ in texts]},
            "group_keys": [{"text_hashes": [text_hash(t)], "image_order": [], "image_aspects": []} for t in texts]}


def test_real_matching_uses_text_identity_instead_of_box_order() -> None:
    mapping, reason, stats = match(record([" First ", "SECOND"]), record(["second", "first"]))
    assert mapping == [1, 0] and reason == "ok"
    assert stats["compatible"] == {"body": 4}
    assert match(record(["a", "b"]), record(["a", "c"]))[1] == "unmatched_group"


def test_ambiguous_correspondence_is_rejected() -> None:
    assert match(record(["same", "same"]), record(["same", "same"]))[1] == "ambiguous"


def test_image_correspondence_requires_order_and_aspect() -> None:
    def image(aspect: float, order: int) -> dict:
        return {"cached": {"groups": [{"kind": "image", "role": "hero", "types": ["image"]}]},
                "group_keys": [{"text_hashes": [], "image_order": [order], "image_aspects": [aspect]}]}
    assert match(image(2.0, 0), image(2.4, 0))[1] == "ok"
    assert match(image(2.0, 0), image(2.6, 0))[1] == "unmatched_group"
    assert match(image(2.0, 0), image(2.0, 1))[1] == "unmatched_group"


def test_fresh_descriptor_directory_and_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("generator.real_pairs.raw_rows", lambda _shard: iter(()))
    assert prepare_descriptors(tmp_path, {}, {"seed": 2026}) == {}
    files = sorted((tmp_path / "real_descriptors").glob("*.json"))
    assert len(files) == 31
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files}
    def unexpected_read(_shard: int) -> None:
        raise AssertionError("completed descriptor cache was regenerated")
    monkeypatch.setattr("generator.real_pairs.raw_rows", unexpected_read)
    assert prepare_descriptors(tmp_path, {}, {"seed": 2026}) == {}
    assert before == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files}


def test_independent_cycle_audit_detects_alternative_matching() -> None:
    a = record(["a", "b"])
    unique_by_cycles(a["cached"]["groups"], a["group_keys"], a["cached"]["groups"], a["group_keys"], [0, 1])
    b = record(["same", "same"])
    with pytest.raises(AssertionError, match="alternating cycle"):
        unique_by_cycles(b["cached"]["groups"], b["group_keys"], b["cached"]["groups"], b["group_keys"], [0, 1])
