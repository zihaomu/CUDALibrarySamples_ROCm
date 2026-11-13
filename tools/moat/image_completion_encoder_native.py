#!/usr/bin/env python3
"""Build unchanged vendor CMake/C++20 and record bounded 5090 encoder probes."""
import json, shlex, tarfile
from pathlib import Path
from experiment import ROOT, Experiment, digest, write
from image_completion_progress import record

HOST='nvidia-5090x2'
PROFILE=ROOT/'migration/rewrite/image-completion-encoder-contract.json'
REPORT=ROOT/'migration/reports/image-completion-encoder-native.json'

def remote(e,args,label,timeout=300):
    return e.command(['ssh',HOST,shlex.join(args)],label,timeout=timeout)

def main():
    p=json.loads(PROFILE.read_text());source=ROOT/p['source'];cmake=source.parent/'CMakeLists.txt'
    if p['status']!='FROZEN' or digest(source)!=p['source_sha256'] or digest(cmake)!=p['cmake_sha256']:
        raise ValueError('immutable native source contract required')
    inputs=[ROOT/x['path'] for x in p['inputs']]
    if any(digest(ROOT/x['path'])!=x['sha256'] for x in p['inputs']):raise ValueError('input drift')
    e=Experiment('I0','completion-encoder-original-CMake-CXX20','cuda-build',sources=[__file__,PROFILE,source,cmake,*inputs])
    root='/tmp/image-completion-'+e.id
    bundle=e.path/'sources.tar'
    with tarfile.open(bundle,'w') as tar:
        for path in [source,cmake]:tar.add(path,arcname='source/'+path.name)
        for path in inputs:tar.add(path,arcname='inputs/'+path.name)
    rc=remote(e,['mkdir','-p',root],'prepare-native')
    rc=rc or e.command(['scp',str(bundle),HOST+':'+root+'/sources.tar'],'upload-unchanged-source-and-inputs')
    rc=rc or remote(e,['tar','xf',root+'/sources.tar','-C',root],'extract-native')
    rc=rc or remote(e,['cmake','-S',root+'/source','-B',root+'/build',
        '-DCMAKE_CUDA_COMPILER=/usr/local/cuda-13.4/bin/nvcc','-DCUDAToolkit_ROOT=/usr/local/cuda-13.4',
        '-DCMAKE_CUDA_ARCHITECTURES=120','-DCMAKE_BUILD_TYPE=Release'],'original-CMake-configure')
    rc=rc or remote(e,['cmake','--build',root+'/build','--parallel','2'],'original-CXX20-build')
    result=dict(status='BUILT' if not rc else 'NATIVE_BUILD_FAILED',remote=root,source=p['source'],
                source_sha256=digest(source),cmake_sha256=digest(cmake),build_return_code=rc,cases=[])
    write(e.path/'result.json',result)
    result['build_evidence']=e.finish('EXECUTED' if not rc else 'NATIVE_BUILD_FAILED')
    write(REPORT,result)
    record('IMG-00','5090 原始 nvJPEG 多实例 encoder 使用未修改 CMake/C++20 构建：'+result['status']+'。',[result['build_evidence']])
    if rc:return 1
    for case in p['native_probe_cases']:
        e=Experiment('I0','completion-encoder-original-'+case['id'],'cuda-native',sources=[__file__,PROFILE,source,cmake,*inputs])
        out=root+'/outputs/'+e.id
        args=[root+'/build/nvJPEGEncMultipleInstances','-i',root+'/inputs',*case['args']]
        if case['output']:args+=['-o',out]
        config=dict(root=root,output=out,args=args,source_sha256=p['source_sha256'],
                    inputs={Path(x['path']).name:x['sha256'] for x in p['inputs']})
        code='''import hashlib,json,os,pathlib,subprocess,sys
c=json.loads(sys.argv[1]);root=pathlib.Path(c['root']);sha=lambda p:hashlib.file_digest(pathlib.Path(p).open('rb'),'sha256').hexdigest()
assert sha(root/'source/nvJPEGEncMultipleInstances.cpp')==c['source_sha256']
assert {p.name:sha(p) for p in (root/'inputs').iterdir()}==c['inputs']
binary=root/'build/nvJPEGEncMultipleInstances';ldd=subprocess.check_output(['ldd',str(binary)],text=True)
libs={}
for line in ldd.splitlines():
    words=line.split()
    if '=>' in words and len(words)>2 and words[2].startswith('/'):
        path=pathlib.Path(words[2]).resolve();libs[str(path)]=dict(sha256=sha(path),bytes=path.stat().st_size)
receipt=dict(source_sha256=c['source_sha256'],inputs=c['inputs'],binary_sha256=sha(binary),libraries=libs,ldd=ldd,
    physical_device_index=1,CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),
    gpu=subprocess.check_output(['nvidia-smi','--id=1','--query-gpu=name,uuid,pci.bus_id,driver_version','--format=csv,noheader'],text=True).strip(),command=c['args'])
print(json.dumps(receipt),flush=True);pathlib.Path(c['output']).mkdir(parents=True)
rc=subprocess.run(c['args'],cwd=root).returncode
print(json.dumps(dict(return_code=rc,outputs={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in pathlib.Path(c['output']).iterdir()})),flush=True)
sys.exit(rc)
'''
        rc=remote(e,['env','CUDA_VISIBLE_DEVICES=1','python3','-c',code,json.dumps(config,separators=(',',':'))],
                  'original-native-GPU1-with-loader-receipt',timeout=180)
        collected=e.path/'outputs'
        cr=e.command(['scp','-r',HOST+':'+out,str(collected)],'collect-native-products')
        products={path.name:dict(sha256=digest(path),bytes=path.stat().st_size) for path in collected.glob('*') if path.is_file()}
        expected=case['count'] if case['output'] else 0
        checks=[dict(check='actual-native-return-code',passed=rc==0),dict(check='collection',passed=cr==0),
                dict(check='numbered-products',passed=set(products)=={str(i)+'.jpg' for i in range(expected)})]
        row=dict(case=case['id'],status='OBSERVED' if all(x['passed'] for x in checks) else 'FAILED',
                 return_code=rc,collection_return_code=cr,config=config,outputs=str(collected.relative_to(ROOT)),products=products,checks=checks)
        write(e.path/'result.json',row)
        row['evidence']=e.finish('OBSERVED' if row['status']=='OBSERVED' else 'NATIVE_MISMATCH',dict(status=row['status'],checks=checks))
        result['cases'].append(row);write(REPORT,result)
        record('IMG-00','原始 CUDA encoder '+case['id']+'：'+row['status']+'，收集 '+str(len(products))+' 件 JPEG；解码/数值比较待独立参考。',[row['evidence']])
        print(case['id'],row['status'],flush=True)
    return int(any(x['status']!='OBSERVED' for x in result['cases']))

if __name__=='__main__':raise SystemExit(main())
