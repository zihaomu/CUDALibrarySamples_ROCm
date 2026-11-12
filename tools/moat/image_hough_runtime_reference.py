#!/usr/bin/env python3
"""Recompute every returned small-image Hough peak from independent CPU votes."""
import json,math
import numpy as np
from experiment import ROOT,Experiment,write
from image_progress import record

def expected():
    w=h=16;rows=math.ceil(math.sqrt(2.)*16);edge=np.zeros((h,w),np.uint8);edge[8,:]=255
    yy,xx=np.nonzero(edge);votes=np.zeros((180,rows),np.int32)
    for theta in range(180):
        c=np.float32(math.cos(theta*math.pi/180));s=np.float32(math.sin(theta*math.pi/180))
        rho=np.rint((xx.astype(np.float32)-8)*c+(yy.astype(np.float32)-8)*s).astype(np.int32)+(rows>>1)
        votes[theta]=np.bincount(rho,minlength=rows)
    peaks=[]
    for theta,rho in np.argwhere(votes>=8):
        v=votes[theta,rho]
        if any(votes[t,r]>v or (votes[t,r]==v and (t,r)<(theta,rho))
               for t in range(max(0,theta-1),min(180,theta+2))
               for r in range(max(0,rho-1),min(rows,rho+2)) if (t,r)!=(theta,rho)):
            continue
        peaks.append((int(rho),int(theta),int(v)))
    return sorted(peaks,key=lambda p:(p[1],p[0]))

def main():
    run=json.loads((ROOT/'migration/reports/image-hough-runtime.json').read_text())
    wanted=expected();rows=run['rows'];actual=[tuple(map(int,p.split(','))) for p in rows[0][3:]]
    restored=[tuple(map(int,p.split(','))) for p in rows[2][3:]]
    checks=[dict(check='independent-complete-peak-set',passed=actual==wanted,expected=wanted,actual=actual),
            dict(check='changed-input-zero-and-restored-peak-set',passed=rows[1]==['changed-to-zero','0','0'] and restored==wanted),
            dict(check='eleven-actual-runtime-cases',passed=run['status']=='PASSED' and run['case_count']==11),
            dict(check='physical-GPU1',passed={d['physical_id'] for d in json.loads((ROOT/run['evidence']/'backend.observed.json').read_text())['devices']}=={1})]
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED'
    e=Experiment('I3','Hough-runtime-independent-CPU-all-peaks','CPU-reference',parent=run['evidence'].split('/')[-1],
                 sources=[__file__,ROOT/'migration/reports/image-hough-runtime.json',ROOT/'tools/moat/image_hough_runtime.cpp'])
    result=dict(status=status,checks=checks,peak_count=len(wanted),runtime_evidence=run['evidence'])
    write(e.path/'results.json',result)
    result['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks))
    write(ROOT/'migration/reports/image-hough-runtime-validation.json',result)
    record('I3','Hough运行合同正常/变化/恢复的全部GPU峰由独立CPU完整重算：'+status+'；其余8类非法跨度/参数真实拒绝。',[result['evidence']])
    print(status,len(wanted))
    return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
