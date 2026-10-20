"""Train the layout critic with a pairwise ranking loss: in every group, the positive should outscore each
of its negatives (loss = mean softplus(score_neg - score_pos), i.e. pairwise logistic).

    python -m critic.train --config critic/configs/layout_small.yaml
    python -m critic.train --config critic/configs/layout_small.yaml --smoke     # tiny subset, 20 epochs, about a minute

Reads the shards critic.make_data wrote (data.dir/{train,val}/shard_*.npz). Device: MPS when available,
else CPU (--device to force). Fixed seed. Each epoch: validation loss and pairwise accuracy (overall and
per negative kind) on the val split; writes out_dir/log.csv, out_dir/last.pt, and out_dir/best.pt when val
pairwise accuracy improves. --resume continues from out_dir/last.pt.
Hand labels are never read here (they are for critic.eval only).
"""

import argparse
import csv
import json
import math
import random
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
import yaml

from critic.damage import KINDS
from critic.features import CONT
from critic.model import build, n_params

REPO = Path(__file__).resolve().parents[1]


def load_split(d):
    """(cont, cat, mask, kind, groups) with groups = [(positive index, [negative indices])]."""
    files = sorted(Path(d).glob("shard_*.npz"))
    if not files:
        raise SystemExit(f"no shards in {d}: run python -m critic.make_data first")
    cont, cat, mask, kind, groups, base = [], [], [], [], [], 0
    for f in files:
        z = np.load(f)
        cont.append(z["cont"]); cat.append(z["cat"]); mask.append(z["mask"]); kind.append(z["kind"])
        for g in np.unique(z["group"]):
            idx = np.nonzero(z["group"] == g)[0]
            pos = [i for i in idx if z["kind"][i] == 0]
            neg = [int(i) + base for i in idx if z["kind"][i] != 0]
            if len(pos) == 1 and neg:
                groups.append((int(pos[0]) + base, neg))
        base += len(z["kind"])
    return (torch.from_numpy(np.concatenate(cont).astype(np.float32)), torch.from_numpy(np.concatenate(cat).astype(np.int64)),
            torch.from_numpy(np.concatenate(mask).astype(np.float32)), np.concatenate(kind), groups)


def batches(groups, size, max_neg, rng):
    order = list(range(len(groups)))
    rng.shuffle(order)
    for s in range(0, len(order), size):
        yield [(groups[g][0], rng.sample(groups[g][1], min(max_neg, len(groups[g][1])))) for g in order[s:s + size]]


def pair_scores(model, data, batch, device):
    """(positive scores, negative scores, negative indices), each [pairs]."""
    cont, cat, mask = data[:3]
    idx = sorted({i for p, ns in batch for i in [p, *ns]})
    where = {i: k for k, i in enumerate(idx)}
    t = torch.tensor(idx)
    s = model(cont[t].to(device), cat[t].to(device), mask[t].to(device))
    p = torch.tensor([where[p] for p, ns in batch for _n in ns], device=device)
    n = torch.tensor([where[n] for _p, ns in batch for n in ns], device=device)
    return s[p], s[n], [n for _p, ns in batch for n in ns]


def evaluate(model, data, device, size=128):
    model.eval()
    loss = right = n = 0.0
    per = {}
    with torch.no_grad():
        for b in batches(data[4], size, 10 ** 6, random.Random(0)):
            sp, sn, negs = pair_scores(model, data, b, device)
            loss += F.softplus(sn - sp).sum().item()
            ok = (sp > sn).float().cpu().numpy()
            right += float(ok.sum()); n += len(ok)
            for k, o in zip(data[3][negs], ok):
                c = per.setdefault(KINDS[k], [0, 0]); c[0] += float(o); c[1] += 1
    model.train()
    return loss / max(n, 1), right / max(n, 1), {k: c[0] / c[1] for k, c in sorted(per.items())}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=REPO / "critic" / "configs" / "layout_small.yaml")
    ap.add_argument("--smoke", action="store_true", help="tiny subset (200 train / 50 val groups), 20 epochs")
    ap.add_argument("--device", help="cpu | mps | cuda (default: mps when available, else cpu)")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--max-minutes", type=float, help="stop after the epoch that passes this wall time")
    args = ap.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    tc = cfg["train"]
    random.seed(tc["seed"]); np.random.seed(tc["seed"]); torch.manual_seed(tc["seed"])
    torch.set_num_threads(tc.get("num_threads", 4))
    device = torch.device(args.device or ("mps" if torch.backends.mps.is_available() else "cpu"))
    data_dir, out = (REPO / cfg["data"]["dir"]).resolve(), (REPO / cfg["out_dir"]).resolve()
    if args.smoke:
        out = out.parent / (out.name + "_smoke")
    out.mkdir(parents=True, exist_ok=True)

    train, val = load_split(data_dir / "train"), load_split(data_dir / "val")
    epochs = tc["epochs"]
    if args.smoke:
        rs = random.Random(0)
        train = (*train[:4], rs.sample(train[4], min(200, len(train[4]))))
        val = (*val[:4], rs.sample(val[4], min(50, len(val[4]))))
        epochs = 20
    model = build(cfg).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=tc["lr"], weight_decay=tc["weight_decay"])
    steps = epochs * math.ceil(len(train[4]) / tc["batch_groups"])
    warm = min(tc["warmup_steps"], max(1, steps // 10))  # short runs (--smoke) still reach the full rate
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / warm)
                                              * 0.5 * (1 + math.cos(math.pi * min(1.0, s / max(1, steps)))))
    start_epoch, best = 0, -1.0
    if args.resume and (out / "last.pt").exists():
        ck = torch.load(out / "last.pt", map_location=device)
        model.load_state_dict(ck["model"]); opt.load_state_dict(ck["opt"]); sched.load_state_dict(ck["sched"])
        start_epoch, best = ck["epoch"] + 1, ck["best"]
    print(f"{n_params(model) / 1e6:.2f}M parameters on {device}; {len(train[4])} train / {len(val[4])} val groups; "
          f"{epochs} epochs -> {out}", flush=True)
    log = out / "log.csv"
    new_log = not log.exists() or start_epoch == 0
    rng, t0 = random.Random(tc["seed"] + start_epoch), time.time()
    with log.open("w" if new_log else "a", newline="") as fh:
        w = csv.writer(fh)
        if new_log:
            w.writerow(["epoch", "train_loss", "val_loss", "val_pair_acc", "per_kind_acc", "lr", "minutes"])
        for epoch in range(start_epoch, epochs):
            tot = n = 0.0
            for b in batches(train[4], tc["batch_groups"], tc["max_negatives"], rng):
                sp, sn, _ = pair_scores(model, train, b, device)
                loss = F.softplus(sn - sp).mean()
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), tc["grad_clip"])
                opt.step(); sched.step()
                tot += loss.item() * len(sp); n += len(sp)
            vl, va, per = evaluate(model, val, device)
            mins = (time.time() - t0) / 60
            w.writerow([epoch, round(tot / max(n, 1), 4), round(vl, 4), round(va, 4), json.dumps({k: round(float(v), 3) for k, v in per.items()}),
                        f"{sched.get_last_lr()[0]:.2e}", round(mins, 2)])
            fh.flush()
            ck = {"model": model.state_dict(), "opt": opt.state_dict(), "sched": sched.state_dict(), "epoch": epoch,
                  "best": max(best, va), "config": cfg, "features": [n for n, _d in CONT]}
            torch.save(ck, out / "last.pt")
            if va > best:
                best = va
                torch.save(ck, out / "best.pt")
            print(f"epoch {epoch}: train {tot / max(n, 1):.4f}  val {vl:.4f}  val pair acc {va:.3f}  ({mins:.1f} min)", flush=True)
            if args.max_minutes and mins > args.max_minutes:
                print("time limit reached")
                break
    print(f"best val pairwise accuracy {best:.3f}; checkpoints in {out}")


if __name__ == "__main__":
    main()
