#!/usr/bin/env python3
"""Replay all benchmark contracts from a fixed clean Git checkout."""
import collections,json,os,shutil,tempfile
from pathlib import Path
from experiment import ROOT,Experiment,write,digest,git
from image_progress import record

REPORTS={'contracts':1,'deps':1,'build':1,'runs':6,'validation':6,'native-comparison':1,'runtime':1,'trace':1}
FILES={'contracts':'image-benchmark-contracts.json','deps':'image-I3-rocm-OpenCV.json',
       'build':'image-benchmark-build.json','runs':'image-benchmark-runs.json',
       'validation':'image-benchmark-validation.json','native-comparison':'image-benchmark-native-comparison.json',
       'runtime':'image-benchmark-runtime.json','trace':'image-benchmark-trace.json'}

def main():
    commit=git('rev-parse','HEAD').strip()
    scripts=[ROOT/'tools/moat'/('image_benchmark_'+name+'.py') for name in
       ['contracts','deps','build','run','reference','native_comparison','runtime','trace']]
    e=Experiment('I3','OpenCV-benchmark-fixed-Git-cold-four-operations-and-CPU','host-cold-replay',
       sources=[__file__,*scripts,ROOT/'migration/rewrite/image-benchmark-profile.json'])
    clone=Path(tempfile.mkdtemp(prefix='image-benchmark-cold-',dir=ROOT.parent))/'src'
    checks=[];children=[]
    rc=e.command(['git','clone','--shared','--quiet',str(ROOT),str(clone)],'fresh-checkout',timeout=300)
    try:
      if not rc:rc=e.command(['git','checkout','--quiet',commit],'fixed-commit',cwd=clone)
      checks.append(dict(check='no-preexisting-build-or-OpenCV-cache',passed=not (clone/'build').exists()))
      cpu=str(ROOT/'build/image-cpu-venv/bin/python')
      jobs=[('tools/moat/image_benchmark_contracts.py','cpu'),
            ('tools/moat/image_benchmark_deps.py','host'),
            ('tools/migration/bootstrap_sdk.py','gpu'),
            ('tools/moat/image_benchmark_build.py','gpu'),
            ('tools/moat/image_benchmark_run.py','gpu'),
            ('tools/moat/image_benchmark_reference.py','cpu'),
            ('tools/moat/image_benchmark_native_comparison.py','cpu'),
            ('tools/moat/image_benchmark_runtime.py','gpu'),
            ('tools/moat/image_benchmark_trace.py','gpu')]
      for name,kind in jobs:
        if rc:break
        if kind=='cpu':argv=[cpu,str(clone/name)];env=None
        elif kind=='host':argv=['python3',str(clone/name)];env=None
        else:
          argv=['/home/zihaomu/zihaomu_workspace/rocm10-launch.sh','env','ROCR_VISIBLE_DEVICES=3',
                'HIP_VISIBLE_DEVICES=0','python3',str(clone/name)]
          env=dict(os.environ,HIP_VISIBLE_DEVICES='2')
        rc=e.command(argv,'cold-'+Path(name).stem,cwd=clone,env=env,timeout=1800)
      checks.append(dict(check='all-nine-cold-jobs-success',passed=rc==0))
      if rc==0:
        checks.append(dict(check='identical-frozen-contract',passed=digest(clone/'migration/rewrite/image-benchmark-profile.json')
           ==digest(ROOT/'migration/rewrite/image-benchmark-profile.json')))
        for kind,file in FILES.items():
          rows=json.loads((clone/'migration/reports'/file).read_text());rows=rows if isinstance(rows,list) else [rows]
          for index,row in enumerate(rows):
            checks.append(dict(check=f'{kind}/{index}/status-and-proof',passed=row.get('status') in
              ('READY','FROZEN','BUILT','EXECUTED','PASSED') and bool(row.get('evidence'))))
            raw=clone/row['evidence'];manifest=json.loads((raw/'manifest.json').read_text())
            full=clone/manifest['raw_artifact_dir'];dest=e.path/'child-evidence'/kind/str(index)
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(full,dest)
            (dest/'sealed.json').rename(dest/'child-seal.json')
            for object_name in json.loads((dest/'source.json').read_text())['source_objects'].values():
              source=clone/object_name;target=ROOT/object_name
              if target.exists():
                if digest(source)!=digest(target):raise ValueError('source object collision')
              else:shutil.copyfile(source,target)
            children.append(dict(kind=kind,index=index,evidence=row['evidence'],raw=str(dest.relative_to(e.path))))
      counts=collections.Counter(c['kind'] for c in children)
      checks.append(dict(check='complete-18-child-inventory',passed=dict(counts)==REPORTS and len(children)==18))
      checks.append(dict(check='same-build-source-hashes',passed=rc==0 and
        json.loads((clone/'migration/reports/image-benchmark-build.json').read_text())['dependencies']==
        {name:digest(ROOT/name) for name in json.loads((ROOT/'migration/reports/image-benchmark-build.json').read_text())['dependencies']}))
    except Exception as error:checks.append(dict(check='cold-replay-finished',passed=False,error=repr(error)));rc=rc or 1
    checks.append(dict(check='final-return-code',passed=rc==0))
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED'
    result=dict(status=status,source_commit=commit,clone=str(clone),return_code=rc,checks=checks,children=children)
    write(e.path/'cold.json',result)
    result['evidence']=e.finish(status if status=='PASSED' else 'SELF_TEST_FAILED',dict(status=status,checks=checks))
    write(ROOT/'migration/reports/image-benchmark-cold.json',result)
    record('I3','benchmark固定Git冷检出同版OpenCV/四算子/六CLI/独立CPU/原生统计/运行/trace及18子封存：'+status,[result['evidence']])
    print(status,[(x['check'],x['passed']) for x in checks if not x['passed']],result['evidence']);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
