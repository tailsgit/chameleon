"""Linear-embedded group transformer and conditional variational box decoder."""
from __future__ import annotations
import math
import torch
from torch import nn
from generator.features import N_CONT, KINDS, ROLES

class Block(nn.Module):
    def __init__(self, d: int, heads: int) -> None:
        super().__init__(); self.heads=heads
        self.n1=nn.LayerNorm(d); self.n2=nn.LayerNorm(d)
        self.qkv=nn.Linear(d,3*d); self.proj=nn.Linear(d,d)
        self.ff=nn.Sequential(nn.Linear(d,4*d),nn.GELU(),nn.Linear(4*d,d))
    def forward(self,h:torch.Tensor,bias:torch.Tensor)->torch.Tensor:
        b,t,d=h.shape
        q,k,v=self.qkv(self.n1(h)).reshape(b,t,3,self.heads,d//self.heads).permute(2,0,3,1,4).unbind(0)
        weights=torch.softmax(q@k.transpose(-1,-2)/math.sqrt(d//self.heads)+bias,dim=-1)
        h=h+self.proj((weights@v).transpose(1,2).reshape(b,t,d))
        return h+self.ff(self.n2(h))

def uniform_fit(cont:torch.Tensor,canvas:torch.Tensor)->torch.Tensor:
    sx=torch.exp(canvas[:,2]-canvas[:,0]);sy=torch.exp(canvas[:,3]-canvas[:,1]);k=torch.minimum(sx,sy)
    f=torch.stack([k/sx,k/sy,k/sx,k/sy],-1)[:,None]
    offset=torch.stack([(1-k/sx)/2,(1-k/sy)/2,torch.zeros_like(k),torch.zeros_like(k)],-1)[:,None]
    return cont[...,:4]*f+offset

class Generator(nn.Module):
    def __init__(self,d:int=192,layers:int=3,heads:int=4,latent:int=16,seed:int=2026)->None:
        super().__init__();self.latent=latent
        self.embedding=nn.Linear(N_CONT,d)  # No raw-data LayerNorm, including posterior/canvas paths.
        self.kind=nn.Embedding(len(KINDS),d);self.role=nn.Embedding(len(ROLES),d)
        self.canvas_embedding=nn.Linear(5,d);self.source_embedding=nn.Embedding(4,d)
        self.blocks=nn.ModuleList(Block(d,heads) for _ in range(layers))
        self.target_embedding=nn.Linear(5,d);self.posterior=Block(d,heads)
        self.mu=nn.Linear(d,latent);self.logvar=nn.Linear(d,latent)
        self.decoder=nn.Sequential(nn.Linear(d+latent,2*d),nn.GELU(),nn.Linear(2*d,d),nn.GELU(),nn.Linear(d,4))
        nn.init.zeros_(self.decoder[-1].weight);nn.init.zeros_(self.decoder[-1].bias)
        rng=torch.Generator().manual_seed(seed)
        self.register_buffer("latents",torch.randn(16,latent,generator=rng))
    def encode(self,cont:torch.Tensor,cat:torch.Tensor,valid:torch.Tensor,canvas:torch.Tensor,source:torch.Tensor)->tuple[torch.Tensor,torch.Tensor]:
        h=self.embedding(cont)+self.kind(cat[...,0])+self.role(cat[...,1])
        h=torch.cat([self.canvas_embedding(canvas)[:,None],self.source_embedding(source)[:,None],h],1)
        mask=torch.cat([torch.ones_like(valid[:,:2]),valid],1)
        bias=(1-mask)[:,None,None,:]*-1e4
        for block in self.blocks:h=block(h,bias)
        return h,bias
    def decode(self,h:torch.Tensor,z:torch.Tensor,base:torch.Tensor)->torch.Tensor:
        h=h[:,2:]
        zz=z[:,None,:].expand(-1,h.shape[1],-1)
        delta=self.decoder(torch.cat([h,zz],-1))
        # Positive sizes, without clipping real bleeds or coordinates to [0,1].
        sizes=torch.nn.functional.softplus(torch.log(torch.exp(base[...,2:].clamp(min=1e-5,max=20))-1)+delta[...,2:])
        return torch.cat([base[...,:2]+delta[...,:2],sizes],-1)
    def training_output(self,cont:torch.Tensor,cat:torch.Tensor,valid:torch.Tensor,canvas:torch.Tensor,source:torch.Tensor,
                        target:torch.Tensor,matched:torch.Tensor,epsilon:torch.Tensor)->tuple[torch.Tensor,torch.Tensor,torch.Tensor]:
        h,bias=self.encode(cont,cat,valid,canvas,source)
        target_input=torch.cat([target*matched[...,None],matched[...,None]],-1)
        post=h+torch.cat([torch.zeros_like(h[:,:2]),self.target_embedding(target_input)],1)
        post=self.posterior(post,bias)[:,2:]
        pooled=(post*matched[...,None]).sum(1)/matched.sum(1,keepdim=True).clamp(min=1)
        mu=self.mu(pooled);logvar=self.logvar(pooled).clamp(-8,4)
        z=mu+torch.exp(.5*logvar)*epsilon
        return self.decode(h,z,uniform_fit(cont,canvas)),mu,logvar
    def forward(self,cont:torch.Tensor,cat:torch.Tensor,valid:torch.Tensor,canvas:torch.Tensor,source:torch.Tensor)->torch.Tensor:
        h,_bias=self.encode(cont,cat,valid,canvas,source)
        b,t,d=h.shape; samples=self.latents.shape[0]
        repeated=h[:,None].expand(-1,samples,-1,-1).reshape(b*samples,t,d)
        z=self.latents[None].expand(b,-1,-1).reshape(b*samples,self.latent)
        base=uniform_fit(cont,canvas)[:,None].expand(-1,samples,-1,-1).reshape(b*samples,t-2,4)
        return self.decode(repeated,z,base).reshape(b,samples,t-2,4)

def loss_terms(pred:torch.Tensor,target:torch.Tensor,matched:torch.Tensor,cat:torch.Tensor,
               mu:torch.Tensor,logvar:torch.Tensor)->tuple[torch.Tensor,torch.Tensor,torch.Tensor]:
    l1=(torch.abs(pred-target)*matched[...,None]).sum((1,2))/(4*matched.sum(1).clamp(min=1))
    def overlaps(boxes):
        lo=torch.maximum(boxes[:,:,None,:2],boxes[:,None,:,:2])
        hi=torch.minimum((boxes[...,:2]+boxes[...,2:])[:,:,None],(boxes[...,:2]+boxes[...,2:])[:,None])
        inter=(hi-lo).clamp(min=0).prod(-1)
        area=boxes[...,2:].prod(-1).clamp(min=1e-5)
        return inter/torch.minimum(area[:,:,None],area[:,None,:])
    active=matched*(cat[...,0]>1)
    pairmask=active[:,:,None]*active[:,None,:]*(1-torch.eye(pred.shape[1],device=pred.device))[None]
    overlap=((overlaps(pred)-overlaps(target)-.02).clamp(min=0)*pairmask).sum()/pairmask.sum().clamp(min=1)
    kl=-.5*(1+logvar-mu.square()-logvar.exp()).mean()
    return l1.mean(),overlap,kl
