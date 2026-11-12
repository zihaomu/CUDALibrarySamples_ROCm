#!/usr/bin/env python3
"""Execute every frozen original benchmark CLI with the real HIP binary."""
import json,shutil
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record

def main():
    profile=json.loads((ROOT/'migration/rewrite/image-benchmark-profile.json').read_text())
    build=json.loads((ROOT/'migration/reports/image-benchmark-build.json').read_text())
    if build['status']!='BUILT' or digest(ROOT/build['binary'])!=build['binary_sha256']:
        raise ValueError('current benchmark binary differs from sealed build')
    source=ROOT/profile['image'];assert digest(source)==profile['image_sha256']
    results=[]
    for case in profile['cases']:
        e=Experiment('I3','OpenCV-benchmark-complete-original-CLI','rocm-original',
                     case=case['case'],parent=build['experiment_id'],
                     sources=[__file__,ROOT/'migration/rewrite/image-benchmark-profile.json',
                              ROOT/'migration/reports/image-benchmark-build.json',source])
        write(e.path/'backend.observed.json',capture())
        images=e.path/'images';images.mkdir();shutil.copyfile(source,images/source.name)
        work=e.path/'outputs';work.mkdir()
        binary=ROOT/build['binary']
        rc=e.command([str(binary),*case['arguments']],'actual-four-operation-original-CLI',cwd=work,timeout=1800)
        products={p.name:dict(bytes=p.stat().st_size,sha256=digest(p)) for p in work.iterdir() if p.is_file()}
        checks=[dict(check='expected-return-code',passed=rc==case['expected_return_code']),
                dict(check='pinned-input-copied',passed=digest(images/source.name)==profile['image_sha256']),
                dict(check='complete-product-name-and-byte-size',passed={name:v['bytes'] for name,v in products.items()}==case['products'])]
        status='EXECUTED' if all(c['passed'] for c in checks) else 'FAILED'
        result=dict(case=case['case'],status=status,return_code=rc,arguments=case['arguments'],
                    build_evidence=build['evidence'],products=products,checks=checks)
        write(e.path/'run.json',result)
        result['evidence']=e.finish(('EXECUTED' if rc==0 else 'EXPECTED_REJECTION') if status=='EXECUTED' else 'RUNTIME_ERROR',
                                   dict(status=status,checks=checks))
        results.append(result)
        write(ROOT/'migration/reports/image-benchmark-runs.json',results)
        record('I3','OpenCV benchmark原例CLI '+case['case']+'：'+status+'；四算子产品/原始计时分别保存，速度比暂不资格。',[result['evidence']])
        print(case['case'],status,result['evidence'],flush=True)
    return int(any(r['status']!='EXECUTED' for r in results))

if __name__=='__main__':raise SystemExit(main())
