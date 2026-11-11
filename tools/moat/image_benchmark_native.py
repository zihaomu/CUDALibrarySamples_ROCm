#!/usr/bin/env python3
"""Retry the unchanged CUDA benchmark using privately pinned CPU OpenCV."""
import json,shlex,tarfile
from experiment import ROOT,Experiment,write,digest
from image_progress import record
def main():
 dependency=json.loads((ROOT/'migration/reports/image-I3-native-OpenCV.json').read_text());assert dependency['status']=='READY';prefix=dependency['source']['prefix'];source=ROOT/'NPP/opencvBenchmark/opencvBenchmark.cpp';image=source.parent/'images/CircuitBoard_2048x1024_8u.raw';e=Experiment('I3','NPP-opencvBenchmark-full-native-default','cuda-original',sources=[__file__,source,image,ROOT/'migration/reports/image-I3-native-OpenCV.json']);remote='/tmp/'+e.id;bundle=e.path/'original.tar.gz'
 with tarfile.open(bundle,'w:gz') as t:t.add(source,arcname='source.cpp');t.add(image,arcname='images/'+image.name)
 def ssh(args,phase,timeout=300):return e.command(['ssh','nvidia-5090x2',shlex.join(args)],phase,timeout=timeout)
 rc=ssh(['mkdir','-p',remote+'/work'],'prepare-full-native-benchmark')
 if not rc:rc=e.command(['scp',str(bundle),'nvidia-5090x2:'+remote+'/original.tar.gz'],'upload-unchanged-source-and-original-image')
 if not rc:rc=ssh(['tar','-xzf',remote+'/original.tar.gz','-C',remote],'extract-full-original')
 if not rc:rc=ssh(['/usr/local/cuda-13.4/bin/nvcc','-O2','-std=c++17','-arch=sm_120','-I'+prefix+'/include/opencv4',remote+'/source.cpp','-L'+prefix+'/lib','-Xlinker=-rpath','-Xlinker='+prefix+'/lib','-lopencv_imgproc','-lopencv_core','-lnppif','-lnppig','-lnppicc','-lnppc','-o',remote+'/original'],'compile-unmodified-native-with-private-OpenCV')
 build_rc=rc;config=dict(remote=remote,source_sha256=digest(source),input_name=image.name,input_sha256=digest(image),OpenCV=dependency['receipt'])
 if not rc:
  code=r'''import hashlib,json,pathlib,subprocess,sys,os
c=json.loads(sys.argv[1]);root=pathlib.Path(c['remote']);sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();assert sha(root/'source.cpp')==c['source_sha256'] and sha(root/'images'/c['input_name'])==c['input_sha256'];prefix=pathlib.Path(c['OpenCV']['source']['prefix'])
for name,v in c['OpenCV']['files'].items():
 p=prefix/name;assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256']
loader=subprocess.check_output(['ldd',str(root/'original')],text=True);libraries={}
for line in loader.splitlines():
 if '=>' in line and any(s in line for s in ['libnpp','libopencv']):
  p=pathlib.Path(line.split('=>',1)[1].split()[0]).resolve();libraries[str(p)]=dict(bytes=p.stat().st_size,sha256=sha(p))
device=subprocess.check_output(['nvidia-smi','-i','1','--query-gpu=name,uuid,pci.bus_id,driver_version','--format=csv,noheader'],text=True).strip();print(json.dumps(dict(source_sha256=sha(root/'source.cpp'),input_sha256=sha(root/'images'/c['input_name']),binary_sha256=sha(root/'original'),libraries=libraries,loader=loader,physical_device_index=1,CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),device=device,OpenCV_source=c['OpenCV']['source'])),flush=True);sys.exit(subprocess.call([str(root/'original')],cwd=root/'work'))
'''
  rc=ssh(['env','CUDA_VISIBLE_DEVICES=1','python3','-c',code,json.dumps(config,separators=(',',':'))],'actual-4096x2048-four-operations-warmup-five-times-twenty-default-iterations',timeout=1200)
 out=e.path/'outputs';out.mkdir();collection=e.command(['scp','-r','nvidia-5090x2:'+remote+'/images','nvidia-5090x2:'+remote+'/work',str(out)],'collect-original-input-and-all-produced-files',timeout=180);r=dict(status='EXECUTED' if not rc and not collection else 'FAILED',source=str(source.relative_to(ROOT)),source_sha256=digest(source),build_return_code=build_rc,return_code=rc,collection_return_code=collection,remote=remote,config=config,outputs=str(out.relative_to(ROOT)),files={str(p.relative_to(out)):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in out.rglob('*') if p.is_file()},experiment_id=e.id);write(e.path/'run.json',r);r['evidence']=e.finish('OBSERVED' if r['status']=='EXECUTED' else 'NATIVE_BUILD_FAILED' if build_rc else 'NATIVE_HARNESS_NONZERO');write(ROOT/'migration/reports/image-I3-benchmark-native.json',r);record('I3','原生benchmark私有OpenCV补齐后完整默认原例：build='+str(build_rc)+'/run='+str(rc)+'/collection='+str(collection)+'；原4096x2048/四算子/预热/五轮20次、源码/输入/实际库/GPU收据和stdout保存，非AMD性能验收。',[r['evidence']]);print(r['status'],r['evidence']);return int(r['status']!='EXECUTED')
if __name__=='__main__':raise SystemExit(main())
