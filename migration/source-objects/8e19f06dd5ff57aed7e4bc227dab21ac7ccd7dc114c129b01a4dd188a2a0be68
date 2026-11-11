#!/usr/bin/env python3
"""A frozen local threshold hypothesis checked against separate native holdouts."""
import argparse,json
import numpy as np
from image_canny_stages_reference import reference
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def local_mask(stages,low,high,boundary_self=False):
    dx=stages['dx'].astype(np.int64);dy=stages['dy'].astype(np.int64)
    m=stages['suppressed'];ax=np.abs(dx);ay=np.abs(dy)
    horizontal=ay*32768<ax*13573;vertical=ay*32768>ax*(13573+65536)
    same=dx*dy>=0
    direction=np.where(horizontal,0,np.where(vertical,2,np.where(same,1,3)))
    def neighbors(values):
        p=np.pad(values,1,mode='edge')
        a=np.where(horizontal,p[1:-1,:-2],np.where(vertical,p[:-2,1:-1],np.where(same,p[:-2,:-2],p[:-2,2:])))
        b=np.where(horizontal,p[1:-1,2:],np.where(vertical,p[2:,1:-1],np.where(same,p[2:,2:],p[2:,:-2])))
        if boundary_self:
            yy,xx=np.indices(values.shape);ox=np.where(vertical,0,1);oy=np.where(horizontal,0,np.where(vertical,1,np.where(same,1,-1)))
            a=np.where((xx-ox<0)|(yy-oy<0)|(yy-oy>=len(values)),values,a)
            b=np.where((xx+ox>=values.shape[1])|(yy+oy<0)|(yy+oy>=len(values)),values,b)
        return a,b
    a,b=neighbors(m);da,db=neighbors(direction)
    connected=((a==m)&(da==direction))|((b==m)&(db==direction))
    return ((m>high)|((m>=low)&connected)).astype(np.uint8)*255

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--boundary-self',action='store_true');args=parser.parse_args()
    e=Experiment('I0','Canny-NPPPlus-local-threshold-hypothesis','CPU-research',sources=[__file__,ROOT/'tools/moat/image_canny_stages_reference.py'])
    cases={}
    for p in sorted((ROOT/'artifacts/rewrite/I0/Canny-NPPPlus-contract').glob('*/case-result.json')):
        row=json.loads(p.read_text())
        if row['return_code']==0:cases[row['case']]=row
    results=[]
    for name,row in cases.items():
        fixture=ROOT/row['input_snapshot'];config=json.loads((fixture/'config.json').read_text())
        output=local_mask(reference(fixture),config['low'],config['high'],args.boundary_self)
        p=ROOT/row['output']/'output.bin'
        native=np.fromfile(p,np.uint8).reshape(config['height'],config['output_pitch'])[:,:config['width']]
        mismatches=np.argwhere(output!=native)
        result=dict(case=name,mismatches=int(len(mismatches)),first_coordinates=mismatches[:16].tolist(),
                    native_sha256=digest(p),input_manifest_sha256=digest(fixture/'manifest.json'),
                    native_evidence='migration/reports/evidence/'+str((ROOT/row['output']).parent.relative_to(ROOT/'artifacts')),
                    native_nonzero=int(np.count_nonzero(native)),CPU_nonzero=int(np.count_nonzero(output)))
        results.append(result)
    result=dict(status='OBSERVED',hypothesis='Integer NMS; strong > high; weak >= low accepted for a same-magnitude neighbor along its gradient with the same direction bin. No recursive 8-neighbor propagation.',boundary_self=args.boundary_self,
                scope='Native contract research; does not qualify a sample or establish all thresholds, streams, sizes or image preprocessing.',cases=results)
    write(e.path/'local-model.json',result)
    ref=e.finish('OBSERVED')
    write(ROOT/('migration/reports/image-I0-Canny-local-model'+('-boundary-self' if args.boundary_self else '')+'.json'),dict(**result,evidence=ref))
    passed=sum(r['mismatches']==0 for r in results)
    record('I0',f'NPP+局部阈值假设在{passed}/{len(results)}个原图/研究/独立holdout上逐像素一致；方向相同的等值NMS邻居与强阈值分别检查。模型仍属合同调查，不作为整例资格。',[ref])
    print(json.dumps(results))

if __name__=='__main__':main()
