#!/usr/bin/env python3
"""Build and execute the isolated watershed candidate with immutable receipts."""
import argparse,json
from pathlib import Path
from experiment import ROOT,Experiment,digest,write
from snapshot import capture
from image_completion_progress import record
HEADER=ROOT/'rocm/common/image/watershed_v2.hpp'
PROBE=ROOT/'rocm/probes/image/watershed_v2_probe.cpp'
BUILD=ROOT/'migration/reports/image-watershed-v2-build.json'

def build():
    e=Experiment('I3','watershed-directed-marker-candidate-build','rocm-build',sources=[__file__,HEADER,PROBE]);write(e.path/'backend.observed.json',capture())
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay';binary=e.path/'watershed-v2'
    rc=e.command(['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-I'+str(ROOT/'rocm/common'),'-x','hip',str(PROBE),'-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(binary)],'build',timeout=300)
    result=dict(status='BUILT' if rc==0 else 'BUILD_ERROR',return_code=rc,binary=dict(path=str(binary.relative_to(ROOT)),sha256=digest(binary)) if rc==0 else None,dependencies={str(p.relative_to(ROOT)):digest(p) for p in [HEADER,PROBE]});write(e.path/'build.json',result);result['evidence']=e.finish('EXECUTED' if rc==0 else 'BUILD_ERROR');write(BUILD,result)
    record('IMG-02','隔离HIP候选核心构建：'+result['status']+'。固定严格下降、GPU有向最小marker传播、灰度边界和压紧；未替换生产入口。',[result['evidence']]);print(result['status'],result['evidence']);return int(rc!=0)

def run(mode):
    build=json.loads(BUILD.read_text());profile=ROOT/'migration/rewrite/image-watershed-semantics-profile.json';p=json.loads(profile.read_text());folder=ROOT/'migration/fixtures/image-watershed-semantics';binary=ROOT/build['binary']['path']
    if digest(binary)!=build['binary']['sha256'] or any(digest(ROOT/f)!=sha for f,sha in build['dependencies'].items()):raise ValueError('candidate build drift')
    e=Experiment('I3','watershed-directed-marker-development-'+mode,'rocm',sources=[__file__,HEADER,PROBE,BUILD,profile,folder/'cases.txt',binary,*[ROOT/i['path'] for i in p['inputs']]]);write(e.path/'backend.observed.json',capture());outputs=e.path/'outputs'
    rc=e.command([str(binary),str(folder),str(outputs),mode],'development-inputs',timeout=300)
    files={f.name:dict(bytes=f.stat().st_size,sha256=digest(f)) for f in outputs.glob('*') if f.is_file()} if outputs.exists() else {}
    result=dict(status='EXECUTED' if rc==0 else 'COMMAND_FAILED',return_code=rc,mode=mode,products=files,output_dir=str(outputs.relative_to(ROOT)),evidence_references=[build['evidence']],scope='Development candidate only; no original-entry qualification.');write(e.path/'run.json',result);result['evidence']=e.finish('EXECUTED' if rc==0 else 'COMMAND_FAILED');write(ROOT/f'migration/reports/image-watershed-v2-development-{mode}.json',result)
    record('IMG-02','隔离HIP候选在18开发输入、'+mode+'布局执行：'+result['status']+'、'+str(len(files))+'产品；ROI/padding/源图保护由实际probe检查，数值待独立验收。',[result['evidence']]);print(result['status'],len(files),result['evidence']);return int(rc!=0)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);p.add_argument('--mode',default='padded',choices=['compact','padded','inplace']);a=p.parse_args();raise SystemExit(build() if a.action=='build' else run(a.mode))
