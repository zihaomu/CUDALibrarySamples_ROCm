#!/usr/bin/env python3
"""Replay the full Hough GPU entry and CPU readers from a clean fixed checkout."""
import json,os,shutil,tempfile
from pathlib import Path
from experiment import ROOT,Experiment,write,digest,git
from image_progress import record

GROUPS=['contracts','build','runs','validation','options','runtime','runtime-validation','trace']

def reports(clone):
    for name in GROUPS:
        p=clone/'migration/reports'/('image-hough-'+name+'.json')
        if not p.is_file():raise ValueError('missing cold report '+name)
        v=json.loads(p.read_text())
        if name=='options':
            for i,row in enumerate(v):
                for field in ['run','validation']:yield f'options-{field}',i,row[field]
        elif isinstance(v,list):
            for i,row in enumerate(v):yield name,i,row
        else:yield name,0,v

def main():
    commit=git('rev-parse','HEAD').strip()
    sources=[__file__,*[ROOT/'tools/moat'/p for p in
             ['image_hough_contracts.py','image_hough_build.py','image_hough_run.py',
              'image_hough_reference.py','image_hough_options.py','image_hough_runtime.py',
              'image_hough_runtime_reference.py','image_hough_trace.py']],
             ROOT/'migration/rewrite/image-hough-profile.json']
    e=Experiment('I3','Hough-clean-fixed-checkout-all-CLI-CPU-runtime-trace',
                 'host-cold-replay',sources=sources)
    clone=Path(tempfile.mkdtemp(prefix='image-hough-cold-',dir=ROOT.parent))/'src'
    children=[];checks=[]
    rc=e.command(['git','clone','--shared','--quiet',str(ROOT),str(clone)],'fresh-checkout',timeout=300)
    try:
        if not rc:rc=e.command(['git','checkout','--quiet',commit],'fixed-commit',cwd=clone)
        checks.append(dict(check='no-preexisting-build-or-library-cache',passed=not (clone/'build').exists()))
        cpu=str(ROOT/'build/image-cpu-venv/bin/python')
        if not rc:rc=e.command([cpu,str(clone/'tools/moat/image_hough_contracts.py')],
                                'regenerate-fixed-contract-and-RAW-inputs',cwd=clone,timeout=180)
        expected=ROOT/'migration/rewrite/image-hough-profile.json'
        checks.append(dict(check='identical-frozen-contract-and-five-RAW-fixtures',
                           passed=rc==0 and digest(clone/'migration/rewrite/image-hough-profile.json')==digest(expected)
                           and all(digest(clone/'tests/fixtures/image-hough'/p.name)==digest(p)
                                   for p in sorted((ROOT/'tests/fixtures/image-hough').glob('*.raw')))))
        jobs=[('tools/migration/bootstrap_sdk.py',False),
              ('tools/moat/image_hough_build.py',False),('tools/moat/image_hough_run.py',False),
              ('tools/moat/image_hough_reference.py',True),('tools/moat/image_hough_options.py',False),
              ('tools/moat/image_hough_runtime.py',False),('tools/moat/image_hough_runtime_reference.py',True),
              ('tools/moat/image_hough_trace.py',False)]
        for name,is_cpu in jobs:
            if rc:break
            if is_cpu:argv=[cpu,str(clone/name)];env=None
            else:
                argv=['/home/zihaomu/zihaomu_workspace/rocm10-launch.sh','env',
                      'ROCR_VISIBLE_DEVICES=3','HIP_VISIBLE_DEVICES=0','python3',str(clone/name)]
                env=dict(os.environ,HIP_VISIBLE_DEVICES='2')
            rc=e.command(argv,'cold-'+Path(name).stem,cwd=clone,env=env,timeout=1200)
        checks.append(dict(check='clean-rebuild-19-full-CLI-CPU-runtime-and-real-trace',passed=rc==0))
        rows=list(reports(clone)) if not rc else []
        count={'contracts':1,'build':1,'runs':14,'validation':14,'options-run':5,
               'options-validation':5,'runtime':1,'runtime-validation':1,'trace':1}
        from collections import Counter
        checks.append(dict(check='complete-43-sealed-child-inventory',
                           passed=len(rows)==43 and Counter(name for name,_,_ in rows)==count
                           and all(row.get('evidence') for _,_,row in rows)))
        checks.append(dict(check='all-cold-results-passed-and-build-current',
                           passed=rc==0 and len(rows)==43
                           and all(row.get('status') in {'FROZEN','BUILT','EXECUTED','PASSED'} for _,_,row in rows)
                           and json.loads((clone/'migration/reports/image-hough-build.json').read_text())['dependencies']==
                           {n:digest(ROOT/n) for n in json.loads((ROOT/'migration/reports/image-hough-build.json').read_text())['dependencies']}))
        for name,index,row in rows:
            if rc:break
            meta=json.loads((clone/row['evidence']/'manifest.json').read_text())
            raw=clone/meta['raw_artifact_dir']
            if not raw.is_dir() or not (raw/'sealed.json').is_file():raise ValueError('missing child seal '+name)
            dest=e.path/'child-evidence'/name/str(index);dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copytree(raw,dest);(dest/'sealed.json').rename(dest/'child-seal.json')
            source=json.loads((dest/'source.json').read_text())
            for object_name in source['source_objects'].values():
                src,dst=clone/object_name,ROOT/object_name
                if dst.exists():
                    if digest(src)!=digest(dst):raise ValueError('source object collision')
                else:shutil.copyfile(src,dst)
            children.append(dict(name=name,index=index,relative=str(dest.relative_to(e.path)),report=row))
        checks.append(dict(check='all-forty-three-complete-children-copied',passed=len(children)==43))
    except Exception as error:
        checks.append(dict(check='cold-replay-finished',passed=False,error=repr(error)));rc=rc or 1
    checks.append(dict(check='final-return-code',passed=rc==0))
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED'
    result=dict(status=status,return_code=rc,source_commit=commit,clone=str(clone),
                checks=checks,children=children)
    write(e.path/'cold.json',result)
    result['evidence']=e.finish('PASSED' if status=='PASSED' else 'SELF_TEST_FAILED',dict(status=status,checks=checks))
    write(ROOT/'migration/reports/image-hough-cold.json',result)
    record('I3','Hough固定Git检出重建合同/RAW、HIP/C++、14主CLI+5有效参数、全部独立CPU、运行合同与GPU trace及43子记录：'+status,[result['evidence']])
    print(status,result['evidence'])
    return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
