#!/usr/bin/env python3
"""Measure and freeze mode-specific checked-prefix dispatch thresholds."""
import argparse,json,statistics
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

PROFILE=ROOT/'migration/rewrite/image-prefix-dispatch-profile.json'
INPUTS=ROOT/'migration/rewrite/image-prefix-dispatch-inputs.json'
BUILD=ROOT/'migration/reports/image-prefix-dispatch-build.json'
REPORT=ROOT/'migration/reports/image-prefix-dispatch-runs.json'
SELECTION=ROOT/'migration/rewrite/image-prefix-dispatch-selection.json'
SOURCE=ROOT/'rocm/probes/image/jpeg_checked_prefix_bench.hip'

def freeze_inputs():
    if INPUTS.exists():raise ValueError('dispatch input bytes already frozen')
    p=json.loads(PROFILE.read_text());folder=ROOT/'migration/fixtures/image-prefix-dispatch';folder.mkdir(parents=True,exist_ok=True);rows=[]
    for c in p['cases']:
        dtype='<u2' if c['mode']=='bits' else 'u1';values=(np.arange(c['count'],dtype=np.uint64)*1664525+c['seed'])&0xffffffff
        if c['pattern']=='mixed':values=values%4096+1 if c['mode']=='bits' else (values^(values>>16))&255
        elif c['pattern']=='zero':values[:]=0
        elif c['pattern']=='excess':values[:]=4097
        elif c['pattern']=='maximum':values[:]=4096 if c['mode']=='bits' else 255
        else:raise ValueError('unknown frozen pattern')
        path=folder/(c['id']+('.u16' if c['mode']=='bits' else '.u8'));values.astype(dtype).tofile(path)
        rows.append(dict(case=c['id'],path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=digest(path),dtype=dtype))
    e=Experiment('I5','checked-prefix-exact-input-bytes','CPU-contract',sources=[__file__,PROFILE,*[ROOT/r['path'] for r in rows]])
    result=dict(status='FROZEN',profile_sha256=digest(PROFILE),inputs=rows)
    write(e.path/'inputs.json',result);result['evidence']=e.finish('OBSERVED');write(INPUTS,result)
    record('IMG-01','33组checked prefix开发输入字节封存：固定little-endian dtype、长度和SHA，独立CPU参考使用uint64累计；尚未运行候选测量。',[str(INPUTS.relative_to(ROOT)),result['evidence']]);print(result['evidence'])

def build():
    from snapshot import capture
    from image_completion_inventory import closure
    deps,missing=closure(SOURCE)
    if missing:raise ValueError(missing)
    for path in (PROFILE,INPUTS):deps[str(path.relative_to(ROOT))]=digest(path)
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay'
    e=Experiment('I5','checked-prefix-dispatch-build','rocm-build',sources=[__file__,*[ROOT/n for n in deps]])
    write(e.path/'backend.observed.json',capture());binary=e.path/'probe'
    rc=e.command(['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
        '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2',
        '-D__HIP_PLATFORM_AMD__','-I'+str(ROOT/'rocm/common'),'-x','hip',str(SOURCE),'-o',str(binary),
        '-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64'],'build-checked-prefix-dispatch')
    row=dict(status='BUILT' if rc==0 else 'BUILD_ERROR',binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary) if rc==0 else None,dependencies=deps,experiment_id=e.id)
    write(e.path/'build.json',row);row['evidence']=e.finish('EXECUTED' if rc==0 else 'BUILD_ERROR');write(BUILD,row)
    record('IMG-01','checked串行/分块prefix同源测量构建：'+row['status']+'。',[row['evidence']]);print(row['status']);return int(rc!=0)

def current():
    b=json.loads(BUILD.read_text())
    if b['status']!='BUILT' or digest(ROOT/b['binary'])!=b['binary_sha256'] or any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()):raise ValueError('current dispatch binary required')
    return b

def run():
    from snapshot import capture
    b=current();p=json.loads(PROFILE.read_text());inputs=json.loads(INPUTS.read_text());rows=[]
    if inputs['profile_sha256']!=digest(PROFILE) or [r['case'] for r in inputs['inputs']]!=[c['id'] for c in p['cases']]:raise ValueError('frozen input/profile mismatch')
    for c,spec in zip(p['cases'],inputs['inputs']):
        source=ROOT/spec['path']
        if source.stat().st_size!=spec['bytes'] or digest(source)!=spec['sha256']:raise ValueError('frozen bytes drift')
        values=np.fromfile(source,dtype=spec['dtype']).astype(np.uint64)
        add=(values==255).astype(np.uint64) if c['mode']=='stuff' else values
        cumulative=np.cumsum(add,dtype=np.uint64);total=int(cumulative[-1])+(c['count'] if c['mode']=='stuff' else 0)
        expected=cumulative-add+(np.arange(c['count'],dtype=np.uint64) if c['mode']=='stuff' else 0)
        errors=int(c['mode']=='bits' and bool(np.any((values==0)|(values>4096))))
        if total>0xffffffff-(7 if c['mode']=='bits' else 0):errors|=2;total=0
        e=Experiment('I5','checked-prefix-dispatch-measurement','rocm-GPU-benchmark',case=c['id'],sources=[__file__,PROFILE,INPUTS,BUILD,source,*[ROOT/n for n in b['dependencies']]],parent=b['experiment_id'])
        write(e.path/'backend.observed.json',capture());out=e.path/'outputs'
        rc=e.command([str(ROOT/b['binary']),c['mode'],str(source),str(out),str(int(c['timed']))],'correctness-gated-paired-prefix-events',timeout=300)
        checks=[dict(check='command-success',passed=rc==0)];metrics={};products={}
        try:
            metrics=json.loads((e.path/'logs/0001-correctness-gated-paired-prefix-events.stdout.log').read_text())
            checks.append(dict(check='frozen-shape-host-guard-and-metadata',passed=metrics['count']==c['count'] and metrics['host_reference_passed'] is True and metrics['errors']==errors and metrics['total']==total))
            checks.append(dict(check='exact-output-file-set',passed={x.name for x in out.iterdir()}=={'serial.u32','tiled.u32','serial-result.u32','tiled-result.u32'}))
            for name in ['serial','tiled']:
                path=out/(name+'.u32');metadata=out/(name+'-result.u32')
                actual=np.fromfile(path,dtype='<u4');result=np.fromfile(metadata,dtype='<u4')
                checks.append(dict(check=name+'-complete-offsets-and-independent-metadata',passed=path.stat().st_size==c['count']*4 and metadata.stat().st_size==8 and result.tolist()==[total,errors] and (bool(errors) or np.array_equal(actual,expected))))
                times=metrics[name+'_ms'];checks.append(dict(check=name+'-frozen-positive-timing-inventory',passed=len(times)==(20 if c['timed'] else 0) and all(np.isfinite(t) and t>0 for t in times)))
                if times:metrics[name+'_median_ms']=statistics.median(times)
                products[name]=dict(offset_sha256=digest(path),metadata_sha256=digest(metadata))
        except Exception as error:checks.append(dict(check='validation-exception',passed=False,error=repr(error)))
        status='PASSED' if all(x['passed'] for x in checks) else 'FAILED';row=dict(case=c['id'],status=status,checks=checks,metrics=metrics,outputs=products,binary_sha256=b['binary_sha256'],experiment_id=e.id)
        write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks));rows.append(row);write(REPORT,rows)
        record('IMG-01','checked prefix '+c['id']+'：'+status+'；serial/tiled完整数值核对及交替event样本保留。',[row['evidence']]);print(c['id'],status,metrics.get('serial_median_ms'),metrics.get('tiled_median_ms'),flush=True)
    return int(any(r['status']!='PASSED' for r in rows))

def select():
    from audit import check
    if SELECTION.exists():raise ValueError('dispatch choice already frozen')
    b=current();p=json.loads(PROFILE.read_text());rows=json.loads(REPORT.read_text())
    if [r['case'] for r in rows]!=[c['id'] for c in p['cases']] or len(rows)!=33:raise ValueError('measurement coverage gap')
    for r in rows:
        if r['status']!='PASSED' or not r['checks'] or not all(c['passed'] for c in r['checks']) or check(ROOT/r['evidence']):raise ValueError('invalid measurement evidence')
        if json.loads((ROOT/r['evidence']/'result.json').read_text())!={k:v for k,v in r.items() if k!='evidence'}:raise ValueError('unsealed report mutation')
        if r['binary_sha256']!=b['binary_sha256']:raise ValueError('measurement binary mismatch')
    thresholds={};comparisons=[]
    for mode in ['bits','stuff']:
        threshold=0;active=True
        for c,r in zip(p['cases'],rows):
            if c['mode']!=mode or not c['timed']:continue
            m=r['metrics'];win=statistics.median(m['serial_ms'])<=0.95*statistics.median(m['tiled_ms'])
            comparisons.append(dict(mode=mode,count=c['count'],serial_has_required_margin=win,serial_median_ms=m['serial_median_ms'],tiled_median_ms=m['tiled_median_ms']))
            if active and win:threshold=c['count']
            else:active=False
        thresholds[mode]=threshold
    e=Experiment('I5','checked-prefix-dispatch-selection','CPU-contract',sources=[__file__,PROFILE,INPUTS,BUILD,REPORT,*[ROOT/n for n in b['dependencies']]])
    value=dict(status='FROZEN',thresholds=thresholds,selection_rule=p['selection'],comparisons=comparisons,
        evidence_references=[r['evidence'] for r in rows],build_evidence=b['evidence'],remaining='Boundary holdout freeze/run, integration and current original-entry regression.')
    write(e.path/'selection.json',value);value['evidence']=e.finish('OBSERVED');write(SELECTION,value)
    record('IMG-01','按预登记5%连续优势规则冻结prefix阈值：bits='+str(thresholds['bits'])+'、stuff='+str(thresholds['stuff'])+'；等待独立边界集，未接入生产。',[str(SELECTION.relative_to(ROOT)),value['evidence']]);print(thresholds)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze_inputs','build','run','select']);args=parser.parse_args();raise SystemExit(globals()[args.action]())
