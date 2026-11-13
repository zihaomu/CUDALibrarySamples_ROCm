#!/usr/bin/env python3
"""Build an isolated exact-DC/ties-away candidate without changing published code."""
import argparse,json,shutil
from pathlib import Path
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

BUILD=ROOT/'migration/reports/image-encoder-rounding-candidate-build.json'
PROFILE=ROOT/'migration/rewrite/image-encoder-quality-profile.json'

def build():
    from snapshot import capture
    base=ROOT/'migration/reports/image-encoder-instances-v2-build.json';b=json.loads(base.read_text())
    if any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()):raise ValueError('current production sources required')
    folder=ROOT/'build/image-encoder-exact-DC-rounding-candidate';folder.mkdir(parents=True,exist_ok=True);copies=[]
    for name in b['dependencies']:
        if name.startswith('rocm/common/'):
            source=ROOT/name;dest=folder/'common'/Path(name).relative_to('rocm/common');dest.parent.mkdir(parents=True,exist_ok=True)
            data=source.read_text()
            if source.name=='jpeg_wide_transform.hpp':
                old='coefficients[index]=static_cast<short>(__float2int_rn(sum*normalizer/quant[index%64]));'
                if data.count(old)!=1:raise ValueError('unexpected FDCT source')
                replacement='''const float scaled=sum*normalizer/quant[index%64];
    const int whole=__float2int_rz(scaled);const float fraction=scaled-float(whole);
    coefficients[index]=static_cast<short>(whole+(fraction>=0.5f?1:(fraction<=-0.5f?-1:0)));'''
                data=data.replace(old,replacement)
                normalizer='const float normalizer=(u?1.0f:0.7071067811865475f)*(v?1.0f:0.7071067811865475f)*0.25f;'
                if data.count(normalizer)!=1:raise ValueError('unexpected DC normalizer')
                data=data.replace(normalizer,'const float normalizer=(!u&&!v)?0.125f:(u?1.0f:0.7071067811865475f)*(v?1.0f:0.7071067811865475f)*0.25f;')
            if dest.exists() and dest.read_text()!=data:raise ValueError('candidate source already exists with other contents')
            dest.write_text(data);copies.append(dest)
    source=ROOT/'rocm/ported/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp'
    jpeg=ROOT/'build/cpu-codecs';core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay'
    deps={str(p.relative_to(ROOT)):digest(p) for p in [source,PROFILE,base,*copies,jpeg/'include/jpeglib.h',jpeg/'lib/libjpeg.so.62.4.0']}
    e=Experiment('I5','encoder-ties-away-candidate-build','rocm-build',sources=[__file__,*[ROOT/n for n in deps]])
    write(e.path/'backend.observed.json',capture());binary=e.path/'sample'
    rc=e.command(['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),
        '--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-I'+str(folder/'common'),'-I'+str(jpeg/'include'),'-x','hip',str(source),'-o',str(binary),
        '-L'+str(core/'lib'),'-L'+str(jpeg/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-Wl,-rpath,'+str(jpeg/'lib'),'-lamdhip64','-ljpeg'],'build-isolated-rounding-candidate')
    row=dict(status='BUILT' if rc==0 else 'BUILD_ERROR',binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary) if binary.exists() else None,dependencies=deps,
        experiment_id=e.id,scope='DC normalizer is exact 1/8; FDCT quantization rounds exact .5 ties away from zero. Truncation plus fractional comparison avoids adding 0.5 rounding near ties. Other-frequency normalization and production tree unchanged.')
    write(e.path/'build.json',row);row['evidence']=e.finish('EXECUTED' if rc==0 else 'BUILD_ERROR');write(BUILD,row)
    record('IMG-01','第二独立FDCT候选构建：'+row['status']+'；DC使用精确1/8、半整数ties远离零，当前正式实现保持不变，先验证已冻结矩阵和DC边界。',[row['evidence']]);print(row['status']);return int(rc!=0)

def run():
    from snapshot import capture
    from image_encoder_quality_run import arguments
    b=json.loads(BUILD.read_text());p=json.loads(PROFILE.read_text());rows=[]
    if b['status']!='BUILT' or digest(ROOT/b['binary'])!=b['binary_sha256'] or any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()):raise ValueError('stale isolated candidate')
    for c in p['cases']:
        i=next(i for i in p['inputs'] if i['id']==c['input']);source=ROOT/i['path']
        if digest(source)!=i['sha256']:raise ValueError('frozen input drift')
        e=Experiment('I5','encoder-ties-away-quality-candidate','rocm-candidate',case=c['id'],sources=[__file__,ROOT/'tools/moat/image_encoder_quality_run.py',BUILD,PROFILE,source,*[ROOT/n for n in b['dependencies']]])
        write(e.path/'backend.observed.json',capture());indir=e.path/'inputs';indir.mkdir();shutil.copyfile(source,indir/'image.bmp');out=e.path/'products';out.mkdir()
        rc=e.command(arguments(c,ROOT/b['binary'],indir,out),'isolated-original-entry',timeout=300)
        products=[dict(name=x.name,path=str(x.relative_to(ROOT)),sha256=digest(x),bytes=x.stat().st_size) for x in sorted(out.iterdir()) if x.is_file()]
        checks=[dict(check='current-candidate-command',passed=rc==0),dict(check='exact-one-product',passed={x.name for x in out.iterdir()}=={'0.jpg'} and len(products)==1)]
        status='PASSED' if all(x['passed'] for x in checks) else 'FAILED';row=dict(case=c['id'],status=status,checks=checks,products=products,input=i,binary_sha256=b['binary_sha256'],experiment_id=e.id)
        write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks));rows.append(row);write(ROOT/'migration/reports/image-encoder-rounding-candidate-runs.json',rows)
        record('IMG-01','独立FDCT候选运行 '+c['id']+'：'+status+'；仅执行/文件检查，数值另验，不替代正式资格。',[row['evidence']]);print(c['id'],status,flush=True)
        if status!='PASSED':return 1
    return 0

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','run']);a=parser.parse_args();raise SystemExit(globals()[a.action]())
