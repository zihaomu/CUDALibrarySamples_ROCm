#!/usr/bin/env python3
"""Inspect disagreement between native libraries on monotone heldout ramps."""
import json
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_completion_progress import record
from image_watershed_v2_reference import bound
from image_watershed_graph_reference import reference

def main():
    pp=ROOT/'migration/rewrite/image-watershed-completion-contract.json';p=json.loads(pp.read_text());paths={s:ROOT/f'migration/reports/image-watershed-completion-{s}.json' for s in ['native-NPP','native-NPPPlus','AMD-padded']};runs={s:json.loads(f.read_text()) for s,f in paths.items()}
    e=Experiment('I3','watershed-native-long-ramp-disagreement','CPU-diagnosis',sources=[__file__,pp,*paths.values(),ROOT/'tools/moat/image_watershed_v2_reference.py',ROOT/'tools/moat/image_watershed_graph_reference.py']);folders={s:bound(r) for s,r in runs.items()};rows=[]
    for item in p['inputs']:
        if item['id'] not in ['heldout-ramp-x','heldout-ramp-y','heldout-ramp-diagonal']:continue
        source=ROOT/item['path'];a=np.fromfile(source,np.uint8).reshape(item['height'],item['width']);expected,_=reference(a)
        row=dict(case=item['id'],source_sha256=digest(source),shape=list(a.shape),CPU_unique_gray=np.unique(expected['segments']).tolist(),sides={})
        for side,folder in folders.items():
            name=item['id']+('.segments' if side=='AMD-padded' else '-n8-m0-r0.segments');actual=np.fromfile(folder/name,np.uint8).reshape(a.shape);yy,xx=np.nonzero(actual!=expected['segments']);values,counts=np.unique(actual,return_counts=True)
            stats=dict(gray_values=dict(zip(map(str,values.tolist()),counts.tolist())),mismatched_pixels=len(xx),mismatch_bbox=None if not len(xx) else [int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())],top_row=actual[0].tolist(),left_column=actual[:,0].tolist(),bottom_row=actual[-1].tolist(),right_column=actual[:,-1].tolist())
            hypotheses={}
            for steps in [31,32,62,63,64,65,66]:
                y,x=np.indices(a.shape)
                if item['id'].endswith('ramp-x'):guess=np.maximum(x-steps,0)*3
                elif item['id'].endswith('ramp-y'):guess=np.maximum(y-steps,0)*3
                else:guess=np.maximum(x-steps,0)+np.maximum(y-steps,0)
                hypotheses[str(steps)]=bool(np.array_equal(guess.astype(np.uint8),actual))
            stats['fixed_descent_step_hypotheses']=hypotheses;row['sides'][side]=stats
        rows.append(row);print(json.dumps(row),flush=True)
    result=dict(status='OBSERVED',rows=rows,evidence_references=[r['evidence'] for r in runs.values()],scope='Failure diagnosis, no acceptance change. A strictly monotone ramp has a unique reachable minimum of zero for every pixel. Native disagreement must be resolved or explicitly reported before qualification.');write(e.path/'result.json',result);result['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-watershed-native-ramp-diagnosis.json',result)
    record('IMG-02','新保留集3条长坡度的NPP+差异已单独封存：输出值、位置、边缘行列与固定31–66步假设逐项记录。NPP/CPU/HIP结果同时绑定，暂不修订EXACT门槛或新增资格。',[result['evidence']])

if __name__=='__main__':main()
