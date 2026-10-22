"""Conservative unique group correspondence, using hashes rather than raw text."""
from __future__ import annotations

import math
import unicodedata
from collections import Counter

from generator.campaigns import hashed

IMAGE_ASPECT_RATIO_LIMIT = 1.25


def text_hash(text: str) -> str:
    return hashed(" ".join(unicodedata.normalize("NFKC", text).casefold().split()))


def descriptors(design: dict, groups: list[dict]) -> list[dict]:
    elements = design["elements"]
    image_order = {i: rank for rank, i in enumerate(i for i, e in enumerate(elements) if e["type"] == "image")}
    return [{"text_hashes": sorted(text_hash(elements[m].get("content", "")) for m in g["members"] if elements[m]["type"] == "text"),
             "image_order": [image_order[m] for m in g["members"] if m in image_order],
             "image_aspects": g["image_aspects"]} for g in groups]


def compatible(a: dict, ak: dict, b: dict, bk: dict) -> bool:
    if (a["kind"], a["role"], sorted(a["types"])) != (b["kind"], b["role"], sorted(b["types"])):
        return False
    if ak["text_hashes"] != bk["text_hashes"] or ak["image_order"] != bk["image_order"]:
        return False
    return len(ak["image_aspects"]) == len(bk["image_aspects"]) and all(
        x > 0 and y > 0 and abs(math.log(x / y)) <= math.log(IMAGE_ASPECT_RATIO_LIMIT) + 1e-12
        for x, y in zip(ak["image_aspects"], bk["image_aspects"]))


def maximum_matching(edges: list[list[int]], banned: tuple[int, int] | None = None) -> dict[int, int]:
    owner: dict[int, int] = {}

    def visit(i: int, seen: set[int]) -> bool:
        for j in edges[i]:
            if (i, j) == banned or j in seen:
                continue
            seen.add(j)
            if j not in owner or visit(owner[j], seen):
                owner[j] = i
                return True
        return False

    for i in range(len(edges)):
        visit(i, set())
    return {i: j for j, i in owner.items()}


def match(left: dict, right: dict) -> tuple[list[int] | None, str, dict]:
    a, b = left["cached"]["groups"], right["cached"]["groups"]
    edges = [[j for j, (g, key) in enumerate(zip(b, right["group_keys"])) if compatible(f, fk, g, key)]
             for f, fk in zip(a, left["group_keys"])]
    assignment = maximum_matching(edges)
    total = Counter(g["role"] for g in [*a, *b])
    matched = Counter(a[i]["role"] for i in assignment)
    stats = {"total": dict(total), "compatible": {r: 2 * n for r, n in matched.items()}}
    if len(a) != len(b):
        return None, "group_count_mismatch", stats
    if len(assignment) != len(a):
        return None, "unmatched_group", stats
    # A clean correspondence must have exactly one perfect matching. Removing
    # any chosen edge must destroy perfection; otherwise the pair is ambiguous.
    if any(len(maximum_matching(edges, (i, j))) == len(a) for i, j in assignment.items()):
        return None, "ambiguous", stats
    return [assignment[i] for i in range(len(a))], "ok", stats
