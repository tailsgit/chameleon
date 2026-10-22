import numpy as np
import torch
from generator.model import Generator, loss_terms
from generator.batches import epoch_indices

def inputs():
    torch.manual_seed(2026)
    return {"cont":torch.rand(2,5,16),"cat":torch.zeros(2,5,2,dtype=torch.long),"valid":torch.ones(2,5),
            "canvas":torch.zeros(2,5),"source":torch.tensor([0,3]),"target":torch.rand(2,5,4),
            "matched":torch.tensor([[1.,1.,1.,0.,0.],[1.,1.,0.,0.,0.]])}

def test_unmatched_targets_have_no_loss_or_posterior_effect():
    m=Generator(d=32,layers=1,heads=4);b=inputs();eps=torch.zeros(2,16)
    a=m.training_output(**b,epsilon=eps)
    losses=loss_terms(a[0],b['target'],b['matched'],b['cat'],a[1],a[2])
    b['target']=torch.where(b['matched'][...,None]>0,b['target'],torch.ones_like(b['target'])*9)
    changed=m.training_output(**b,epsilon=eps)
    assert all(torch.equal(x,y) for x,y in zip(a,changed))
    assert all(torch.equal(x,y) for x,y in zip(losses,loss_terms(changed[0],b['target'],b['matched'],b['cat'],changed[1],changed[2])))

def test_saved_latents_are_deterministic_and_model_size():
    m=Generator().eval();b=inputs()
    assert 1_000_000<=sum(p.numel() for p in m.parameters())<=3_000_000
    args=[b[k] for k in ('cont','cat','valid','canvas','source')]
    with torch.no_grad():
        assert torch.equal(m(*args),m(*args))
    assert m(*args).shape==(2,16,5,4)

def test_sampler_exact_shares_cap_and_seed():
    data={'split':np.zeros(120000),'source':np.repeat(np.arange(4),30000)}
    a=epoch_indices(data,0,2026);b=epoch_indices(data,1,2026)
    assert np.array_equal(a,epoch_indices(data,0,2026)) and not np.array_equal(a,b)
    assert np.bincount(data['source'][a[0]],minlength=4).tolist()==[24,24,16,16]
    assert np.sum(data['source'][a]==0)==30000
    assert len(np.unique(a[data['source'][a]==0]))==30000
    assert len(np.unique(a[data['source'][a]==1]))==30000

def test_early_linear_embedding_feeds_every_layernorm():
    m=Generator(d=32,layers=1,heads=4);b=inputs();seen=[]
    hooks=[p.register_forward_pre_hook(lambda mod,args: seen.append(args[0].requires_grad)) for p in m.modules() if isinstance(p,torch.nn.LayerNorm)]
    pred,mu,lv=m.training_output(**b,epsilon=torch.zeros(2,16))
    sum(loss_terms(pred,b['target'],b['matched'],b['cat'],mu,lv)).backward()
    assert seen and all(seen)
    assert all(torch.isfinite(p.grad).all() for p in m.parameters() if p.grad is not None)
    for h in hooks:h.remove()

def test_optimizer_checkpoint_continuation_is_identical():
    import copy
    from generator.batches import finite_step
    b=inputs();m=Generator(d=32,layers=1,heads=4)
    cfg={'seed':2026,'kl_weight':.001,'kl_warmup_steps':5000,'overlap_weight':.01,'grad_clip':1.}
    opt=torch.optim.AdamW(m.parameters(),lr=.0003)
    finite_step(m,opt,b,1,cfg)
    weights=copy.deepcopy(m.state_dict());moments=copy.deepcopy(opt.state_dict())
    finite_step(m,opt,b,2,cfg)
    other=Generator(d=32,layers=1,heads=4);other.load_state_dict(weights)
    other_opt=torch.optim.AdamW(other.parameters(),lr=.0003);other_opt.load_state_dict(moments)
    finite_step(other,other_opt,b,2,cfg)
    assert all(torch.equal(x,y) for x,y in zip(m.state_dict().values(),other.state_dict().values()))
