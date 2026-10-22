"""Scripted exclusion, partial-match and feature-cache alignment audit."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from generator.download import digest
from generator.features import ROOT, files, load, SOURCES
from generator.make_data import atomic_json
from generator.match_real import compatible, maximum_matching
from generator.pair_data import cached_rows, PHASE1
from generator.partial_pairs import ROOT as PARTIAL
from generator.phase2b import ROOT as PREVIOUS
from generator.verify_data import verify as original_audit

def run()->None:
    leakage=original_audit(PHASE1)
    originals={r['design_hash']:r for r in cached_rows()};keys={}
    for path in sorted((PREVIOUS/'real_descriptors').glob('*.json')):keys.update(json.loads(path.read_text())['group_keys'])
    checked=0
    for path in sorted(PARTIAL.glob('real*.parquet')):
        for batch in pq.ParquetFile(path).iter_batches(batch_size=32):
            for row in batch.to_pylist():
                a,b=originals[row['source_design_hash']],originals[row['design_hash']]
                assert a['split']==b['split']==row['split'] and a['campaign_hash']==b['campaign_hash']==row['campaign_hash']
                mask=row['matched'];mapping=row['target_group_indices'];g=a['groups'];h=b['groups']
                assert sum(mask)>=.6*len(g) and sum(mask)>=.6*len(h)
                assert row['source_groups']==g
                edges=[[j for j in range(len(h)) if compatible(x,keys[a['design_hash']][i],h[j],keys[b['design_hash']][j])] for i,x in enumerate(g)]
                cardinality=len(maximum_matching(edges));chosen=[]
                for i,(j,m) in enumerate(zip(mapping,mask)):
                    if m:
                        assert j in edges[i]
                        assert len(maximum_matching(edges,(i,j)))<cardinality,'ambiguous edge received loss'
                        assert row['target_boxes'][i]==h[j]['box'];chosen.append(j)
                    else:
                        assert j==-1 and row['target_boxes'][i]==[0.,0.,0.,0.]
                assert len(chosen)==len(set(chosen))
                checked+=1
    data=load();position=0
    for path in files():
        for batch in pq.ParquetFile(path).iter_batches(batch_size=32):
            for row in batch.to_pylist():
                n=len(row['source_groups'])
                assert int(data['split'][position])==int(row['split']=='val')
                assert int(data['source'][position])==SOURCES.index(row['source_kind'])
                assert np.array_equal(data['target'][position,:n],np.array(row['target_boxes'],dtype=np.float32))
                assert np.array_equal(data['matched'][position,:n],row.get('matched',[True]*n))
                assert data['valid'][position].sum()==n
                position+=1
    assert position==len(data['split'])
    result={'leakage':leakage,'partial_and_strict_pairs_checked':checked,'feature_rows_checked':position,
            'ambiguous_groups_receive_loss':False,'unmatched_groups_retained_as_inputs':True}
    atomic_json(ROOT/'leakage.json',result)
    print('PASS: training-data audit',json.dumps(result),flush=True)

if __name__=='__main__':run()
