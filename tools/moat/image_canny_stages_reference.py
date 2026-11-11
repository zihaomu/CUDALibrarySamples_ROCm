#!/usr/bin/env python3
"""Independent NumPy oracle for staged gradients; never imported by GPU code."""
import json
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_progress import record
from image_validation import coverage,file_set,fixture_identity,array_check

def reference(fixture):
    config=json.loads((fixture/'config.json').read_text())
    w,h,c,pitch=[config[k] for k in ['width','height','channels','pitch']]
    data=np.fromfile(fixture/'input.bin',np.uint8).reshape(h,pitch)[:,:w*c].reshape(h,w,c).astype(np.int64)
    padded=np.pad(data,((1,1),(1,1),(0,0)),mode='edge')
    # Explicit convolution kernels keep the oracle independent of device loops.
    sx=np.array([[-1,0,1],[-2,0,2],[-1,0,1]])
    sy=sx.T
    dx=sum(sx[j,i]*padded[j:j+h,i:i+w] for j in range(3) for i in range(3))
    dy=sum(sy[j,i]*padded[j:j+h,i:i+w] for j in range(3) for i in range(3))
    squared=dx**2+dy**2
    best=np.argmax(squared,axis=2)[:,:,None]
    dx=np.take_along_axis(dx,best,2)[:,:,0]
    dy=np.take_along_axis(dy,best,2)[:,:,0]
    mag=np.floor(np.sqrt(np.take_along_axis(squared,best,2)[:,:,0].astype(np.float64))).astype(np.uint16)
    # Test integer-root defining inequalities, including perfect squares.
    norm=dx**2+dy**2
    assert np.all(mag.astype(np.int64)**2<=norm)
    assert np.all((mag.astype(np.int64)+1)**2>norm)
    horizontal=np.abs(dy)*32768<np.abs(dx)*13573
    vertical=np.abs(dy)*32768>np.abs(dx)*(13573+65536)
    same=dx*dy>=0
    p=np.pad(mag,1,mode='edge')
    a=np.where(horizontal,p[1:-1,:-2],np.where(vertical,p[:-2,1:-1],np.where(same,p[:-2,:-2],p[:-2,2:])))
    b=np.where(horizontal,p[1:-1,2:],np.where(vertical,p[2:,1:-1],np.where(same,p[2:,2:],p[2:,:-2])))
    return dict(dx=dx.astype(np.int16),dy=dy.astype(np.int16),magnitude=mag,
                suppressed=np.where((mag>=a)&(mag>=b),mag,0).astype(np.uint16))

def validate_run(row,case):
    checks=[dict(check='GPU-process-exit',passed=row.get('return_code')==0)]
    fixture=ROOT/row['inputs'];output=ROOT/row['outputs']
    names={name+'.bin' for name in ['dx','dy','magnitude','suppressed']}
    checks += [fixture_identity(fixture,case['manifest_sha256']),file_set(output,names),
               dict(check='complete-output-hash-map',passed=set(row.get('output_sha256',{}))==names)]
    if all(c['passed'] for c in checks):
        try:
            for name,expected in reference(fixture).items():
                checks.append(array_check(output/(name+'.bin'),expected,row['output_sha256'][name+'.bin']))
        except (OSError,ValueError,KeyError) as error:checks.append(dict(check='read-complete-arrays',passed=False,error=repr(error)))
    return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,
                scope='Stage correctness only. Native hysteresis, full sample CLI and Python workloads remain pending.')

def main():
    results=[];plan=ROOT/'migration/rewrite/image-canny-stage-cases.json'
    cases=json.loads(plan.read_text())['cases'];rows=json.loads((ROOT/'migration/reports/image-I1-Canny-stages-runs.json').read_text())
    required={c['case']:c for c in cases};complete=coverage(rows,cases)
    if not complete['passed']:
        e=Experiment('I1','Canny-stages-case-coverage','CPU-reference',sources=[__file__,plan,ROOT/'tools/moat/image_validation.py'])
        validation=dict(status='FAILED',checks=[complete]);ref=e.finish('CONTRACT_AUDIT_FAILED',validation)
        write(ROOT/'migration/reports/image-I1-Canny-stages-validation.json',[dict(case='case-coverage',**validation,evidence=ref)])
        record('I1','阶段验收拒绝不完整或重复case集合。',[ref]);return 1
    for row in rows:
        e=Experiment('I1','Canny-stages-independent-CPU','CPU-reference',case=row['case'],
                     sources=[__file__,ROOT/'migration/rewrite/image-canny-stages-contract.json',plan,ROOT/'tools/moat/image_validation.py'],parent=row['experiment_id'])
        validation=validate_run(row,required[row['case']])
        ref=e.finish('PASSED' if validation['status']=='PASSED' else 'NUMERIC_MISMATCH',validation)
        result=dict(case=row['case'],**validation,evidence=ref,parent=row['evidence']);results.append(result)
        write(ROOT/'migration/reports/image-I1-Canny-stages-validation.json',results)
        record('I1',row['case']+'：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU'+('逐元素完全一致；此结论仅覆盖阶段。' if validation['status']=='PASSED' else '存在差异，保留失败坐标。'),[ref])
    return int(not results or any(r['status']!='PASSED' for r in results))

if __name__=='__main__':raise SystemExit(main())
