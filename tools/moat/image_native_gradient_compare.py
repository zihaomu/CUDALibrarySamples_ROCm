#!/usr/bin/env python3
"""Compare actual native Sobel outputs with the separate NumPy stage oracle."""
import json
import numpy as np
from image_canny_stages_reference import reference
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def main():
    e=Experiment('I0','Canny-native-gradient-comparison','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_canny_stages_reference.py'])
    checks=[]
    for suffix in ['', '-plus']:
        report=ROOT/('migration/reports/image-I0-Canny-native-probes'+suffix+'-gradients.json')
        for row in json.loads(report.read_text()):
            fixture=ROOT/row['input_snapshot'];out=ROOT/row['output'];expected=reference(fixture)
            for name,oracle in [('x',-expected['dx']),('y',expected['dy']),('magnitude',expected['magnitude'])]:
                path=out/('native-'+name+'.bin');actual=np.fromfile(path,np.int16)
                mismatch=int(np.count_nonzero(actual.reshape(oracle.shape)!=oracle)) if actual.size==oracle.size else None
                checks.append(dict(check=('NPP+' if suffix else 'NPP')+'/'+row['case']+'/'+name,
                                   passed=mismatch==0,mismatches=mismatch,elements=int(oracle.size),native_sha256=digest(path)))
    result=dict(status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED',checks=checks,
                scope='Gradient stages only. Native X is -CPU dx, native Y is CPU dy; no claim about native NMS or final Canny mask.')
    ref=e.finish('PASSED' if result['status']=='PASSED' else 'NUMERIC_MISMATCH',result)
    write(ROOT/'migration/reports/image-I0-native-gradients-validation.json',dict(**result,evidence=ref))
    record('I0','真实NPP/NPP+外部Sobel API与独立CPU梯度/整数幅度全数组对照：'+result['status']+'；明确X符号映射。此项不证明Canny内部NMS/连接阶段。',[ref])
    print(json.dumps(result))

if __name__=='__main__':main()
