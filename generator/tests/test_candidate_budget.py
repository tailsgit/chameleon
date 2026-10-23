"""Quota coverage is independent of case identity, renderer and model weights."""
from types import SimpleNamespace
import pytest
from engine import candidate_budget as budget
from engine.recipes import Plan


def test_all_paths_precede_shared_extras(monkeypatch):
    analyses=[SimpleNamespace(units={'f':SimpleNamespace(emphasis=1)},panels={'p':[]}),
              SimpleNamespace(units={'f':SimpleNamespace(emphasis=1)},panels={})]
    def make(*args,**kwargs):return Plan('',{},[],['f'],1.,0.)
    def tasks(a,*args,**kw):
        return {'stack':[(make,'stack',{})], 'split':[(make,'split',{'vjust':'spread'}),(make,'split',{'vjust':'center'})]}
    monkeypatch.setattr(budget.recipes,'generate',tasks)
    monkeypatch.setattr(budget,'Sizer',lambda *a:object())
    monkeypatch.setattr(budget,'preserve_plans',lambda *args:[Plan('preserve',{'variant':v},[],['f'],1.,0.) for v in ['share','fit','edges','between']])
    monkeypatch.setattr(budget,'retrieved',lambda *args,**kw:[Plan('retrieved',{'rank':i},[],['f'],1.,0.) for i in [0,4,9,14,19,24,29]][:kw['limit']])
    rows=list(budget.schedule(analyses,{'width':100,'height':100},extra=0))
    assert {p.recipe for a,p,f,k in rows}=={'stack','split','preserve','retrieved'}
    assert {(analyses.index(a),p.knobs['variant']) for a,p,f,k in rows if p.recipe=='preserve'}=={(i,v) for i in [0,1] for v in ['share','fit','edges','between']}
    assert next(a for a,p,f,k in rows if p.recipe=='split') is analyses[1]
    assert next(p for a,p,f,k in rows if p.recipe=='split').knobs['vjust']=='center'
    assert {p.knobs['rank'] for a,p,f,k in rows if p.recipe=='retrieved'}=={0,4,9,14,19,24,29}
    assert next(a for a,p,f,k in rows if p.recipe=='retrieved' and p.knobs['rank']==19) is analyses[0]
    assert any(a is analyses[1] and p.recipe=='retrieved' for a,p,f,k in rows)
    assert {(f,k) for a,p,f,k in rows}=={(True,True),(True,False),(False,True),(False,False)}
    assert budget.LAST['extra']==0
    minimum=len(rows)
    assert len(list(budget.schedule(analyses,{'width':100,'height':100},extra=2)))==minimum+2


def test_retrieval_strata_reach_tail_and_keep_legacy_prefix(monkeypatch):
    from engine import retrieve
    designs=[{'aspect':1.,'roles':{},'units':[]} for _ in range(30)]
    monkeypatch.setattr(retrieve,'library',lambda:designs)
    a=SimpleNamespace(units={},sw=100,sh=100)
    assert [p.knobs['rank'] for p in retrieve.retrieved(a,object(),100,100,limit=7,spread=True)]==[0,4,9,14,19,24,29]
    assert [p.knobs['rank'] for p in retrieve.retrieved(a,object(),100,100,limit=4)]==[0,1,2,3]
    monkeypatch.setattr(retrieve,'library',lambda:designs[:23])
    assert 19 in [p.knobs['rank'] for p in retrieve.retrieved(a,object(),100,100,limit=7,spread=True)]


def test_shared_cap_cannot_disable_path_minima():
    with pytest.raises(ValueError):list(budget.schedule([],{},recipe_min=0))
