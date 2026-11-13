#!/usr/bin/env python3
"""Run the frozen full watershed corpus on AMD and both native NVIDIA libraries."""
import argparse,json,shlex,tarfile
from experiment import ROOT,Experiment,digest,write
from snapshot import capture
from image_completion_progress import record
CONTRACT=ROOT/'migration/rewrite/image-watershed-completion-contract.json'
FOLDER=ROOT/'migration/fixtures/image-watershed-completion'
NATIVE=ROOT/'rocm/probes/image/watershed_completion_native.cpp'
ACTIVE=None

def inputs():
    profile=json.loads(CONTRACT.read_text())
    if profile['status']!='FROZEN' or len(profile['inputs'])!=60:raise ValueError('frozen complete inventory')
    if any((ROOT/i['path']).stat().st_size!=i['bytes'] or digest(ROOT/i['path'])!=i['sha256'] for i in profile['inputs']):raise ValueError('frozen input identity')
    expected=''.join(f'{i["id"]} {i["width"]} {i["height"]}\n' for i in profile['inputs'])
    if (FOLDER/'cases.txt').read_text()!=expected:raise ValueError('case order/shape')
    return profile

def native(plus):
    global ACTIVE
    p=inputs();vendor='NPPPlus' if plus else 'NPP';e=Experiment('I3','watershed-complete-native-'+vendor,'cuda',sources=[__file__,NATIVE,CONTRACT,FOLDER/'cases.txt',*[ROOT/i['path'] for i in p['inputs']]]);ACTIVE=e
    remote='/tmp/'+e.id;archive=e.path/'inputs.tar';flags=['-lnppif','-lnppc']
    if plus:
        sdk=next(r for r in json.loads((ROOT/'migration/reports/image-I0-native-private-SDKs.json').read_text()) if r['SDK']=='nppplus');prefix=sdk['remote']+'/libnpp_plus-linux-x86_64-'+sdk['identity']['version']+'_'+sdk['identity']['variant']+'-archive';flags=['-DIMAGE_NPP_PLUS','-I'+prefix+'/include','-L'+prefix+'/lib','-Xlinker','-rpath','-Xlinker',prefix+'/lib','-lnpp_plus_if','-lnpp_plus_c']
    with tarfile.open(archive,'w') as tar:tar.add(NATIVE,arcname='probe.cpp');tar.add(FOLDER,arcname='inputs')
    identity="import hashlib,json,pathlib,subprocess; b=pathlib.Path("+repr(remote+'/probe')+"); s=subprocess.check_output(['ldd',str(b)],text=True); print(s); paths=[b]+[pathlib.Path(line.split('=>',1)[1].strip().split()[0]) for line in s.splitlines() if '=>' in line and line.split('=>',1)[1].strip().startswith('/')]; print(json.dumps({str(p):{'resolved':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths},indent=2))"
    steps=[(['ssh','nvidia-5090x2',shlex.join(['mkdir','-p',remote])],'prepare'),(['scp',str(archive),'nvidia-5090x2:'+remote+'/inputs.tar'],'upload'),(['ssh','nvidia-5090x2',shlex.join(['tar','xf',remote+'/inputs.tar','-C',remote])],'unpack'),(['ssh','nvidia-5090x2',shlex.join(['/usr/local/cuda-13.4/bin/nvcc','-std=c++17','-O2','-arch=sm_120',remote+'/probe.cpp','-o',remote+'/probe',*flags])],'build'),(['ssh','nvidia-5090x2',shlex.join(['python3','-c',identity])],'binary-and-loaded-library-identity'),(['ssh','nvidia-5090x2',shlex.join(['env','CUDA_VISIBLE_DEVICES=1',remote+'/probe',remote+'/inputs',remote+'/outputs'])],'frozen-native-corpus'),(['scp','-r','nvidia-5090x2:'+remote+'/outputs',str(e.path/'outputs')],'collect')]
    rc=0
    for cmd,phase in steps:
        rc=e.command(cmd,phase,timeout=600)
        if rc:break
    result=finish(e,rc,'native-'+vendor);result['vendor']=vendor;result['remote']=remote;seal(e,result,'native-'+vendor)
    return int(result['status']!='EXECUTED')

def finish(e,rc,key):
    outputs=e.path/'outputs';files={f.name:dict(bytes=f.stat().st_size,sha256=digest(f)) for f in outputs.glob('*') if f.is_file()} if outputs.exists() else {}
    return dict(status='EXECUTED' if rc==0 else 'COMMAND_FAILED',return_code=rc,key=key,products=files,output_dir=str(outputs.relative_to(ROOT)),contract_sha256=digest(CONTRACT))

def seal(e,result,key):
    write(e.path/'result.json',result);result['evidence']=e.finish(result['status']);write(ROOT/f'migration/reports/image-watershed-completion-{key}.json',result)
    record('IMG-02','完整Watershed合同 '+key+' 执行：'+result['status']+'，'+str(len(result['products']))+'件产品；输入身份、命令、库/设备记录及原始输出封存。',[result['evidence']]);print(result['status'],len(result['products']),result['evidence'])

def amd(mode):
    global ACTIVE
    p=inputs();bp=ROOT/'migration/reports/image-watershed-v2-build.json';build=json.loads(bp.read_text());binary=ROOT/build['binary']['path']
    if build['status']!='BUILT' or digest(binary)!=build['binary']['sha256'] or any(digest(ROOT/f)!=sha for f,sha in build['dependencies'].items()):raise ValueError('current complete GPU build required')
    e=Experiment('I3','watershed-complete-AMD-'+mode,'rocm',sources=[__file__,CONTRACT,FOLDER/'cases.txt',bp,binary,*[ROOT/f for f in build['dependencies']],*[ROOT/i['path'] for i in p['inputs']]]);ACTIVE=e;write(e.path/'backend.observed.json',capture())
    rc=e.command([str(binary),str(FOLDER),str(e.path/'outputs'),mode],'frozen-AMD-corpus',timeout=600);result=finish(e,rc,'AMD-'+mode);result['build_evidence']=build['evidence'];result['binary_sha256']=digest(binary);seal(e,result,'AMD-'+mode);return int(result['status']!='EXECUTED')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['native','amd']);p.add_argument('--plus',action='store_true');p.add_argument('--mode',default='padded',choices=['compact','padded','inplace','no-labels']);a=p.parse_args()
    try:rc=native(a.plus) if a.action=='native' else amd(a.mode)
    except Exception as error:
        if ACTIVE is not None and not ACTIVE.sealed:
            ref=ACTIVE.finish('RUNTIME_ERROR',reason=repr(error));record('IMG-02','Watershed完整合同执行异常已封存：'+repr(error),[ref])
        raise
    raise SystemExit(rc)
