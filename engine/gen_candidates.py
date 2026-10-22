"""Deterministic ONNX-only candidate proposals, fitted by the existing engine.

The fixed latent table is embedded in ONNX and declared in interface.json. No
runtime sampling. Background/panel/decoration fitting retains engine semantics.
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
import math
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort

from generator.features import KINDS, ROLES, MAX_GROUPS, N_CONT, continuous, canvases
from generator.group_features import group_features

DATA = Path(__file__).parent / 'data'
DEDUP_L1 = 0.005
log = logging.getLogger(__name__)
LAST: dict[str, Any] = {}


def enabled() -> bool:
    return os.environ.get('GEN_OFF') != '1'


@lru_cache(maxsize=1)
def runtime() -> tuple[ort.InferenceSession, dict]:
    interface = json.loads((DATA / 'interface.json').read_text())
    model = DATA / 'generator.onnx'
    if hashlib.sha256(model.read_bytes()).hexdigest() != interface['onnx_sha256']:
        raise ValueError('generator ONNX checksum mismatch')
    latent = np.asarray(interface['fixed_latents'], dtype=np.float32)
    buf = io.BytesIO(); np.save(buf, latent)
    if latent.shape[0] != 16 or hashlib.sha256(buf.getvalue()).hexdigest() != interface['latents_sha256']:
        raise ValueError('fixed latent table checksum mismatch')
    if interface['inputs']['source']['inference_value'] != interface['inputs']['source']['values']['real']:
        raise ValueError('inference source kind must be real')
    assert interface['inputs']['cat']['kinds'] == KINDS
    assert interface['inputs']['cat']['roles'] == ROLES
    options = ort.SessionOptions()
    options.intra_op_num_threads = options.inter_op_num_threads = 1
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    options.add_session_config_entry('session.use_deterministic_compute', '1')
    return ort.InferenceSession(str(model), options, providers=['CPUExecutionProvider']), interface


def features(groups: list[dict], source_canvas: dict, target: dict) -> dict[str, np.ndarray]:
    """Use the training functions, vocabulary, padding, and float conversion exactly."""
    _, meta = runtime()
    n = len(groups)
    if not 1 <= n <= MAX_GROUPS:
        raise ValueError(f'unsupported group count {n}; model maximum {MAX_GROUPS}')
    cont = np.zeros((1, MAX_GROUPS, N_CONT), np.float32)
    cat = np.zeros((1, MAX_GROUPS, 2), np.int64)
    valid = np.zeros((1, MAX_GROUPS), np.float32)
    cont[0, :n] = [continuous(g) for g in groups]
    cat[0, :n] = [[KINDS.index(g['kind']), ROLES.index(g['role'])] for g in groups]
    valid[0, :n] = 1
    row = {'canvas_a': [source_canvas['width'], source_canvas['height']],
           'canvas_b': [target['width'], target['height']]}
    return dict(cont=cont, cat=cat, valid=valid,
                canvas=np.asarray([canvases(row)], np.float32),
                source=np.asarray([meta['inputs']['source']['inference_value']], np.int64))


def predict(a: Any, target: dict) -> tuple[list[dict], np.ndarray]:
    groups = group_features(a)
    x = features(groups, a.source['canvas'], target)
    boxes = runtime()[0].run(['boxes'], x)[0][0, :, :len(groups)].copy()
    if not np.isfinite(boxes).all():
        raise ValueError('nonfinite generator output')
    return groups, boxes


def project(groups: list[dict], boxes: np.ndarray, tw: int, th: int) -> np.ndarray:
    out = np.asarray(boxes, np.float64).copy()
    for g, b in zip(groups, out):
        x, y, w, h = b * [tw, th, tw, th]
        cx, cy = x + w / 2, y + h / 2
        w, h = max(w, 1.5), max(h, 1.5)
        if g['kind'] == 'background':
            b[:] = [0, 0, 1, 1]; continue
        if g['kind'] not in ('flow_text', 'panel'):
            aspect = max(g['aspect'], 1e-9)
            w = min(w, h * aspect); h = w / aspect
        scale = min(1., tw / w, th / h)
        w *= scale; h *= scale
        b[:] = [min(max(cx - w/2, 0), tw-w)/tw,
                min(max(cy - h/2, 0), th-h)/th, w/tw, h/th]
    return out


def geometry_cost(groups: list[dict], boxes: np.ndarray) -> float:
    """Only newly introduced foreground overlap; designed containment is free."""
    ids = [i for i,g in enumerate(groups) if g['kind'] not in ('background','panel')]
    def overlap(a: np.ndarray, b: np.ndarray) -> float:
        area = np.maximum(0, np.minimum(a[:2]+a[2:], b[:2]+b[2:])-np.maximum(a[:2], b[:2])).prod()
        return float(area/max(min(a[2]*a[3],b[2]*b[3]), 1e-9))
    source = np.asarray([g['box'] for g in groups])
    return sum(max(0., overlap(boxes[i], boxes[j])-overlap(source[i],source[j]))
               for k,i in enumerate(ids) for j in ids[k+1:])


def fit_sample(a: Any, target: dict, groups: list[dict], boxes: np.ndarray, sample: int) -> dict:
    from engine.fit import Sizer, realize
    from engine.recipes import Plan, Slot
    from engine.retrieve import _place
    from engine.select import repair
    tw, th = target['width'], target['height']
    sizer = Sizer(a, tw, th)
    members = {tuple(g['members']): b for g,b in zip(groups, boxes)}
    order = {eid:i for i,eid in enumerate(a.els)}
    slots = []
    for u in a.units.values():
        if u.host:
            continue  # existing attached-unit handling follows its host
        x,y,w,h = members[tuple(order[m] for m in u.members)]
        if u.kind == 'text':
            slots.append(_place(a,sizer,u,[x,y,x+w,y+h],tw,th))
        else:
            scale = min(w*tw/max(u.w,1e-9), h*th/max(u.h,1e-9))
            cols = (u.cols or len(u.parts)) if u.parts else None
            slots.append(Slot(u.id,x*tw,y*th,u.w*scale,u.h*scale,scale=scale,cols=cols))
    plan = Plan('generator', {'sample':sample},slots,[u.id for u in a.units.values() if u.host],
                math.sqrt(tw*th/(a.sw*a.sh)),0.,sizer)
    # Existing background, attachment, panel, decoration and rotation semantics.
    output = realize(a,plan,tw,th)
    return repair(a.source,target,output)


def candidates(a: Any, target: dict, k: int | None = None) -> list[dict]:
    LAST.clear(); LAST.update(attempted=0, passing=0, unique=0, sample_indices=[], outputs=[])
    k = int(os.environ.get('GEN_K','6')) if k is None else k
    if not 0 <= k <= 16:
        raise ValueError('GEN_K must be between 0 and 16')
    groups, raw = predict(a,target)
    projected = [project(groups,b,target['width'],target['height']) for b in raw]
    ranking = sorted(range(16), key=lambda i:(geometry_cost(groups,projected[i]),i))
    selected = []
    for i in ranking:
        if all(float(np.mean(np.abs(projected[i]-projected[j]))) >= DEDUP_L1 for j in selected):
            selected.append(i)
    LAST['unique'] = len(selected)
    from engine.select import _passes
    outputs = []
    for i in selected[:k]:
        out = fit_sample(a,target,groups,projected[i],i)
        outputs.append(out)
        LAST['attempted'] += 1
        LAST['passing'] += int(_passes(a.source,target,out))
        LAST['sample_indices'].append(i)
    LAST['outputs'] = outputs
    return outputs


def layout_distance(a: dict, b: dict) -> float:
    """Recall-page uniqueness distance in target-canvas fractions."""
    aa={e['id']:e for e in a['elements']};w=a['canvas']['width'];h=a['canvas']['height']
    values=[]
    for e in b['elements']:
        q=aa[e['id']]
        values.append(abs(e['x']+e['width']/2-q['x']-q['width']/2)/w+
                      abs(e['y']+e['height']/2-q['y']-q['height']/2)/h+
                      abs(e['width']-q['width'])/w+abs(e['height']-q['height'])/h)
    return float(np.mean(values)) if values else 0.
