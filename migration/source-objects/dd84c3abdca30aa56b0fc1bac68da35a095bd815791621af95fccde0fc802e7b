#!/usr/bin/env python3
"""Build and run both original-format file workflows using the complete HIP core."""
import argparse,json,shutil
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_completion_progress import record
CONTRACT=ROOT/'migration/rewrite/image-watershed-completion-contract.json'
INVENTORY=ROOT/'migration/rewrite/image-watershed-profile.json'
BUILD=ROOT/'migration/reports/image-watershed-completion-entries-build.json'
PORTS={'NPP':'rocm/ported/NPP/watershedSegmentation/watershedSegmentation.cpp','NPP+':'rocm/ported/NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp'}

def dependencies():
    return [ROOT/'rocm/common/image'/n for n in ['watershed.h','watershed.hip','watershed_v2.hpp','watershed_sample.hpp']]+[ROOT/n for n in PORTS.values()]

def build():
    e=Experiment('I3','watershed-complete-original-entry-build','rocm-build',sources=[__file__,CONTRACT,INVENTORY,*dependencies()]);write(e.path/'backend.observed.json',capture());core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay'
    flags=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-I'+str(ROOT/'rocm/common/image'),'-x','hip'];binaries={};rc=0
    for family,path in PORTS.items():
        output=e.path/('watershedNPPPlus' if family=='NPP+' else 'watershedNPP');rc=e.command([*flags,str(ROOT/path),str(ROOT/'rocm/common/image/watershed.hip'),'-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(output)],'build-'+family,timeout=300)
        if rc:break
        binaries[family]=dict(path=str(output.relative_to(ROOT)),sha256=digest(output))
    result=dict(status='BUILT' if rc==0 and len(binaries)==2 else 'BUILD_ERROR',return_code=rc,binaries=binaries,dependencies={str(p.relative_to(ROOT)):digest(p) for p in dependencies()},contract_sha256=digest(CONTRACT));write(e.path/'build.json',result);result['evidence']=e.finish('EXECUTED' if result['status']=='BUILT' else 'BUILD_ERROR');write(BUILD,result)
    record('IMG-02','两原始文件入口已接入严格下降/有向图共享HIP核心，完整构建：'+result['status']+'；保留原CUDA树及全部原图/文件名，资格仍待整体验收。',[result['evidence']]);print(result['status'],result['evidence']);return int(result['status']!='BUILT')

def run():
    inventory=json.loads(INVENTORY.read_text());build=json.loads(BUILD.read_text());rows=[]
    if build['status']!='BUILT' or any(digest(ROOT/n)!=sha for n,sha in build['dependencies'].items()):raise ValueError('current compiled entries required')
    for sample in inventory['samples']:
        family=sample['sample_id'].split('/')[0];binary=ROOT/build['binaries'][family]['path']
        if digest(binary)!=build['binaries'][family]['sha256']:raise ValueError('binary changed')
        e=Experiment('I3',sample['sample_id'],'rocm-complete-original-entry',sources=[__file__,CONTRACT,INVENTORY,BUILD,binary,*dependencies(),*[ROOT/family/'watershedSegmentation/images'/i['name'] for i in sample['inputs']]]);write(e.path/'backend.observed.json',capture());images=e.path/'images';images.mkdir();work=e.path/'work';work.mkdir()
        for item in sample['inputs']:
            source=ROOT/family/'watershedSegmentation/images'/item['name']
            if source.stat().st_size!=item['bytes'] or digest(source)!=item['sha256']:raise ValueError('original input identity')
            shutil.copyfile(source,images/item['name'])
        rc=e.command([str(binary)],'complete-original-file-workflow',cwd=work,timeout=300);inputs={i['name'] for i in sample['inputs']};outputs={f.name:dict(bytes=f.stat().st_size,sha256=digest(f)) for f in images.iterdir() if f.name not in inputs and f.is_file()};expected=sample['products'];checks=[dict(check='original-entry-exit-zero',passed=rc==0),dict(check='complete-original-product-names-and-extents',passed=set(outputs)==set(expected) and all(outputs[n]['bytes']==expected[n]['bytes'] for n in expected))]
        status='EXECUTED' if all(c['passed'] for c in checks) else 'RUNTIME_ERROR';row=dict(status=status,return_code=rc,sample_id=sample['sample_id'],family=family,outputs=outputs,output_dir=str(images.relative_to(ROOT)),build_evidence=build['evidence'],binary_sha256=digest(binary),contract_sha256=digest(CONTRACT),checks=checks);write(e.path/'run.json',row);row['evidence']=e.finish(status,dict(status=status,checks=checks));rows.append(row);write(ROOT/'migration/reports/image-watershed-completion-entries-runs.json',rows)
        record('IMG-02',family+'原入口完整文件流程：'+status+'，'+str(len(outputs))+'件产品；独立CPU/native和trace/cold证明待补齐，不预记整例通过。',[row['evidence']]);print(family,status,len(outputs))
    return int(any(r['status']!='EXECUTED' for r in rows))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);a=p.parse_args();raise SystemExit(build() if a.action=='build' else run())
