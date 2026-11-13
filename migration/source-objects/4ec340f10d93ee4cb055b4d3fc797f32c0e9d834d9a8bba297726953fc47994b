#!/usr/bin/env python3
"""Freeze, build and verify reusable event-driven GPU JPEG slots."""
import argparse,hashlib,json,re
from pathlib import Path
import numpy as np
from PIL import Image,JpegImagePlugin
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_completion_inventory import closure

PROFILE=ROOT/'migration/rewrite/image-encoder-pipeline-profile.json'
BUILD=ROOT/'migration/reports/image-encoder-pipeline-build.json'
SOURCE=ROOT/'rocm/probes/image/jpeg_encoder_pipeline.hip'
HEADER=ROOT/'rocm/common/image/jpeg_encoder_pipeline.hpp'

def freeze():
    if PROFILE.exists():raise ValueError('profile already frozen')
    cases=[];folder=ROOT/'migration/fixtures/image-encoder-pipeline';folder.mkdir(parents=True,exist_ok=True)
    for index,(width,height) in enumerate([(1,1),(1,257),(257,1),(17,19),(256,257),(511,509)]):
        rng=np.random.default_rng(14631+index);rgb=rng.integers(0,256,(height,width,3),dtype=np.uint8)
        path=folder/f'{width}x{height}.rgb';rgb.tofile(path)
        for opt in (False,True):
            cases.append(dict(id=f'{width}x{height}-'+('optimized' if opt else 'standard'),width=width,height=height,
                quality=[1,75,100,90,80,95][index],sampling=1 if index%2 else 2,optimized=opt,download=True,
                jobs=6,path=str(path.relative_to(ROOT)),sha256=digest(path),seed=14631+index))
    for opt in (False,True):
        base=next(x for x in cases if x['width']==17 and x['optimized']==opt)
        cases.append(dict(base,id='device-only-'+str(int(opt)),download=False))
    e=Experiment('I5','async-JPEG-slot-exact-reuse-contract','CPU-contract',sources=[__file__,*[ROOT/x['path'] for x in cases]])
    value=dict(status='FROZEN',cases=cases,gates=dict(serial_encoder_bitstream_exact=True,
        independent_decode_geometry_sampling=True,two_pending_slots=True,six_jobs_per_case=True,
        no_workspace_growth_after_two_jobs=True,device_only_no_host_payload=True),
        limits='Component qualification, not full original entrypoint. Large-index guard, OOM cleanup, mixed dimensions, profiler overlap and native held-out comparisons are still separately owed.')
    write(e.path/'contract.json',value);value['evidence']=e.finish('OBSERVED');write(PROFILE,value)
    record('IMG-01','冻结异步slot的14组开发验证：单像素/单行列/奇数/MCU边界、Q1/75/100/90/80/95、标准/优化Huffman、两slot六任务复用和不下载模式；与旧串行核心逐字节比较。',[str(PROFILE.relative_to(ROOT)),value['evidence']])

def build():
    from snapshot import capture
    assert json.loads(PROFILE.read_text())['status']=='FROZEN'
    deps,missing=closure(SOURCE)
    # The probe include is resolved using the same explicit include directory.
    if missing:raise ValueError(missing)
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay';jpeg=ROOT/'build/cpu-codecs'
    for path in (jpeg/'include/jpeglib.h',jpeg/'lib/libjpeg.so.62.4.0'):
        deps[str(path.relative_to(ROOT))]=digest(path)
    e=Experiment('I5','async-JPEG-slot-build','rocm-build',sources=[__file__,PROFILE,*[ROOT/x for x in deps],jpeg/'include/jpeglib.h',jpeg/'lib/libjpeg.so.62.4.0'])
    write(e.path/'backend.observed.json',capture());binary=e.path/'probe'
    rc=e.command(['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
        '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2',
        '-D__HIP_PLATFORM_AMD__','-I'+str(ROOT/'rocm/common'),'-I'+str(jpeg/'include'),'-x','hip',str(SOURCE),'-o',str(binary),
        '-L'+str(core/'lib'),'-L'+str(jpeg/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-Wl,-rpath,'+str(jpeg/'lib'),'-lamdhip64','-ljpeg'],'build-async-JPEG-slot')
    value=dict(status='BUILT' if not rc else 'BUILD_ERROR',binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary) if not rc else None,
        dependencies={**deps,str(PROFILE.relative_to(ROOT)):digest(PROFILE)},experiment_id=e.id)
    write(e.path/'build.json',value);value['evidence']=e.finish('EXECUTED' if not rc else 'BUILD_ERROR');write(BUILD,value)
    record('IMG-01','异步JPEG slot候选构建：'+value['status']+'。',[value['evidence']]);print(value['status']);return int(bool(rc))

def run():
    from snapshot import capture
    p=json.loads(PROFILE.read_text());b=json.loads(BUILD.read_text())
    if b['status']!='BUILT' or digest(ROOT/b['binary'])!=b['binary_sha256'] or any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()):raise ValueError('current build required')
    rows=[]
    for case in p['cases']:
        source=ROOT/case['path']
        if digest(source)!=case['sha256']:raise ValueError('input drift')
        e=Experiment('I5','async-JPEG-slot-numeric-reuse','rocm-probe',case=case['id'],sources=[__file__,PROFILE,BUILD,source,*[ROOT/n for n in b['dependencies']]],parent=b['experiment_id'])
        write(e.path/'backend.observed.json',capture());out=e.path/'products'
        cmd=[str(ROOT/b['binary']),str(source),str(case['width']),str(case['height']),str(case['quality']),str(case['sampling']),
             str(int(case['optimized'])),str(case['jobs']),str(int(case['download'])),str(out)]
        rc=e.command(cmd,'async-JPEG-six-jobs-and-serial-oracle',timeout=180)
        reference_dir=e.path/'reference';reference_cmd=cmd.copy();reference_cmd[7]='0';reference_cmd[-1]=str(reference_dir)
        reference_rc=e.command(reference_cmd,'separate-process-serial-oracle',timeout=180)
        checks=[];observed={};products={}
        try:
            observed=json.loads((e.path/'logs/0001-async-JPEG-six-jobs-and-serial-oracle.stdout.log').read_text()) if not rc else {}
            checks=[dict(check='GPU-and-oracle-command-success',passed=rc==reference_rc==0),dict(check='two-pending-six-completed-steady-workspace-reused',passed=observed.get('completed')==6 and observed.get('max_pending')==2 and observed.get('steady_workspace_growths')==0)]
            loaded=re.findall(r'^JPEG_LIBRARY=(.+)$',(e.path/'logs/0001-async-JPEG-six-jobs-and-serial-oracle.stderr.log').read_text(),re.M)
            checks.append(dict(check='actual-loaded-libjpeg-matches-bound-SHA',passed=len(loaded)==1 and
                Path(loaded[0]).resolve()==(ROOT/'build/cpu-codecs/lib/libjpeg.so.62.4.0').resolve() and
                digest(loaded[0])==b['dependencies']['build/cpu-codecs/lib/libjpeg.so.62.4.0']))
            expected={str(i)+'.jpg' for i in range(6)} if case['download'] else set()
            checks.append(dict(check='exact-product-set-and-download-mode',passed={x.name for x in out.glob('*')}==expected and observed.get('payload_download')==case['download']))
            products={};reference=reference_dir/'serial-reference.jpg'
            for path in sorted(out.glob('*.jpg')):
                products[path.name]=dict(sha256=digest(path),bytes=path.stat().st_size)
                with Image.open(path) as image:
                    image.load();shape=image.size;sampling=JpegImagePlugin.get_sampling(image);pixels=image.convert('RGB').tobytes()
                checks.append(dict(check='independent-decode-'+path.name,passed=shape==(case['width'],case['height']) and sampling==(2 if case['sampling']==2 else 0)))
                if path.name!='serial-reference.jpg':checks.append(dict(check='serial-entropy-byte-exact-'+path.name,passed=path.read_bytes()==reference.read_bytes()))
                products[path.name]['decoded_rgb_sha256']=hashlib.sha256(pixels).hexdigest()
        except Exception as error:
            checks.append(dict(check='validation-exception',passed=False,error=repr(error)))
        status='PASSED' if all(x['passed'] for x in checks) else 'FAILED'
        row=dict(case=case['id'],status=status,checks=checks,observed=observed,products=products,command=cmd,outputs=str(out.relative_to(ROOT)),experiment_id=e.id)
        write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks))
        rows.append(row);write(ROOT/'migration/reports/image-encoder-pipeline-runs.json',rows)
        record('IMG-01','异步slot '+case['id']+'：'+status+'；组件结果不提升整例资格。',[row['evidence']]);print(case['id'],status,flush=True)
    return int(any(x['status']!='PASSED' for x in rows))

def faults():
    from snapshot import capture
    source=ROOT/'rocm/probes/image/jpeg_pipeline_fault.hip';deps,missing=closure(source)
    if missing:raise ValueError(missing)
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay';jpeg=ROOT/'build/cpu-codecs'
    e=Experiment('I5','async-JPEG-slot-allocation-fault-recovery','rocm-negative',sources=[__file__,*[ROOT/n for n in deps],jpeg/'include/jpeglib.h',jpeg/'lib/libjpeg.so.62.4.0'])
    write(e.path/'backend.observed.json',capture());binary=e.path/'probe'
    rc=e.command(['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
        '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2',
        '-D__HIP_PLATFORM_AMD__','-I'+str(ROOT/'rocm/common'),'-I'+str(jpeg/'include'),'-x','hip',str(source),'-o',str(binary),
        '-L'+str(core/'lib'),'-L'+str(jpeg/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-Wl,-rpath,'+str(jpeg/'lib'),'-lamdhip64','-ljpeg'],'build-test-only-fault-injection')
    rc=rc or e.command([str(binary)],'five-inflight-allocation-failures-and-recovery')
    checks=[dict(check='fault-probe-success',passed=rc==0)]
    try:
        rows=[json.loads(line) for line in (e.path/'logs/0002-five-inflight-allocation-failures-and-recovery.stdout.log').read_text().splitlines()]
        checks.append(dict(check='five-errors-poison-and-new-slot-recovers',passed=[r['fault_after'] for r in rows]==[7,10,20,27,30] and all(r['rejected'] and r['reuse_rejected'] and r['new_slot_recovered'] for r in rows)))
    except Exception as error:checks.append(dict(check='fault-receipt-parsed',passed=False,error=repr(error)))
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';value=dict(status=status,checks=checks)
    write(e.path/'result.json',value);value['evidence']=e.finish('PASSED' if status=='PASSED' else 'RUNTIME_ERROR',dict(status=status,checks=checks))
    write(ROOT/'migration/reports/image-encoder-pipeline-faults.json',value)
    record('IMG-01','复审修复后的5处提交中途分配故障注入：'+status+'；失败slot排空并禁止复用，新slot恢复执行。',[value['evidence']]);print(status);return int(status!='PASSED')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','build','run','faults']);args=parser.parse_args()
    raise SystemExit(globals()[args.action]())
