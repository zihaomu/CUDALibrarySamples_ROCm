#!/usr/bin/env python3
"""Independent NumPy/OpenCV CPU checks for the complete HIP benchmark products."""
import argparse,json,re,tempfile
from pathlib import Path
import cv2,numpy as np
from experiment import ROOT,Experiment,write,digest
from image_progress import record
from image_canny_stages_reference import reference as canny_stages
from image_canny_local_research import local_mask

def difference(actual,expected):
    a=actual.astype(np.int16);b=expected.astype(np.int16);delta=np.abs(a-b)
    coords=np.argwhere(delta)
    return dict(mismatches=int(np.count_nonzero(delta)),max_abs=int(delta.max(initial=0)),
                mean_abs=float(delta.mean()),first_coordinates=coords[:8].tolist())

def tiled(profile,w,h):
    source=np.fromfile(ROOT/profile['image'],np.uint8).reshape(1024,2048)
    yy=np.arange(h);xx=np.arange(w)
    sy=np.where((yy//1024)%2,1023-yy%1024,yy%1024)
    sx=np.where((xx//2048)%2,2047-xx%2048,xx%2048)
    return source[np.ix_(sy,sx)].copy()

def gpu_product(path,name,w,h,sha):
    file=path/'outputs'/name
    if digest(file)!=sha:raise ValueError('GPU product SHA changed '+name)
    shape=(h//2,w//2) if name=='resize.raw' else (h,w)
    return np.fromfile(file,np.uint8).reshape(shape)

def validate(case,run,profile):
    proof=ROOT/run['evidence'];manifest=json.loads((proof/'manifest.json').read_text())
    commands=json.loads((proof/'commands.json').read_text())
    actual=[c for c in commands if c['phase']=='actual-four-operation-original-CLI']
    build=json.loads((ROOT/'migration/reports/image-benchmark-build.json').read_text())
    command=actual[0] if len(actual)==1 else {}
    raw=ROOT/manifest['raw_artifact_dir']
    stdout=(raw/command['stdout']).read_text() if command else ''
    stderr=(raw/command['stderr']).read_text() if command else ''
    checks=[dict(check='actual-return-and-source',passed=run['status']=='EXECUTED'
                 and command.get('return_code')==run['return_code']==case['expected_return_code']
                 and manifest['case_id']==run['case']==case['case']
                 and manifest['parent_experiment_id']==build['experiment_id']
                 and command.get('argv')==[str(ROOT/build['binary']),*case['arguments']]
                 and command.get('cwd')==str(raw/'outputs')
                 and run['arguments']==case['arguments']
                 and run['build_evidence']==build['evidence']),
            dict(check='actual-input-and-diagnostics',passed=digest(raw/'images'/Path(profile['image']).name)==profile['image_sha256']
                 and stdout.startswith(case['stdout_starts']) and stderr.startswith(case['stderr_starts'])
                 and (bool(stdout)==bool(case['stdout_starts']))
                 and (bool(stderr)==bool(case['stderr_starts']))),
            dict(check='actual-physical-GPU1',passed={d['physical_id'] for d in json.loads((proof/'backend.observed.json').read_text())['devices']}=={1}),
            dict(check='complete-four-product-set',passed={name:x['bytes'] for name,x in run['products'].items()}==case['products'])]
    if case['expected_return_code']:
        return dict(case=case['case'],status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks)
    w,h=case['width'],case['height'];gray=tiled(profile,w,h)
    project_gauss=np.zeros((h,w),np.int32)
    p=np.pad(gray,2,mode='edge').astype(np.int32)
    weight=(1,4,6,4,1)
    for dy in range(5):
        for dx in range(5):project_gauss+=weight[dy]*weight[dx]*p[dy:dy+h,dx:dx+w]
    project_gauss=((project_gauss+128)>>8).astype(np.uint8)
    with tempfile.TemporaryDirectory(prefix='benchmark-canny-CPU-') as temporary:
        fixture=Path(temporary);write(fixture/'config.json',dict(width=w,height=h,channels=1,pitch=w))
        (fixture/'input.bin').write_bytes(gray.tobytes())
        project_canny=local_mask(canny_stages(fixture),60,120)
    # Original CUDA and the HIP C++ benchmark use OpenCV's default REFLECT_101.
    cv_gauss=cv2.GaussianBlur(gray,(5,5),0)
    cv_canny=cv2.Canny(gray,60,120,apertureSize=3,L2gradient=True)
    cv_resize=cv2.resize(gray,(w//2,h//2),interpolation=cv2.INTER_LINEAR)
    # OpenCV MatExpr gray/2+40 uses integer saturation after division.
    blue=cv2.addWeighted(gray,0.5,gray,0,40)
    rgb=cv2.merge((gray,255-gray,blue))
    cv_color=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    policy=profile['semantic_policy']
    expected={'gauss.raw':(project_gauss,cv_gauss,policy['gaussian']['project_max_abs'],policy['gaussian']['project_mean_abs']),
              'canny.raw':(project_canny,cv_canny,policy['canny']['project_max_abs'],policy['canny']['project_mean_abs']),
              'resize.raw':(cv_resize,cv_resize,policy['resize']['project_max_abs'],policy['resize']['project_mean_abs']),
              'color.raw':(cv_color,cv_color,policy['rgb_gray']['project_max_abs'],policy['rgb_gray']['project_mean_abs'])}
    metrics={}
    for name,(project,cv,limit,mean_limit) in expected.items():
        got=gpu_product(raw,name,w,h,run['products'][name]['sha256'])
        project_diff=difference(got,project);native_diff=difference(got,cv)
        metrics[name]=dict(project=project_diff,opencv=native_diff,nonzero=int(np.count_nonzero(got)))
        checks.append(dict(check=name+'/project-CPU',passed=project_diff['max_abs']<=limit
                           and project_diff['mean_abs']<=mean_limit,
                           max_abs=project_diff['max_abs'],mean_abs=project_diff['mean_abs']))
    checks.append(dict(check='Canny-OpenCV-structural-comparison-recorded',
                       passed=metrics['canny.raw']['opencv']['mismatches']>=0
                       and metrics['canny.raw']['nonzero']>0))
    labels={'gauss.raw':'Gaussian 5x5','canny.raw':'Canny 3x3 L2',
            'resize.raw':'Resize 1/2 bilinear','color.raw':'RGB to gray'}
    lines=[line for line in stdout.splitlines() if any(line.startswith(label) for label in labels.values())]
    checks.append(dict(check='four-printed-operation-rows-in-original-order',
                       passed=[next((label for label in labels.values() if line.startswith(label)),None) for line in lines]
                       ==list(labels.values())))
    if len(lines)==4:
        for (name,_),line in zip(labels.items(),lines):
            try:printed=float(line.rsplit('|',1)[1].strip())
            except (IndexError,ValueError):printed=float('inf')
            observed=metrics[name]['opencv']['mean_abs']
            checks.append(dict(check=name+'/printed-OpenCV-mean-abs',
                               passed=abs(printed-observed)<=policy['printed_mean_abs_tolerance'],printed=printed,independent=observed))
    match=re.search(r'^Canny edge pixels: ROCm (\d+), OpenCV (\d+)',stdout,re.MULTILINE)
    checks.append(dict(check='printed-Canny-edge-counts',passed=bool(match)
                       and (int(match[1]),int(match[2]))==
                       (metrics['canny.raw']['nonzero'],int(np.count_nonzero(cv_canny)))))
    return dict(case=case['case'],status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',
                checks=checks,metrics=metrics)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case');args=parser.parse_args()
    profile=json.loads((ROOT/'migration/rewrite/image-benchmark-profile.json').read_text())
    cases={c['case']:c for c in profile['cases']}
    runs=json.loads((ROOT/'migration/reports/image-benchmark-runs.json').read_text())
    if len(runs)!=len(cases) or {r['case'] for r in runs}!=set(cases):raise ValueError('complete unique benchmark runs required')
    existing=ROOT/'migration/reports/image-benchmark-validation.json'
    results=json.loads(existing.read_text()) if existing.exists() else []
    for run in runs:
        if args.case and run['case']!=args.case:continue
        e=Experiment('I3','OpenCV-benchmark-independent-four-operation-CPU','CPU-reference',
                     case=run['case'],parent=Path(run['evidence']).name,
                     sources=[__file__,ROOT/'migration/rewrite/image-benchmark-profile.json',
                              ROOT/'migration/reports/image-benchmark-runs.json',
                              ROOT/'tools/moat/image_canny_stages_reference.py',
                              ROOT/'tools/moat/image_canny_local_research.py'])
        try:result=validate(cases[run['case']],run,profile)
        except Exception as error:result=dict(case=run['case'],status='FAILED',checks=[dict(check='independent-CPU-replay',passed=False,error=repr(error))])
        write(e.path/'results.json',result)
        result['evidence']=e.finish('PASSED' if result['status']=='PASSED' else 'NUMERIC_MISMATCH',
                                   dict(status=result['status'],checks=result['checks']))
        results=[r for r in results if r['case']!=run['case']]+[result]
        write(existing,results)
        record('I3','OpenCV benchmark '+run['case']+' 全输出独立CPU/OpenCV验证：'+result['status']+'；原始计时不作速度资格。',[result['evidence']])
        print(run['case'],result['status'],[(c['check'],c['passed']) for c in result['checks'] if not c['passed']],flush=True)
    return int(any(r['status']!='PASSED' for r in results))

if __name__=='__main__':raise SystemExit(main())
