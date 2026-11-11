#!/usr/bin/env python3
"""Compare actual native Sobel outputs with the separate NumPy stage oracle."""
import json
import numpy as np
from image_canny_stages_reference import reference
from experiment import ROOT,Experiment,write,digest
from image_progress import record
from image_validation import coverage,file_set,fixture_identity,array_check

def main():
    plan=ROOT/'migration/rewrite/image-native-gradient-cases.json';cases=json.loads(plan.read_text())['vendors']
    e=Experiment('I0','Canny-native-gradient-comparison','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_canny_stages_reference.py',ROOT/'tools/moat/image_validation.py',plan])
    checks=[]
    for suffix in ['', '-plus']:
        report=ROOT/('migration/reports/image-I0-Canny-native-probes'+suffix+'-gradients.json')
        vendor='NPP+' if suffix else 'NPP';rows=json.loads(report.read_text());required={r['case']:r for r in cases[vendor]}
        complete=coverage(rows,cases[vendor]);checks.append(dict(complete,check=vendor+'/complete-case-coverage'))
        if not complete['passed']:continue
        for row in rows:
            prefix=vendor+'/'+row['case']+'/'
            checks.append(dict(check=prefix+'process-exit',passed=row.get('return_code')==0))
            fixture=ROOT/row['input_snapshot'];out=ROOT/row['output']
            identity=fixture_identity(fixture,required[row['case']]['manifest_sha256'])
            files=file_set(out,['output.bin','native.json','native-x.bin','native-y.bin','native-magnitude.bin','native-angle.bin'])
            checks += [dict(identity,check=prefix+identity['check']),dict(files,check=prefix+files['check'])]
            if row.get('return_code')!=0 or not identity['passed'] or not files['passed']:continue
            try:
                expected=reference(fixture);seal=json.loads((out.parent/'sealed.json').read_text())['files']
                for name,oracle in [('x',-expected['dx']),('y',expected['dy']),('magnitude',expected['magnitude'])]:
                    path=out/('native-'+name+'.bin');check=array_check(path,oracle,seal['outputs/'+path.name]['sha256'])
                    checks.append(dict(check,check=prefix+name))
            except (OSError,KeyError,ValueError) as error:checks.append(dict(check=prefix+'read-arrays',passed=False,error=repr(error)))
    result=dict(status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED',checks=checks,
                scope='Gradient stages only. Native X is -CPU dx, native Y is CPU dy; no claim about native NMS or final Canny mask.')
    ref=e.finish('PASSED' if result['status']=='PASSED' else 'NUMERIC_MISMATCH',result)
    write(ROOT/'migration/reports/image-I0-native-gradients-validation.json',dict(**result,evidence=ref))
    record('I0','真实NPP/NPP+外部Sobel API与独立CPU梯度/整数幅度全数组对照：'+result['status']+'；明确X符号映射。此项不证明Canny内部NMS/连接阶段。',[ref])
    print(json.dumps(result))
    return int(result['status']!='PASSED')

if __name__=='__main__':raise SystemExit(main())
