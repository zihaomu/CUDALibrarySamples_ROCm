#!/usr/bin/env python3
"""Rebuild committed encoder sources and replay CLI, traces and numerical corpora."""
import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from experiment import ROOT,Experiment,digest,git,write
from image_completion_progress import record
from image_encoder_math_binding import sealed
from image_encoder_quality_run import arguments
from image_encoder_large import fixture

def main():
    from snapshot import capture
    commit=git('rev-parse','HEAD').strip();bp=ROOT/'migration/reports/image-encoder-instances-v2-build.json';build=json.loads(bp.read_text());sealed(build,'build.json')
    numerical={m:ROOT/f'migration/reports/image-encoder-math-production-{m}.json' for m in ['fresh','development','heldout']}
    profiles={m:ROOT/'migration/rewrite'/n for m,n in [('fresh','image-encoder-math-variant-v2-profile.json'),('development','image-encoder-quality-profile.json'),('heldout','image-encoder-quality-holdout-v2-profile.json')]}
    largep=ROOT/'migration/rewrite/image-encoder-large-profile.json';larger=ROOT/'migration/reports/image-encoder-large-runs.json'
    scripts=['image_encoder_pipeline.py','image_encoder_instances_v2.py','image_encoder_pipeline_trace.py','image_encoder_runtime.py','image_encoder_instances_v2_trace.py','image_encoder_preallocation.py','image_encoder_quality_run.py','image_encoder_large.py']
    sources=[__file__,bp,largep,larger,*numerical.values(),*profiles.values(),*[ROOT/'tools/moat'/n for n in scripts],*[ROOT/n for n in build['dependencies']]]
    e=Experiment('I5','encoder-fixed-commit-cold-rebuild','rocm-cold',sources=sources)
    write(e.path/'backend.observed.json',capture());clone=Path(tempfile.mkdtemp(prefix='image-encoder-cold-',dir=ROOT.parent))/'src'
    checks=[];children=[];outputs=[];refs=[]
    try:
        rc=e.command(['git','clone','--quiet','--shared','--no-checkout',str(ROOT),str(clone)],'cold-clone',timeout=300)
        if rc:raise ValueError('clone failed')
        paths=['/rocm/','/tools/','/nvJPEG/','/migration/rewrite/','/migration/fixtures/','/migration/environments/','/migration/moat/','/migration/*.md','/migration/reports/image-completion-progress.json','/migration/reports/image-libraries-progress.json','/migration/reports/image-libraries-progress.md','/.gitignore']
        if e.command(['git','sparse-checkout','set','--no-cone',*paths],'cold-source-surface',cwd=clone):raise ValueError('sparse checkout')
        if e.command(['git','checkout','--quiet',commit],'cold-fixed-commit',cwd=clone):raise ValueError('checkout')
        checks.append(dict(check='clean-fixed-checkout-no-application-cache',passed=not (clone/'build').exists() and not (clone/'artifacts').exists() and subprocess.check_output(['git','rev-parse','HEAD'],cwd=clone,text=True).strip()==commit))
        expected={n:h for n,h in build['dependencies'].items() if not n.startswith('build/')}
        checks.append(dict(check='every-compiled-project-source-from-commit',passed=all((clone/n).is_file() and digest(clone/n)==h for n,h in expected.items())))
        if not all(c['passed'] for c in checks):raise ValueError('committed source mismatch')
        # Fixed external library installation is shared; no application/probe
        # binary, prior object file, or generated output is copied into build.
        (clone/'build').mkdir();(clone/'build/cpu-codecs').symlink_to(ROOT/'build/cpu-codecs',target_is_directory=True)
        write(e.path/'external-dependencies.json',dict(scope='Pinned external libjpeg and installed ROCm SDK reused; all application, reference-probe and observer binaries rebuilt in the empty checkout.',dependencies={n:h for n,h in build['dependencies'].items() if n.startswith('build/')}))
        jobs=[('tools/migration/bootstrap_sdk.py',[]),('tools/moat/image_encoder_pipeline.py',['build']),('tools/moat/image_encoder_instances_v2.py',['build']),('tools/moat/image_encoder_instances_v2.py',['run']),('tools/moat/image_encoder_pipeline_trace.py',[]),('tools/moat/image_encoder_runtime.py',['run']),('tools/moat/image_encoder_instances_v2_trace.py',[]),('tools/moat/image_encoder_preallocation.py',['run']),('tools/moat/image_encoder_preallocation.py',['lifecycle'])]
        for script,args in jobs:
            if e.command([sys.executable,str(clone/script),*args],'cold-'+Path(script).stem+'-'+('-'.join(args) or 'main'),cwd=clone,timeout=1200):raise ValueError('cold child '+script)
            record('IMG-01','固定提交冷构建步骤完成：'+script+' '+' '.join(args)+'；子实验保留在独立检出，等待完整资格。')
        names={'image-encoder-instances-v2-build.json':1,'image-encoder-pipeline-build.json':1,'image-encoder-instances-v2-runs.json':15,'image-encoder-pipeline-trace.json':4,'image-encoder-runtime-runs.json':16,'image-encoder-instances-v2-trace.json':3,'image-encoder-preallocation-runs.json':3,'image-encoder-prepared-lifecycle.json':1}
        for name,count in names.items():
            group=json.loads((clone/'migration/reports'/name).read_text());rows=group if isinstance(group,list) else [group]
            checks.append(dict(check='complete-cold-'+name,passed=len(rows)==count and all(r['status'] in ['PASSED','BUILT'] and (r['status']=='BUILT' or r['checks'] and all(c['passed'] for c in r['checks'])) for r in rows)))
            for index,row in enumerate(rows):
                path=clone/row['evidence'];manifest=json.loads((path/'manifest.json').read_text());raw=clone/manifest['raw_artifact_dir']
                target=e.path/'children'/name/str(index);target.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(raw,target);(target/'sealed.json').rename(target/'child-seal.json')
                for object_name in json.loads((target/'source.json').read_text())['source_objects'].values():
                    source=clone/object_name;dest=ROOT/object_name
                    if dest.exists():
                        if digest(dest)!=digest(source):raise ValueError('source object collision')
                    else:shutil.copyfile(source,dest)
                children.append(dict(report=name,index=index,path=str(target.relative_to(e.path)),result=row))
        cb=json.loads((clone/'migration/reports/image-encoder-instances-v2-build.json').read_text());binary=clone/cb['binary']
        checks.append(dict(check='new-application-binary-current-source-closure',passed=digest(binary)==cb['binary_sha256'] and cb['dependencies']==build['dependencies'] and str(binary)!=str(ROOT/build['binary'])))
        for matrix,pp in profiles.items():
            profile=json.loads(pp.read_text());proof=json.loads(numerical[matrix].read_text());sealed(proof)
            if proof['status']!='PASSED' or len(proof['cases'])!=80 or [r['case'] for r in proof['cases']]!=[c['id'] for c in profile['cases']]:raise ValueError('complete prior numerical proof')
            refs.append(proof['evidence'])
            for case,golden in zip(profile['cases'],proof['cases']):
                item=next(i for i in profile['inputs'] if i['id']==case['input']);source=clone/item['path']
                if digest(source)!=item['sha256']:raise ValueError('committed fixture SHA')
                folder=e.path/'numerical'/matrix/case['id'];folder.mkdir(parents=True);inputdir=folder/'input';inputdir.mkdir();shutil.copyfile(source,inputdir/'image.bmp');out=folder/'products'
                rc=e.command(arguments(case,binary,inputdir,out),'cold-'+matrix+'-'+case['id'],timeout=300)
                files=list(out.iterdir()) if out.is_dir() else []
                passed=rc==0 and {p.name for p in files}=={'0.jpg'} and digest(out/'0.jpg')==golden['JPEG_sha256']
                checks.append(dict(check='cold-'+matrix+'-'+case['id'],passed=passed));outputs.append(dict(matrix=matrix,case=case['id'],sha256=digest(out/'0.jpg') if (out/'0.jpg').exists() else None,passed=passed))
                if not passed:raise ValueError('cold numerical mismatch')
            record('IMG-01','固定提交新编译入口 '+matrix+' 80/80独立已验JPEG完整字节复现；不复用先前应用二进制。')
        largeprofile=json.loads(largep.read_text());large=json.loads(larger.read_text())
        for case,golden in zip(largeprofile['cases'],large):
            sealed(golden)
            if golden['case']!=case['id'] or len(golden['products'])!=3:raise ValueError('large output contract')
            rgb,bmp=fixture(case)
            if hashlib.sha256(bmp).hexdigest()!=case['bmp_sha256'] or hashlib.sha256(rgb.tobytes()).hexdigest()!=case['sha256']:raise ValueError('cold large seed reconstruction')
            folder=e.path/'large'/case['id'];folder.mkdir(parents=True);inputs=folder/'input';inputs.mkdir();(inputs/'image.bmp').write_bytes(bmp);out=folder/'products';del rgb,bmp
            args=[str(binary),'-i',str(inputs),'-o',str(out),'-j','1','-s','1','-n','3','-b','gpu','-q',str(case['quality'])]
            if case['sampling']==1:args+=['-p']
            if case['optimized']:args+=['-f']
            rc=e.command(args,'cold-'+case['id'],timeout=600)
            passed=rc==0 and {f.name for f in out.iterdir()}=={p['name'] for p in golden['products']} and all(digest(out/p['name'])==p['sha256'] for p in golden['products'])
            checks.append(dict(check='cold-'+case['id'],passed=passed));outputs.append(dict(matrix='large',case=case['id'],passed=passed))
            if not passed:raise ValueError('cold large byte mismatch')
        checks.append(dict(check='complete-240-quality-plus-eight-large-groups',passed=len(outputs)==248))
    except Exception as error:checks.append(dict(check='cold-exception',passed=False,error=repr(error)))
    status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED'
    row=dict(status=status,source_commit=commit,clone=str(clone),checks=checks,children=children,outputs=outputs,evidence_references=refs,scope='Committed-source rebuild of both encoder/probe and copy observer; 15 CLI,16 runtime,3 original-entry traces including changed-input replay,3 preallocation cases/lifecycle,240 mathematical JPEG outputs and8 large groups. External pinned libjpeg and ROCm SDK are dependencies, not cold rebuilt here.')
    write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'SELF_TEST_FAILED',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-completion-cold.json',row)
    record('IMG-01','固定Git提交编码器冷检出重建与完整规定回归：'+status+'；源码依赖、重建二进制、子实验、240数学产品和大图种子重建均保留。',[row['evidence']]);print(status,[c for c in checks if not c['passed']]);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
