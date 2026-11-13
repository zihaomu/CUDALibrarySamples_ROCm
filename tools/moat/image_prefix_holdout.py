#!/usr/bin/env python3
"""Freeze and verify adaptive-prefix boundaries after dispatch choice is fixed."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

SELECTION=ROOT/'migration/rewrite/image-prefix-dispatch-selection.json'
PROFILE=ROOT/'migration/rewrite/image-prefix-holdout-profile.json'
BUILD=ROOT/'migration/reports/image-prefix-holdout-build.json'
REPORT=ROOT/'migration/reports/image-prefix-holdout-runs.json'
SOURCE=ROOT/'rocm/probes/image/jpeg_adaptive_prefix.hip'

def freeze():
    if PROFILE.exists():raise ValueError('holdout already frozen')
    selection=json.loads(SELECTION.read_text());folder=ROOT/'migration/fixtures/image-prefix-holdout';folder.mkdir(parents=True,exist_ok=True);cases=[]
    for mode,threshold in selection['thresholds'].items():
        for count in sorted({max(1,threshold-1),max(1,threshold),threshold+1}):
            for pattern in ['mixed','minimum','maximum']:cases.append(dict(id=f'{mode}-{count}-{pattern}',mode=mode,count=count,pattern=pattern))
    cases += [dict(id='bits-invalid-zero',mode='bits',count=1,pattern='invalid-zero'),
              dict(id='bits-invalid-long',mode='bits',count=1,pattern='invalid-long'),
              dict(id='bits-overflow-tiled',mode='bits',count=1048576,pattern='maximum'),
              *[dict(id=mode+'-empty',mode=mode,count=0,pattern='minimum') for mode in ['bits','stuff']]]
    for c in cases:
        dtype='<u2' if c['mode']=='bits' else 'u1';a=(np.arange(c['count'],dtype=np.uint64)*22695477+20111)&0xffffffff
        if c['pattern']=='mixed':a=a%4096+1 if c['mode']=='bits' else (a^(a>>17))&255
        elif c['pattern']=='minimum':a[:]=1 if c['mode']=='bits' else 0
        elif c['pattern']=='maximum':a[:]=4096 if c['mode']=='bits' else 255
        elif c['pattern']=='invalid-zero':a[:]=0
        elif c['pattern']=='invalid-long':a[:]=4097
        path=folder/(c['id']+('.u16' if c['mode']=='bits' else '.u8'));a.astype(dtype).tofile(path)
        c.update(path=str(path.relative_to(ROOT)),dtype=dtype,bytes=path.stat().st_size,sha256=digest(path),serial=bool(c['count'] and c['count']<=selection['thresholds'][c['mode']]))
    e=Experiment('I5','adaptive-prefix-boundary-holdout-contract','CPU-contract',sources=[__file__,SELECTION,*[ROOT/c['path'] for c in cases]])
    value=dict(status='FROZEN',selection_sha256=digest(SELECTION),thresholds=selection['thresholds'],cases=cases,host_guard_rejections=22,
        gates=['Full independent uint64 CPU offsets/metadata; invalid cases may leave unspecified offsets but must flag errors.',
               'Actual trace must contain one serial or three tiled application kernels exactly as chosen before holdout execution.',
               'Empty/pointer guards must reject before dispatch; thresholds cannot be retuned with these outcomes.'])
    write(e.path/'profile.json',value);value['evidence']=e.finish('OBSERVED');write(PROFILE,value)
    record('IMG-01','冻结prefix独立边界集：'+str(len(cases))+'组阈值前/等/后、三分布、无效长度/溢出/空输入，另22项指针/零计数拒绝；阈值保持128/64。',[str(PROFILE.relative_to(ROOT)),value['evidence']]);print(value['evidence'])

def build():
    from snapshot import capture
    from image_completion_inventory import closure
    deps,missing=closure(SOURCE)
    if missing:raise ValueError(missing)
    for path in [PROFILE,SELECTION]:deps[str(path.relative_to(ROOT))]=digest(path)
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay'
    e=Experiment('I5','adaptive-prefix-holdout-build','rocm-build',sources=[__file__,*[ROOT/n for n in deps]])
    write(e.path/'backend.observed.json',capture());binary=e.path/'probe'
    rc=e.command(['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
        '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__',
        '-I'+str(ROOT/'rocm/common'),'-x','hip',str(SOURCE),'-o',str(binary),'-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64'],'build-adaptive-prefix')
    row=dict(status='BUILT' if rc==0 else 'BUILD_ERROR',binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary) if rc==0 else None,dependencies=deps,experiment_id=e.id)
    write(e.path/'build.json',row);row['evidence']=e.finish('EXECUTED' if rc==0 else 'BUILD_ERROR');write(BUILD,row)
    record('IMG-01','自适应prefix边界探针构建：'+row['status']+'。',[row['evidence']]);print(row['status']);return int(rc!=0)

def run():
    from snapshot import capture
    p=json.loads(PROFILE.read_text());b=json.loads(BUILD.read_text())
    if p['selection_sha256']!=digest(SELECTION) or b['status']!='BUILT' or digest(ROOT/b['binary'])!=b['binary_sha256'] or any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()):raise ValueError('frozen selection/current binary required')
    rows=[]
    for c in p['cases']+[dict(id='null-pointer-and-count-guards',guards=True)]:
        source=None if c.get('guards') else ROOT/c['path']
        if source is not None and (source.stat().st_size!=c['bytes'] or digest(source)!=c['sha256']):raise ValueError('holdout byte drift')
        e=Experiment('I5','adaptive-prefix-holdout','rocm-trace',case=c['id'],sources=[__file__,PROFILE,SELECTION,BUILD,*([source] if source is not None else []),*[ROOT/n for n in b['dependencies']]],parent=b['experiment_id'])
        observed=capture();write(e.path/'backend.observed.json',observed);out=e.path/'outputs'
        args=[str(ROOT/b['binary'])]+(['guards'] if c.get('guards') else [c['mode'],str(source),str(out)])
        rc=e.command(['rocprofv3','--kernel-trace','--output-format','csv','--output-directory',str(e.path/'trace'),'--',*args],'adaptive-prefix-boundary-trace',timeout=300)
        checks=[dict(check='command-success',passed=rc==0)];metadata={};expected_kernels=0;products={}
        try:
            metadata=json.loads((e.path/'logs/0001-adaptive-prefix-boundary-trace.stdout.log').read_text())
            if c.get('guards'):checks.append(dict(check='all22-host-guards-rejected',passed=metadata==dict(rejected_host_contracts=p['host_guard_rejections'])))
            elif c['count']==0:
                checks.append(dict(check='empty-input-rejected-without-output',passed=metadata==dict(count=0,host_invalid=True) and not list(out.iterdir())))
            else:
                expected_kernels=1 if c['serial'] else 3
                values=np.fromfile(source,dtype=c['dtype']).astype(np.uint64);add=(values==255).astype(np.uint64) if c['mode']=='stuff' else values
                summed=np.cumsum(add,dtype=np.uint64);positions=summed-add+(np.arange(c['count'],dtype=np.uint64) if c['mode']=='stuff' else 0)
                total=int(summed[-1])+(c['count'] if c['mode']=='stuff' else 0);errors=int(c['mode']=='bits' and bool(np.any((values==0)|(values>4096))))
                if total>0xffffffff-(7 if c['mode']=='bits' else 0):errors|=2;total=0
                checks.append(dict(check='frozen-dispatch-and-independent-metadata',passed=metadata==dict(count=c['count'],total=total,errors=errors,serial=c['serial'])))
                checks.append(dict(check='exact-product-set',passed={x.name for x in out.iterdir()}=={'offsets.u32','result.u32'}))
                actual=out/'offsets.u32';result=out/'result.u32'
                checks.append(dict(check='complete-output-length-and-CPU-reference',passed=actual.stat().st_size==c['count']*4 and result.stat().st_size==8 and np.fromfile(result,dtype='<u4').tolist()==[total,errors] and (bool(errors) or np.array_equal(np.fromfile(actual,dtype='<u4'),positions))))
                products=dict(offsets_sha256=digest(actual),result_sha256=digest(result))
            traces=list((e.path/'trace').rglob('*kernel_trace.csv'));agents=list((e.path/'trace').rglob('*agent_info.csv'))
            if len(traces)>1 or len(agents)>1:raise ValueError('multiple trace/agent tables')
            kernels=list(csv.DictReader(traces[0].open())) if traces else [];app=[r for r in kernels if not r['Kernel_Name'].startswith('__amd_rocclr_')]
            names=[r['Kernel_Name'] for r in app];identity=(not names if expected_kernels==0 else len(names)==1 and 'image_jpeg_serial_prefix::serial<' in names[0] if expected_kernels==1 else len(names)==3 and all(any('image_jpeg_checked_prefix::'+stage+'<' in name for name in names) for stage in ['tiles','bases','finish']))
            checks.append(dict(check='actual-frozen-dispatch-kernels',passed=len(app)==expected_kernels and identity,expected=expected_kernels,actual=names))
            allowed={d['pci_bdf'] for d in observed['devices'] if d['physical_id']==1};lookup={r['Node_Id']:r for r in csv.DictReader(agents[0].open())} if agents else {};valid=True
            for row in kernels:
                agent=lookup[row['Agent_Id'].split()[-1]];loc=int(agent['Location_Id']);address=f"{int(agent['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}"
                valid &= address in allowed and int(row['End_Timestamp'])>int(row['Start_Timestamp']) and int(row['Grid_Size_X'])>0
            checks.append(dict(check='all-real-kernels-on-GPU1',passed=valid and (bool(kernels) or expected_kernels==0)))
        except Exception as error:checks.append(dict(check='validation-exception',passed=False,error=repr(error)))
        status='PASSED' if all(x['passed'] for x in checks) else 'FAILED';row=dict(case=c['id'],status=status,checks=checks,metadata=metadata,products=products,binary_sha256=b['binary_sha256'],experiment_id=e.id)
        write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks));rows.append(row);write(REPORT,rows)
        record('IMG-01','prefix保留边界 '+c['id']+'：'+status+'；数值/错误状态与实际分派kernel同验。',[row['evidence']]);print(c['id'],status,flush=True)
    return int(any(r['status']!='PASSED' for r in rows))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','build','run']);args=parser.parse_args();raise SystemExit(globals()[args.action]())
