"""Focused integration contracts, independent of renderer and Crello content."""
import subprocess
import sys

import numpy as np

from engine.gen_candidates import features, project, geometry_cost, runtime
from generator.features import continuous, canvases
from generator.group_features import group_features
from generator.extract import group_features as training_group_features


def group(kind='rigid', aspect=2.):
    return dict(kind=kind, role='hero', box=[.1,.2,.3,.4], aspect=aspect,
                types=['image'],image_aspects=[2.],char_count=0,area_share=.12,
                z_order=0,parts=[],cols=0,floating=False,members=[0])


def test_shared_builders_and_padding():
    g=[group()]; a={'width':100,'height':200}; b={'width':300,'height':100}
    x=features(g,a,b)
    assert training_group_features is group_features
    np.testing.assert_array_equal(x['cont'][0,0],np.asarray(continuous(g[0]),np.float32))
    np.testing.assert_array_equal(x['canvas'][0],np.asarray(canvases({'canvas_a':[100,200],'canvas_b':[300,100]}),np.float32))
    assert x['source'].tolist()==[3]
    assert not x['cont'][0,1:].any() and not x['valid'][0,1:].any()


def test_projection_bounds_and_rigid_aspect():
    groups=[group(),group('background'),group('flow_text')]
    boxes=np.array([[-.4,.8,2.,1.],[-2,0,3,3],[.9,-.2,.8,.4]])
    p=project(groups,boxes,300,100)
    assert np.all(p[:,:2]>=0) and np.all(p[:,:2]+p[:,2:]<=1+1e-12)
    assert abs((p[0,2]*300)/(p[0,3]*100)-2)<1e-10
    np.testing.assert_array_equal(p[1],[0,0,1,1])
    assert geometry_cost(groups,p)>=0


def test_runtime_no_torch_or_pyarrow():
    code='import sys; from engine.gen_candidates import runtime; runtime(); assert "torch" not in sys.modules; assert "pyarrow" not in sys.modules'
    subprocess.run([sys.executable,'-c',code],check=True)
    sess,meta=runtime()
    assert sess.get_session_options().intra_op_num_threads==1
    assert len(meta['fixed_latents'])==16


def test_recipe_budget_is_applied_before_measuring(monkeypatch):
    from types import SimpleNamespace
    from engine import recipes
    hero=SimpleNamespace(floating=False,w=80,h=80)
    a=SimpleNamespace(sw=100,sh=100,by_role=lambda role:hero)
    calls=[]
    def make(*args,**kwargs):
        calls.append(1)
        return recipes.Plan('',{},[],[],1.,0.)
    for name in ['stack','split','anchor','strip']:monkeypatch.setattr(recipes,name,make)
    monkeypatch.setattr(recipes,'quiet_regions',lambda *a:[])
    monkeypatch.setattr(recipes,'preserve_plans',lambda *a:[])
    limits=[]
    monkeypatch.setattr(recipes,'retrieved',lambda *a,limit=None:limits.append(limit) or [])
    plans=recipes.generate(a,400,100,recipe_limit=5,retrieval_limit=3)
    assert len(calls)==len(plans)==5
    assert len(set(p.recipe for p in plans))>=3
    assert limits==[3]


def test_contrast_budget_keeps_legacy_default(monkeypatch):
    from engine import select as selection
    seen=[]
    def score(source,target,output,contrast=False):
        if contrast:seen.append(output['n'])
        return {'total':float(output['n'])}
    monkeypatch.setattr(selection,'score',score)
    monkeypatch.setattr(selection,'_passes',lambda *a:True)
    monkeypatch.setattr(selection,'_safest',lambda a,b,p:p)
    pool=[{'n':i} for i in range(12)]
    assert selection.select({}, {}, pool,render_limit=3)=={'n':11}
    assert seen==[11,10,9]
    seen.clear();selection.select({}, {}, pool)
    assert len(seen)==selection.RENDER_TOP==10


def test_rigid_member_visibility_floor_and_canvas_bounds():
    from types import SimpleNamespace
    from engine.gen_candidates import rigid_slot
    u=SimpleNamespace(id='group',w=580.,h=158.,cols=None,parts=[])
    sizer=SimpleNamespace(floor_scale=lambda unit:.75)  # a 2px member must remain 1.5px
    slot=rigid_slot(sizer,u,np.array([.9,.9,.2,.2]),600,200)
    assert 2*slot.scale>=1.5
    assert slot.x>=0 and slot.y>=0 and slot.x+slot.w<=600 and slot.y+slot.h<=200
    assert abs(slot.w/slot.h-u.w/u.h)<1e-12
    # If the floor cannot fit, use the largest uniform scale that can fit.
    small=rigid_slot(sizer,u,np.array([.1,.1,.01,.01]),100,20)
    assert small.w<=100 and small.h<=20
    assert abs(small.w/small.h-u.w/u.h)<1e-12
