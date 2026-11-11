#!/usr/bin/env python3
"""Run all five unchanged I3 originals with full source/input/loader/device receipts."""
import json,shlex,tarfile
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_progress import record
SDK='/usr/local/cuda-13.4'
PLUS='/tmp/image-library-private-SDKs/nppplus-0.10.0.0/libnpp_plus-linux-x86_64-0.10.0.0_cuda12-archive'
CASES=[
 ('NPP/watershedSegmentation/watershedSegmentation.cpp', ['Lena_512x512_8u_Gray.raw','CT_skull_512x512_8u_Gray.raw','Rocks_512x512_8u_Gray.raw','coins_500x383_8u_Gray.raw','coins_overlay_500x569_8u_Gray.raw']),
 ('NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp',['CT_skull_512x512_8u_Gray.raw','Rocks_512x512_8u_Gray.raw','Corn_614x461_8u_Gray.raw']),
 ('NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp',['RainbowChart_RGB_C3_1024x445_8u.raw','SeabedSampler_RGB_C3_675x1024_8u.raw']),
 ('NPP/houghLines/houghLines.cpp',[]),
 ('NPP/opencvBenchmark/opencvBenchmark.cpp',['CircuitBoard_2048x1024_8u.raw'])]
def ssh(e,args,phase,timeout=300):return e.command(['ssh','nvidia-5090x2',shlex.join(args)],phase,timeout=timeout)
def main():
 rows=[]
 for source,inputs in CASES:
  p=ROOT/source;headers=sorted(p.parent.glob('*.h'));assets=[p.parent/'images'/n for n in inputs];e=Experiment('I3',source.replace('/', '::',1),'cuda-original',sources=[__file__,p,*headers,*assets,ROOT/'migration/reports/image-I0-native-private-SDKs.json']);remote='/tmp/'+e.id;bundle=e.path/'original.tar.gz'
  with tarfile.open(bundle,'w:gz') as tar:
   tar.add(p,arcname=p.name)
   for header in headers:tar.add(header,arcname=header.name)
   for asset in assets:tar.add(asset,arcname='images/'+asset.name)
  rc=ssh(e,['mkdir','-p',remote+'/work',remote+'/images'],'prepare-private-full-original')
  if not rc:rc=e.command(['scp',str(bundle),'nvidia-5090x2:'+remote+'/original.tar.gz'],'upload-unmodified-sources-and-exact-inputs')
  if not rc:rc=ssh(e,['tar','-xzf',remote+'/original.tar.gz','-C',remote],'extract-private-original')
  cv=[]
  if not rc and 'opencvBenchmark' in source:
   rc=ssh(e,['pkg-config','--cflags','--libs','opencv4'],'actual-native-OpenCV-build-dependency')
   if not rc:cv=shlex.split((e.path/e.commands[-1]['stdout']).read_text())
  flags=[SDK+'/bin/nvcc','-O2','-std=c++17','-arch=sm_120']
  if source.startswith('NPP+/'):flags+=['-DNPP_PLUS_ENABLE','-I'+PLUS+'/include','-L'+PLUS+'/lib','-Xlinker=-rpath','-Xlinker='+PLUS+'/lib','-lnpp_plus_if','-lnpp_plus_c']
  else:flags+=['-lnppif','-lnppig','-lnppicc','-lnppc']
  if not rc:rc=ssh(e,[*flags,remote+'/'+p.name,*cv,'-o',remote+'/original'],'compile-complete-unmodified-original')
  build_rc=rc;config=dict(remote=remote,source=p.name,source_sha256=digest(p),headers={p.name:digest(p) for p in headers},inputs={p.name:digest(p) for p in assets})
  if not rc:
   code=r'''import hashlib,json,pathlib,subprocess,sys,os
c=json.loads(sys.argv[1]);root=pathlib.Path(c['remote']);sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert sha(root/c['source'])==c['source_sha256']
assert {n:sha(root/n) for n in c['headers']}==c['headers']
assert {p.name:sha(p) for p in (root/'images').iterdir()}==c['inputs']
loader=subprocess.check_output(['ldd',str(root/'original')],text=True);libraries={}
for line in loader.splitlines():
 if '=>' in line and any(n in line for n in ['libnpp','libopencv']):
  p=pathlib.Path(line.split('=>',1)[1].split()[0]).resolve();libraries[str(p)]=dict(bytes=p.stat().st_size,sha256=sha(p))
device=subprocess.check_output(['nvidia-smi','-i','1','--query-gpu=name,uuid,pci.bus_id,driver_version','--format=csv,noheader'],text=True).strip()
print(json.dumps(dict(source_sha256=sha(root/c['source']),headers=c['headers'],inputs=c['inputs'],binary_sha256=sha(root/'original'),libraries=libraries,loader=loader,physical_device_index=1,CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),device=device)),flush=True)
sys.exit(subprocess.call([str(root/'original')],cwd=root/'work'))
'''
   rc=ssh(e,['env','CUDA_VISIBLE_DEVICES=1','python3','-c',code,json.dumps(config,separators=(',',':'))],'actual-complete-native-default-with-source-input-library-GPU-receipt',timeout=900)
  out=e.path/'outputs';out.mkdir();collection=e.command(['scp','-r','nvidia-5090x2:'+remote+'/images','nvidia-5090x2:'+remote+'/work',str(out)],'collect-all-inputs-products-and-original-workflow-files',timeout=180);r=dict(status='EXECUTED' if not rc and not collection else 'FAILED',source=source,source_sha256=digest(p),build_return_code=build_rc,return_code=rc,collection_return_code=collection,config=config,remote=remote,outputs=str(out.relative_to(ROOT)),files={str(x.relative_to(out)):dict(bytes=x.stat().st_size,sha256=digest(x)) for x in sorted(out.rglob('*')) if x.is_file()},experiment_id=e.id);write(e.path/'run.json',r);r['evidence']=e.finish('OBSERVED' if r['status']=='EXECUTED' else 'NATIVE_BUILD_FAILED' if build_rc else 'NATIVE_HARNESS_NONZERO');rows.append(r);write(ROOT/'migration/reports/image-I3-native-originals.json',rows);record('I3',source+'未改CUDA原始完整默认流程：build='+str(build_rc)+'/run='+str(rc)+'/collection='+str(collection)+'；完整source/header/input/binary/实际库/GPU receipt及所有产品文件保留，CPU/AMD比较另验。',[r['evidence']]);print(source,r['status'],len(r['files']),flush=True)
 return int(any(r['status']!='EXECUTED' for r in rows))
if __name__=='__main__':raise SystemExit(main())
