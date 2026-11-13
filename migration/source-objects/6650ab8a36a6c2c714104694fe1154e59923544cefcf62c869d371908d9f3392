#!/usr/bin/env python3
"""Rebuild fixed committed watershed sources and reproduce all current GPU products."""
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
from experiment import ROOT,Experiment,digest,git,write
from image_completion_progress import record
from image_encoder_math_binding import sealed
from image_watershed_completion_entries import BUILD,INVENTORY,CONTRACT,dependencies

def main():
    from snapshot import capture
    commit=git('rev-parse','HEAD').strip();build=json.loads(BUILD.read_text());sealed(build,'build.json')
    modes=['padded','compact','inplace','no-labels']
    names=['image-watershed-completion-entries-runs.json','image-watershed-completion-entry-trace.json','image-watershed-completion-entry-replay.json','image-watershed-completion-entry-negative.json','image-watershed-v2-controls.json']+[f'image-watershed-completion-AMD-{m}.json' for m in modes]
    old={n:json.loads((ROOT/'migration/reports'/n).read_text()) for n in names}
    scripts=['image_watershed_completion_entries.py','image_watershed_entry_runtime.py','image_watershed_v2.py','image_watershed_completion.py','image_watershed_v2_controls.py']
    sources=[Path(__file__),BUILD,INVENTORY,CONTRACT,*dependencies(),*[ROOT/'rocm/probes/image'/n for n in ['watershed_v2_probe.cpp','watershed_v2_controls.cpp']],*[ROOT/'tools/moat'/n for n in scripts],*[ROOT/'migration/reports'/n for n in names]]
    e=Experiment('I3','watershed-fixed-commit-complete-cold-rebuild','rocm-cold',sources=sources);write(e.path/'backend.observed.json',capture());clone=Path(tempfile.mkdtemp(prefix='image-watershed-cold-',dir=ROOT.parent))/'src';checks=[];children=[];refs=set();products=0
    try:
        if e.command(['git','clone','--quiet','--shared','--no-checkout',str(ROOT),str(clone)],'cold-clone',timeout=300):raise ValueError('clone failed')
        paths=['/rocm/','/tools/','/NPP/','/NPP+/','/migration/rewrite/','/migration/fixtures/','/migration/environments/','/migration/moat/','/migration/*.md','/migration/samples.yaml','/migration/reports/image-completion-progress.json','/migration/reports/image-libraries-progress.json','/migration/reports/image-libraries-progress.md','/.gitignore']
        if e.command(['git','sparse-checkout','set','--no-cone',*paths],'cold-source-surface',cwd=clone):raise ValueError('sparse checkout')
        if e.command(['git','checkout','--quiet',commit],'cold-fixed-commit',cwd=clone):raise ValueError('checkout')
        checks.append(dict(check='clean-fixed-checkout-without-build-artifacts',passed=not (clone/'build').exists() and not (clone/'artifacts').exists() and subprocess.check_output(['git','rev-parse','HEAD'],cwd=clone,text=True).strip()==commit))
        checks.append(dict(check='all-production-and-probe-sources-from-commit',passed=all((clone/p.relative_to(ROOT)).is_file() and digest(clone/p.relative_to(ROOT))==digest(p) for p in sources if p.suffix in ('.py','.hpp','.hip','.h','.cpp'))))
        if not all(c['passed'] for c in checks):raise ValueError('committed source mismatch')
        (clone/'build').mkdir();(clone/'migration/source-objects').mkdir(parents=True,exist_ok=True)
        write(e.path/'external-dependencies.json',dict(scope='Installed ROCm10.1 SDK/driver reused; overlay, both original programs, isolated probe and failure-injection probe rebuilt. No prior application binary/object/output copied.'))
        jobs=[('tools/migration/bootstrap_sdk.py',[]),('tools/moat/image_watershed_completion_entries.py',['build']),('tools/moat/image_watershed_completion_entries.py',['run']),('tools/moat/image_watershed_entry_runtime.py',['trace']),('tools/moat/image_watershed_entry_runtime.py',['replay']),('tools/moat/image_watershed_entry_runtime.py',['negative']),('tools/moat/image_watershed_v2.py',['build']),('tools/moat/image_watershed_v2_controls.py',[])]+[('tools/moat/image_watershed_completion.py',['amd','--mode',m]) for m in modes]
        for script,args in jobs:
            if e.command([sys.executable,str(clone/script),*args],'cold-'+Path(script).stem+'-'+('-'.join(args) or 'main'),cwd=clone,timeout=900):raise ValueError('cold child '+script+' '+str(args))
            record('IMG-02','固定提交冷构建步骤完成：'+Path(script).stem+' '+' '.join(args)+'；完整产品回归及子证据仍待汇总。')
        for name in names:
            fresh=json.loads((clone/'migration/reports'/name).read_text());gold=old[name];rows=fresh if isinstance(fresh,list) else [fresh];gold_rows=gold if isinstance(gold,list) else [gold]
            checks.append(dict(check='complete-report-'+name,passed=len(rows)==len(gold_rows)))
            for index,(row,prior) in enumerate(zip(rows,gold_rows)):
                member='run.json' if name=='image-watershed-completion-entries-runs.json' else 'result.json';sealed(prior,member);refs.add(prior['evidence'])
                for key in ('sample_id','case','family','action','key'):
                    if key in prior and row.get(key)!=prior[key]:raise ValueError('cold semantic row identity '+name)
                checks.append(dict(check=name+'-'+str(index)+'-successful-and-identical-status',passed=row['status']==prior['status'] and row['status'] in ('PASSED','EXECUTED') and all(c['passed'] for c in row.get('checks',[]))))
                key='products' if 'products' in prior else 'outputs' if 'outputs' in prior else None
                if key:
                    checks.append(dict(check=name+'-'+str(index)+'-every-product-byte-identical',passed=row[key]==prior[key]));products+=len(row[key])
                raw=clone/json.loads((clone/row['evidence']/'manifest.json').read_text())['raw_artifact_dir']
                if 'output_dir' in row:
                    folder=clone/row['output_dir']
                    if {p.name for p in folder.iterdir() if p.is_file() and p.name in row[key]}!=set(row[key]) or any(digest(folder/n)!=v['sha256'] or (folder/n).stat().st_size!=v['bytes'] for n,v in row[key].items()):raise ValueError('actual cold output identity')
                if name.startswith('image-watershed-completion-AMD-'):
                    commands=json.loads((raw/'commands.json').read_text());log=(raw/commands[0]['stdout']).read_text();lines=[s for s in log.splitlines() if s.startswith('RESULT ')]
                    checks.append(dict(check=name+'-actual-GPU-and-sixty-padding-checks',passed='arch=gfx1201' in log and 'PCI=0000:23:00.0' in log and len(lines)==60 and all('padding=1' in s for s in lines)))
        for manifest in (clone/'artifacts/rewrite').rglob('manifest.json'):
            raw=manifest.parent
            if not (raw/'sealed.json').exists():raise ValueError('unfinished cold child')
            target=e.path/'children'/raw.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(raw,target);(target/'sealed.json').rename(target/'child-seal.json')
            for name in json.loads((target/'source.json').read_text())['source_objects'].values():
                source=clone/name;dest=ROOT/name
                if dest.exists() and digest(dest)!=digest(source):raise ValueError('source object mismatch')
                if not dest.exists():shutil.copyfile(source,dest)
            children.append(dict(path=str(target.relative_to(e.path)),manifest=json.loads(manifest.read_text())))
        checks.append(dict(check='twenty-one-complete-sealed-child-experiments',passed=len(children)==21))
        cb=json.loads((clone/BUILD.relative_to(ROOT)).read_text());checks.append(dict(check='same-compiled-source-closure-new-build-location',passed=cb['dependencies']==build['dependencies'] and all(cb['binaries'][f]['path']!=build['binaries'][f]['path'] for f in build['binaries'])))
    except Exception as error:checks.append(dict(check='cold-exception',passed=False,error=repr(error)))
    status='PASSED' if checks and all(c['passed'] for c in checks) else 'SELF_TEST_FAILED';row=dict(status=status,source_commit=commit,clone=str(clone),checks=checks,children=children,product_reproductions=products,evidence_references=sorted(refs),scope='Both original programs and probes rebuilt from fixed commit; all22 original products, both kernel traces, changed inputs,8 I/O failures,18 invalid views,9 allocation failures/recovery, and all60 inputs in4 layouts reproduced. Native and CPU numerical proofs remain separately referenced.')
    write(e.path/'result.json',row);row['evidence']=e.finish(status,dict(status=status,checks=checks));write(ROOT/'migration/reports/image-watershed-completion-cold.json',row);record('IMG-02','固定提交Watershed冷检出、完整构建及规定回归：'+status+'，子实验与全部产品哈希保留。',[row['evidence']]);print(status,[c for c in checks if not c['passed']]);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
