#!/usr/bin/env python3
"""Freeze and check exact integer DC boundaries on the isolated GPU candidate."""
import argparse,json
from pathlib import Path
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
PROFILE=ROOT/'migration/rewrite/image-encoder-DC-boundary-profile.json'
SOURCE=ROOT/'rocm/probes/image/jpeg_dc_boundaries.hip'

def freeze():
    if PROFILE.exists():raise ValueError('DC boundaries already frozen')
    cases=[]
    for q in [1,2,3,16,255]:
        sums=sorted({-8192,0,8128}|{4*q*(2*k+1)+delta for k in [-4,-1,0,2,3] for delta in [-1,0,1]})
        for total in sums:
            if -8192<=total<=8128:cases.append(dict(id=f'q{q}-sum{total}',quant=q,sum=total))
    e=Experiment('I5','encoder-exact-DC-boundary-contract','CPU-contract',sources=[__file__])
    value=dict(status='FROZEN',cases=cases,gate='Each full GPU 8x8 FDCT DC equals nearest integer to sum/(8*q), exact half ties away from zero; exact integer CPU arithmetic.',scope='DC only; full image quality and fresh independent heldouts are separately required.')
    write(e.path/'profile.json',value);value['evidence']=e.finish('OBSERVED');write(PROFILE,value)
    record('IMG-01','冻结'+str(len(cases))+'组独立DC边界：Q1/2/3/16/255、正负half前/等/后、像素极值与零；整数参考且门槛精确。',[value['evidence']]);print(len(cases))

def run():
    from snapshot import capture
    p=json.loads(PROFILE.read_text());bp=ROOT/'migration/reports/image-encoder-rounding-candidate-build.json';b=json.loads(bp.read_text())
    if b['status']!='BUILT' or any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()):raise ValueError('stale candidate closure')
    common=ROOT/'build/image-encoder-exact-DC-rounding-candidate/common';core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay';jpeg=ROOT/'build/cpu-codecs'
    e=Experiment('I5','encoder-exact-DC-GPU-boundaries','rocm-probe',sources=[__file__,SOURCE,PROFILE,bp,*[ROOT/n for n in b['dependencies']]])
    write(e.path/'backend.observed.json',capture());binary=e.path/'probe';pairs=e.path/'inputs.txt';pairs.write_text(''.join(f"{c['quant']} {c['sum']}\n" for c in p['cases']))
    rc=e.command(['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-I'+str(common),'-I'+str(jpeg/'include'),'-x','hip',str(SOURCE),'-o',str(binary),'-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64'],'build-full-FDCT-boundary-probe')
    rc=rc or e.command([str(binary),str(pairs)],'execute-frozen-DC-boundaries');checks=[dict(check='build-and-execute',passed=rc==0)];comparisons=[]
    try:
        rows=json.loads((e.path/e.commands[-1]['stdout']).read_text());checks.append(dict(check='exact-frozen-rows',passed=len(rows)==len(p['cases'])))
        for case,row in zip(p['cases'],rows):
            s,q=case['sum'],case['quant'];expected=(1 if s>=0 else -1)*((abs(s)+4*q)//(8*q))
            checks.append(dict(check=case['id'],passed=row==dict(quant=q,sum=s,DC=expected)));comparisons.append(dict(case=case['id'],actual=row,expected_DC=expected))
    except Exception as error:checks.append(dict(check='validation-exception',passed=False,error=repr(error)))
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(status=status,checks=checks,comparisons=comparisons,binary_sha256=digest(binary) if binary.exists() else None)
    write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-DC-boundaries.json',row)
    record('IMG-01','完整GPU FDCT的'+str(len(p['cases']))+'组DC精确边界：'+status+'；只验证隔离候选DC数学，不代替整图资格。',[row['evidence']]);print(status);return int(status!='PASSED')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','run']);a=parser.parse_args();raise SystemExit(globals()[a.action]())
