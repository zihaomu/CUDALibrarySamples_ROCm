#!/usr/bin/env python3
"""Freeze/build/test checked production prefix before integrating encoder state."""
import argparse,json
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

PROFILE=ROOT/'migration/rewrite/image-checked-prefix-profile.json'
BUILD=ROOT/'migration/reports/image-checked-prefix-build.json'
HEADER=ROOT/'rocm/common/image/jpeg_checked_prefix.hpp'
SOURCE=ROOT/'rocm/probes/image/jpeg_checked_prefix.hip'

def freeze():
    if PROFILE.exists():raise ValueError('profile already frozen')
    cases=[dict(id=f'{mode}-{n}',mode=mode,count=n,error=0) for mode in ('bits','stuff') for n in (1,255,256,257,4096,65536)]
    cases += [dict(id='empty-rejected',mode='empty',count=0,error=0),
              dict(id='zero-length-rejected',mode='bits',count=257,error=1,replace=0),
              dict(id='4097-length-rejected',mode='bits',count=257,error=1,replace=4097),
              dict(id='uint32-bit-total-overflow',mode='bits',count=1048576,error=2,constant=4096)]
    e=Experiment('I5','checked-JPEG-prefix-exact-and-error-contract','CPU-contract',sources=[__file__])
    value=dict(status='FROZEN',cases=cases,seed=713,exact_offsets_and_total=True,
               rejection='Error bits must be checked before pack; any zero or >4096 block length is invalid. Accumulate sums in uint64; reject totals above UINT32_MAX-7. Empty input returns hipErrorInvalidValue.',
               scope='New component only; final encoder pipeline and all affected entrypoint qualification still required.')
    write(e.path/'profile.json',value);value['evidence']=e.finish('OBSERVED');write(PROFILE,value)
    record('IMG-01','冻结生产 prefix 的16组逐元素/总数/错误门槛：包括零长度、4097长度和真实4Gbit累计溢出；组件尚未接入入口。',[str(PROFILE.relative_to(ROOT)),value['evidence']])

def build():
    from snapshot import capture
    profile=json.loads(PROFILE.read_text());assert profile['status']=='FROZEN'
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay'
    e=Experiment('I5','checked-JPEG-prefix-build','rocm-build',sources=[__file__,HEADER,SOURCE,PROFILE]);write(e.path/'backend.observed.json',capture())
    binary=e.path/'probe';rc=e.command(['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
        '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2',
        '-D__HIP_PLATFORM_AMD__','-I'+str(HEADER.parent),'-x','hip',str(SOURCE),'-o',str(binary),
        '-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64'],'build-checked-prefix')
    value=dict(status='BUILT' if not rc else 'BUILD_ERROR',binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary) if not rc else None,
               dependencies={str(p.relative_to(ROOT)):digest(p) for p in [HEADER,SOURCE,PROFILE]},experiment_id=e.id)
    write(e.path/'build.json',value);value['evidence']=e.finish('EXECUTED' if not rc else 'BUILD_ERROR');write(BUILD,value)
    record('IMG-01','带非法块长度和64位累计检查的生产 prefix 构建：'+value['status']+'。',[value['evidence']]);print(value['status']);return int(bool(rc))

def run():
    from snapshot import capture
    profile=json.loads(PROFILE.read_text());build=json.loads(BUILD.read_text())
    if build['status']!='BUILT' or digest(ROOT/build['binary'])!=build['binary_sha256'] or any(digest(ROOT/n)!=h for n,h in build['dependencies'].items()):raise ValueError('stale build')
    rows=[]
    for case in profile['cases']:
        e=Experiment('I5','checked-JPEG-prefix-exact-and-guards','rocm-probe',case=case['id'],sources=[__file__,PROFILE,BUILD,HEADER,SOURCE],parent=build['experiment_id'])
        write(e.path/'backend.observed.json',capture());rng=np.random.default_rng(profile['seed']);n=case['count'];mode=case['mode']
        data=rng.integers(1,4097,n,dtype=np.uint16) if mode=='bits' else rng.integers(0,256,n,dtype=np.uint8)
        if mode=='stuff':data[::7]=255
        if 'replace' in case:data[n//2]=case['replace']
        if 'constant' in case:data[:]=case['constant']
        src=e.path/'input.bin';out=e.path/'offsets.bin';data.tofile(src)
        rc=e.command([str(ROOT/build['binary']),mode,str(src),str(out)],'exact-prefix-and-error-flags')
        result=json.loads((e.path/'logs/0001-exact-prefix-and-error-flags.stdout.log').read_text()) if not rc else {}
        checks=[dict(check='probe-success',passed=rc==0)]
        if mode=='empty':checks.append(dict(check='empty-input-rejected-before-dispatch',passed=result.get('empty_rejected') is True))
        else:
            checks.append(dict(check='expected-error-mask',passed=result.get('errors')==case['error']))
            if not case['error']:
                value=(data==255).astype(np.uint64) if mode=='stuff' else data.astype(np.uint64)
                offsets=np.cumsum(value)-value
                total=int(value.sum())
                if mode=='stuff':offsets+=np.arange(n,dtype=np.uint64);total+=n
                actual=np.fromfile(out,'<u4') if out.exists() else np.array([])
                checks.append(dict(check='all-CPU-uint64-exclusive-offsets-and-total-exact',passed=np.array_equal(actual,offsets) and result.get('total')==total))
            if case['error']==2:checks.append(dict(check='overflow-does-not-publish-wrapped-total',passed=result.get('total')==0))
        status='PASSED' if all(x['passed'] for x in checks) else 'FAILED'
        value=dict(case=case['id'],status=status,observed=result,checks=checks,input_sha256=digest(src),experiment_id=e.id)
        write(e.path/'result.json',value);value['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks))
        rows.append(value);write(ROOT/'migration/reports/image-checked-prefix-runs.json',rows)
        record('IMG-01','checked prefix '+case['id']+'：'+status+'；错误模式仅通过显式拒绝，不能进入码流打包。',[value['evidence']]);print(case['id'],status,flush=True)
    return int(any(x['status']!='PASSED' for x in rows))

def oversize():
    from snapshot import capture
    build=json.loads(BUILD.read_text())
    if build['status']!='BUILT' or digest(ROOT/build['binary'])!=build['binary_sha256'] or any(digest(ROOT/n)!=h for n,h in build['dependencies'].items()):raise ValueError('current prefix build required')
    rows=[]
    for mode,item_size in [('stuff',1),('bits',2)]:
        e=Experiment('I5','checked-prefix-oversize-file-rejection','rocm-negative',case=mode,sources=[__file__,BUILD,SOURCE,HEADER])
        write(e.path/'backend.observed.json',capture())
        source=ROOT/'build'/('prefix-oversize-'+e.id+'.bin');size=(2**32+1)*item_size
        with source.open('wb') as file:file.truncate(size)
        write(e.path/'input-generator.json',dict(path=str(source.relative_to(ROOT)),bytes=size,pattern='all zero bytes from sparse truncate',scope='file-length guard; contents must never be read or allocated on host/device'))
        try:rc=e.command([str(ROOT/build['binary']),mode,str(source),str(e.path/'output.bin')],'reject-file-length-before-allocation',timeout=30)
        finally:source.unlink(missing_ok=True)
        stderr=(e.path/'logs/0001-reject-file-length-before-allocation.stderr.log').read_text()
        checks=[dict(check='oversize-rejected-before-output',passed=rc==1 and 'prefix count exceeds uint32' in stderr and not (e.path/'output.bin').exists())]
        status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(mode=mode,status=status,checks=checks)
        write(e.path/'result.json',row);row['evidence']=e.finish('EXPECTED_REJECTION' if status=='PASSED' else 'RUNTIME_ERROR',dict(status=status,checks=checks));rows.append(row)
        write(ROOT/'migration/reports/image-checked-prefix-oversize.json',rows)
        record('IMG-01','prefix超uint32元素数稀疏文件 '+mode+'：'+status+'；分配/读取内容前拒绝，验证复审修复。',[row['evidence']]);print(mode,status,flush=True)
    return int(any(x['status']!='PASSED' for x in rows))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','build','run','oversize']);args=parser.parse_args()
    raise SystemExit(globals()[args.action]())
