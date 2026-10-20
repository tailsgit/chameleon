"""The layout critic: a small transformer over element tokens (critic.features) giving one score per design.

Input  cont [B, T, F] float, cat [B, T, 3] int64 (type, role, group), mask [B, T] float (1 = real token)
Output score [B] float: higher = better layout. Only differences between scores of layouts of the same
       source and target mean anything (it is trained with a ranking loss).

Each token = Linear(cont) + type, role and group embeddings. Pre-norm transformer blocks with masked
self-attention, then an MLP on the global token (token 0). Attention is written out (no
nn.MultiheadAttention) so ONNX export (critic.export) has no fast-path special cases.
"""

import math

import torch
from torch import nn

from critic.features import MAX_ELEMENTS, N_CONT, ROLES, TYPES


class Block(nn.Module):
    def __init__(self, d, heads, ff, dropout):
        super().__init__()
        self.heads = heads
        self.n1, self.n2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.qkv, self.proj = nn.Linear(d, 3 * d), nn.Linear(d, d)
        self.mlp = nn.Sequential(nn.Linear(d, ff), nn.GELU(), nn.Linear(ff, d))
        self.drop = nn.Dropout(dropout)

    def forward(self, h, bias):
        B, T, D = h.shape
        q, k, v = self.qkv(self.n1(h)).reshape(B, T, 3, self.heads, D // self.heads).permute(2, 0, 3, 1, 4)
        att = torch.softmax(q @ k.transpose(-1, -2) / math.sqrt(D // self.heads) + bias, dim=-1)
        h = h + self.drop(self.proj((att @ v).transpose(1, 2).reshape(B, T, D)))
        return h + self.drop(self.mlp(self.n2(h)))


class Critic(nn.Module):
    def __init__(self, d_model=192, layers=4, heads=4, ff=768, dropout=0.1):
        super().__init__()
        self.cont = nn.Linear(N_CONT, d_model)
        self.kind = nn.Embedding(len(TYPES), d_model)
        self.role = nn.Embedding(len(ROLES), d_model)
        self.group = nn.Embedding(MAX_ELEMENTS + 1, d_model)
        self.blocks = nn.ModuleList(Block(d_model, heads, ff, dropout) for _ in range(layers))
        self.head = nn.Sequential(nn.LayerNorm(d_model), nn.Linear(d_model, d_model), nn.GELU(), nn.Linear(d_model, 1))

    def forward(self, cont, cat, mask):
        h = self.cont(cont) + self.kind(cat[..., 0]) + self.role(cat[..., 1]) + self.group(cat[..., 2])
        bias = ((1.0 - mask) * -1e4)[:, None, None, :]  # padding tokens get no attention
        for blk in self.blocks:
            h = blk(h, bias)
        return self.head(h[:, 0]).squeeze(-1)


def build(cfg):
    """A Critic from the `model:` section of a config (critic/configs/*.yaml)."""
    return Critic(**cfg["model"])


def n_params(model):
    return sum(p.numel() for p in model.parameters())
