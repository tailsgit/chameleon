"""Export a trained critic checkpoint to ONNX, so the engine (and the Docker image) needs only onnxruntime.

    python -m critic.export --checkpoint ../data/critic/runs/layout_small/best.pt --out engine/data/critic.onnx

Inputs cont [B, T, F] float32, cat [B, T, 3] int64, mask [B, T] float32; output score [B]; the batch axis is
dynamic, T and F are fixed (critic.features). Afterwards the ONNX model is run with onnxruntime on random
inputs and compared with PyTorch (fails above TOLERANCE).
"""

import argparse
from pathlib import Path

import numpy as np
import torch

from critic.features import CONT, MAX_TOKENS, N_CONT, ROLES, TYPES
from critic.model import build

REPO = Path(__file__).resolve().parents[1]
TOLERANCE = 1e-3


def export(checkpoint, out):
    ck = torch.load(checkpoint, map_location="cpu")
    if ck["features"] != [n for n, _d in CONT]:
        raise SystemExit("checkpoint was trained on different features than critic.features makes now")
    model = build(ck["config"])
    model.load_state_dict(ck["model"])
    model.eval()
    g = torch.Generator().manual_seed(0)
    B = 3
    cont = torch.rand(B, MAX_TOKENS, N_CONT, generator=g)
    cat = torch.stack([torch.randint(0, n, (B, MAX_TOKENS), generator=g) for n in (len(TYPES), len(ROLES), MAX_TOKENS)], -1)
    mask = torch.ones(B, MAX_TOKENS)
    mask[:, 20:] = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(model, (cont, cat, mask), str(out), input_names=["cont", "cat", "mask"], output_names=["score"],
                      dynamic_axes={"cont": {0: "batch"}, "cat": {0: "batch"}, "mask": {0: "batch"}, "score": {0: "batch"}},
                      opset_version=17)
    import onnxruntime as ort
    sess = ort.InferenceSession(str(out), providers=["CPUExecutionProvider"])
    got = sess.run(["score"], {"cont": cont.numpy(), "cat": cat.numpy(), "mask": mask.numpy()})[0]
    with torch.no_grad():
        want = model(cont, cat, mask).numpy()
    diff = float(np.abs(got - want).max())
    if diff > TOLERANCE:
        raise SystemExit(f"ONNX and PyTorch disagree by {diff}")
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, epoch {ck['epoch']}); onnxruntime matches PyTorch within {diff:.1e}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=REPO / "engine" / "data" / "critic.onnx")
    args = ap.parse_args()
    export(args.checkpoint, args.out)


if __name__ == "__main__":
    main()
