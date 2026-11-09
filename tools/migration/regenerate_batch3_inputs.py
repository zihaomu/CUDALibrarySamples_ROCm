#!/usr/bin/env python3
"""Recreate the sparse inputs offline and check all 36 captured buffer hashes."""
import hashlib, json
from catalog import ROOT
from validate_blas import np

def regenerate(record):
    g={'original':700,'small-varied':23,'nonzero-initial':31}[record['case']]
    n=g*g;i=np.arange(n,dtype=np.int64)
    valid=np.stack([i>=g,i%g>0,np.ones(n,dtype=bool),i%g<g-1,i<n-g],axis=1)
    offsets=np.array([-g,-1,0,1,g]);columns=(i[:,None]+offsets)[valid].astype('<i4')
    ptr=np.r_[0,np.cumsum(valid.sum(axis=1))].astype('<i4')
    values=([-1.,-1.,4.+0.04,-1.,-1.] if '/cg/' in record['source'] else
            [-1.-0.3,-1.-0.2,4.+0.3+0.3+0.2,-1.,-1.])
    val=np.broadcast_to(np.array(values),(n,5))[valid].astype('<f8')
    known=np.ones(n) if record['case']=='original' else 1.+(i%17-8)/16.
    initial=np.zeros(n) if record['case']!='nonzero-initial' else 0.125+(i%7)/64.
    return {'input_rows.bin':ptr.tobytes(),'input_columns.bin':columns.tobytes(),
            'input_values.bin':val.tobytes(),'input_manufactured.bin':known.astype('<f8').tobytes(),
            'input_initial.bin':initial.astype('<f8').tobytes(),
            'input_rhs.bin':(ROOT/record['shared_rhs']).read_bytes()}

def main():
    records=json.loads((ROOT/'migration/reports/batch3-inputs.json').read_text())['fixtures'];checks=[]
    for r in records:
        data=regenerate(r)
        for name,expected in r['inputs'].items():
            actual={'sha256':hashlib.sha256(data[name]).hexdigest(),'bytes':len(data[name])}
            checks.append({'source':r['source'],'case':r['case'],'buffer':name,'passed':actual==expected,**actual})
    result={'status':'PASSED' if len(checks)==36 and all(x['passed'] for x in checks) else 'FAILED','checks':checks}
    (ROOT/'migration/reports/batch3-input-regeneration.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],sum(x['passed'] for x in checks),'/',len(checks),'input buffers')
    return result['status']!='PASSED'
if __name__=='__main__':raise SystemExit(main())
