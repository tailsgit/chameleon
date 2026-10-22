"""Text-free fingerprints and connected campaign components."""

from __future__ import annotations

import hashlib
import unicodedata
from collections import defaultdict


def hashed(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def text_prefix(value: str) -> str:
    """Normalize before truncating; retain no literal text in the fingerprint."""
    normalized = " ".join(unicodedata.normalize("NFKC", value).casefold().split())[:30]
    return hashed(normalized) if normalized else ""


def fingerprint(elements: list[dict]) -> dict:
    return {"types": [e["type"] for e in elements],
            "texts": sorted({h for e in elements if e["type"] == "text" and (h := text_prefix(e.get("content", "")))})}


def similarity(left: dict, right: dict) -> float:
    if left["types"] != right["types"]:
        return 0.0
    a, b = set(left["texts"]), set(right["texts"])
    return len(a & b) / len(a | b) if a and b else 0.0


def cluster(records: list[dict]) -> tuple[dict[str, str], list[dict]]:
    """Union all matching edges, including excluded/rejected bridge designs.

    Compare both raw and converted fingerprints. An inverted prefix index makes
    comparisons exact without the quadratic scan over unrelated designs.
    """
    parent = {r["design_hash"]: r["design_hash"] for r in records}

    def find(key: str) -> str:
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    def union(a: str, b: str) -> None:
        a, b = find(a), find(b)
        parent[max(a, b)] = min(a, b)

    inverted: dict[tuple, list[tuple[str, dict]]] = defaultdict(list)
    edges = []
    seen = set()
    for row in sorted(records, key=lambda r: r["design_hash"]):
        key = row["design_hash"]
        for fp in row["fingerprints"]:
            candidates = {}
            for token in fp["texts"]:
                for other, other_fp in inverted[(tuple(fp["types"]), token)]:
                    candidates[(other, tuple(other_fp["texts"]))] = other_fp
            for (other, _), other_fp in sorted(candidates.items()):
                if key == other:
                    continue
                score = similarity(fp, other_fp)
                pair = tuple(sorted((key, other)))
                if score >= 0.5:
                    union(key, other)
                    if pair not in seen:
                        edges.append({"left": pair[0], "right": pair[1], "jaccard": score,
                                      "types": fp["types"], "shared_text_hashes": sorted(set(fp["texts"]) & set(other_fp["texts"]))})
                        seen.add(pair)
            for token in fp["texts"]:
                inverted[(tuple(fp["types"]), token)].append((key, fp))
    return {key: find(key) for key in sorted(parent)}, edges
