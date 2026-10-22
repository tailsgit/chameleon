"""Shared training/inference group extraction; no data conversion imports."""
from __future__ import annotations
import math
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from engine.analyze import Analysis

def group_features(analysis: Analysis) -> list[dict]:
    sw, sh = analysis.sw, analysis.sh
    els = analysis.els
    order = {eid: index for index, eid in enumerate(els)}

    def feature(members: list[str], box: tuple, role: str, kind: str,
                *, parts: list | None = None, cols: int = 0, host: str | None = None) -> dict:
        w, h = box[2] - box[0], box[3] - box[1]
        types = [els[eid]["type"] for eid in members]
        return {"members": [order[eid] for eid in members], "types": types, "role": role, "kind": kind,
                "box": [box[0] / sw, box[1] / sh, w / sw, h / sh], "aspect": w / max(h, 1e-9),
                "char_count": sum(len(els[eid].get("content", "")) for eid in members),
                "image_aspects": [els[eid]["width"] / max(els[eid]["height"], 1e-9) for eid in members if els[eid]["type"] == "image"],
                "area_share": w * h / (sw * sh), "z_order": min(els[eid].get("z_index", order[eid]) for eid in members),
                "host_members": [order[eid] for eid in analysis.units[host].members] if host else [],
                "parts": [{"members": [order[eid] for eid in mem], "box": [b[0] / sw, b[1] / sh, (b[2] - b[0]) / sw, (b[3] - b[1]) / sh]} for mem, b in (parts or [])],
                "cols": cols}

    out = []
    for u in [*analysis.units.values(), *analysis.decorations]:
        kind = "grid" if u.cols else "row" if u.parts else "flow_text" if u.kind == "text" else u.kind
        item = feature(u.members, u.box, u.role, kind, parts=u.parts, cols=u.cols, host=u.host)
        item["engine_kind"] = u.kind
        item["floating"] = u.floating
        out.append(item)
    # Preserve special groups separately: the engine does not put these in units.
    for eid in analysis.background:
        e = els[eid]
        item = feature([eid], (e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"]), "background", "background")
        item.update(engine_kind=e["type"], floating=False)
        out.append(item)
    for eid, members in analysis.panels.items():
        e = els[eid]
        item = feature([eid], (e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"]), "panel", "panel")
        item.update(engine_kind=e["type"], floating=False)
        # Content membership references other groups; it must not double-count elements.
        item["host_members"] = [order[m] for m in members]
        out.append(item)
    out.sort(key=lambda g: (g["z_order"], g["members"]))
    assert sorted(m for g in out for m in g["members"]) == list(range(len(els))), "group membership must partition elements"
    assert all(math.isfinite(v) for g in out for v in [*g["box"], g["aspect"], g["area_share"], *g["image_aspects"]])
    return out

