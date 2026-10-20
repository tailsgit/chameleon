"""Layout scores from the trained critic (ONNX), else from the hand scorer.

The model file is $CHAMELEON_CRITIC_MODEL, else engine/data/critic.onnx (exported by critic.export; the
Docker build can download it, see the Dockerfile's CRITIC_URL). When the file or onnxruntime is missing, or
the model's features don't match critic.features, scores() falls back to eval.score's total, so callers work
the same either way; only the scale differs (critic: any real number; hand scorer: 0-100). Compare scores of
layouts of the same source and target only.
"""

import logging
import os
from functools import lru_cache
from pathlib import Path

import numpy as np

from critic.features import N_CONT, encode
from eval.score import score

DEFAULT = Path(__file__).parent / "data" / "critic.onnx"
log = logging.getLogger(__name__)


def model_path():
    return Path(os.environ.get("CHAMELEON_CRITIC_MODEL") or DEFAULT)


@lru_cache(maxsize=4)
def _session(path):
    if not Path(path).is_file():
        return None
    try:
        import onnxruntime as ort
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 2
        sess = ort.InferenceSession(str(path), opts, providers=["CPUExecutionProvider"])
    except Exception:
        log.exception("critic model %s could not be loaded; using the hand scorer", path)
        return None
    if sess.get_inputs()[0].shape[-1] != N_CONT:
        log.error("critic model %s expects %s features, critic.features makes %d; using the hand scorer",
                  path, sess.get_inputs()[0].shape[-1], N_CONT)
        return None
    return sess


def available(path=None):
    return _session(str(path or model_path())) is not None


def scores(source, target, outputs, a, path=None):
    """One score per output (higher = better). a = engine.analyze(source), shared by every call for a case."""
    sess = _session(str(path or model_path()))
    if sess is None or not outputs:
        return [score(source, target, o)["total"] for o in outputs]
    enc = [encode(a, o) for o in outputs]
    feed = {"cont": np.stack([e[0] for e in enc]).astype(np.float32), "cat": np.stack([e[1] for e in enc]).astype(np.int64),
            "mask": np.stack([e[2] for e in enc]).astype(np.float32)}
    return [float(s) for s in sess.run(["score"], feed)[0]]
