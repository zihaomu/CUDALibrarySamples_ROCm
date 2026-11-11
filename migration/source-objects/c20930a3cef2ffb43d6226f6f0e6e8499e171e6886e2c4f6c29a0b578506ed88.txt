#!/usr/bin/env python3
"""Run the unchanged vendor EDT sample with binary/input/SDK/device receipts."""
import json,shlex,tarfile
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def main():
 source=ROOT/'NPP+/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp';assets=source.parent/'images';sdk=next(r for r in json.loads((ROOT/'migration/reports/image-I0-native-private-SDKs.json').read_text()) if r['SDK']=='nppplus');prefix=sdk['remote']+'/libnpp_plus-linux-x86_64-'+sdk['identity']['version']+'_'+sdk['identity']['variant']+'-archive';e=Experiment('I2','Distance-unchanged-CUDA-original-with-full-receipts','cuda-original',sources=[__file__,source,source.parent/'CMakeLists.txt',ROOT/'migration/reports/image-I0-native-private-SDKs.json',*sorted(assets.glob('*.raw'))]);remote='/tmp/'+e.id;bundle=e.path/'original.tar.gz'
 with tarfile.open(bundle,'w:gz') as tar:tar.add(source,arcname='source.cpp');tar.add(assets,arcname='images')
 jobs=[(['ssh','nvidia-5090x2',shlex.join(['mkdir','-p',remote+'/work'])],'prepare'),(['scp',str(bundle),'nvidia-5090x2:'+remote+'/original.tar.gz'],'upload-unchanged-source-and-all-assets'),(['ssh','nvidia-5090x2',shlex.join(['tar','-xzf',remote+'/original.tar.gz','-C',remote])],'unpack'),(['ssh','nvidia-5090x2',shlex.join(['/usr/local/cuda-13.4/bin/nvcc','-O2','-std=c++17','-arch=sm_120','-DNPP_PLUS_ENABLE','-I'+prefix+'/include',remote+'/source.cpp','-L'+prefix+'/lib','-Xlinker=-rpath','-Xlinker='+prefix+'/lib','-lnpp_plus_if','-lnpp_plus_c','-o',remote+'/distance'])],'compile-unmodified-vendor-original')];rc=0
 for command,phase in jobs:
  rc=e.command(command,phase,timeout=300)
  if rc:break
 config=dict(remote=remote,prefix=prefix,source_sha256=digest(source),inputs={p.name:digest(p) for p in sorted(assets.glob('*.raw'))})
 if not rc:
  code=r'''import hashlib,json,pathlib,subprocess,sys
c=json.loads(sys.argv[1]);root=pathlib.Path(c['remote']);sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert sha(root/'source.cpp')==c['source_sha256']
assert {p.name:sha(p) for p in (root/'images').glob('*.raw')}==c['inputs']
loader=subprocess.check_output(['ldd',str(root/'distance')],text=True);libraries={}
for line in loader.splitlines():
 if 'libnpp_plus_' in line and '=>' in line:
  p=pathlib.Path(line.split('=>',1)[1].split()[0]).resolve();libraries[str(p)]=dict(bytes=p.stat().st_size,sha256=sha(p))
device=subprocess.check_output(['nvidia-smi','-i','1','--query-gpu=name,uuid,pci.bus_id,driver_version','--format=csv,noheader'],text=True).strip()
print(json.dumps(dict(source_sha256=sha(root/'source.cpp'),binary_sha256=sha(root/'distance'),inputs=c['inputs'],libraries=libraries,loader=loader,physical_device_index=1,CUDA_VISIBLE_DEVICES='1',device=device)),flush=True)
sys.exit(subprocess.call([str(root/'distance')],cwd=root/'work'))
'''
  rc=e.command(['ssh','nvidia-5090x2',shlex.join(['env','CUDA_VISIBLE_DEVICES=1','python3','-c',code,json.dumps(config,separators=(',',':'))])],'actual-vendor-five-input-twelve-output-workflow-with-receipts',timeout=600)
 collect=e.command(['scp','-r','nvidia-5090x2:'+remote+'/images',str(e.path/'outputs')],'collect-all-original-input-and-output-bytes',timeout=180);r=dict(status='EXECUTED' if not rc and not collect else 'FAILED',return_code=rc,collection_return_code=collect,remote=remote,SDK=sdk['identity'],original_source=str(source.relative_to(ROOT)),original_source_sha256=digest(source),config=config,outputs=str((e.path/'outputs').relative_to(ROOT)),files={p.name:dict(bytes=p.stat().st_size,sha256=digest(p)) for p in (e.path/'outputs').glob('*') if p.is_file()},experiment_id=e.id);write(e.path/'run.json',r);r['evidence']=e.finish('OBSERVED' if not rc and not collect else 'NATIVE_HARNESS_NONZERO');write(ROOT/'migration/reports/image-distance-native.json',r);record('I2','NPP+未改完整EDT原例重新实测CUDA rc='+str(rc)+'，收集rc='+str(collect)+'；source/binary/全部输入/实际SDK loader和库SHA/GPU UUID-PCI-driver实际receipt与12输出保留，数学差异另验。',[r['evidence']]);print(r['status'],len(r['files']),r['evidence']);return int(bool(rc or collect))
if __name__=='__main__':raise SystemExit(main())
