#!/usr/bin/env python3
"""Install a pinned private CPU OpenCV core/imgproc for the unchanged CUDA benchmark."""
import json,shlex
from experiment import ROOT,Experiment,write
from image_progress import record
def main():
 e=Experiment('I3','OpenCV-private-native-core-imgproc-dependency','CPU-native-setup',sources=[__file__,ROOT/'NPP/opencvBenchmark/opencvBenchmark.cpp']);url='https://github.com/opencv/opencv.git';rc=e.command(['git','ls-remote',url,'refs/tags/4.12.0','refs/tags/4.12.0^{}'],'resolve-pinned-official-OpenCV-tag',timeout=120);lock=None
 if not rc:
  lines=(e.path/e.commands[-1]['stdout']).read_text().splitlines();refs={line.split()[1]:line.split()[0] for line in lines};sha=refs.get('refs/tags/4.12.0^{}',refs['refs/tags/4.12.0']);lock=dict(url=url,tag='4.12.0',commit=sha,prefix='/tmp/image-library-private-OpenCV/opencv-4.12.0-'+sha[:12]);write(e.path/'source-lock.json',lock)
  code=r'''import hashlib,json,pathlib,subprocess,sys
c=json.loads(sys.argv[1]);prefix=pathlib.Path(c['prefix']);source=pathlib.Path(str(prefix)+'-source');build=pathlib.Path(str(prefix)+'-build')
def run(args):subprocess.run(args,check=True)
if not source.exists():run(['git','clone','--depth','1','--branch',c['tag'],c['url'],str(source)])
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==c['commit']
run(['git','-C',str(source),'diff','--exit-code'])
flags=['-DCMAKE_BUILD_TYPE=Release','-DCMAKE_INSTALL_PREFIX='+str(prefix),'-DBUILD_LIST=core,imgproc','-DBUILD_TESTS=OFF','-DBUILD_PERF_TESTS=OFF','-DBUILD_EXAMPLES=OFF','-DBUILD_opencv_python2=OFF','-DBUILD_opencv_python3=OFF','-DBUILD_JAVA=OFF','-DOPENCV_GENERATE_PKGCONFIG=ON','-DBUILD_SHARED_LIBS=ON','-DWITH_IPP=OFF','-DWITH_OPENCL=OFF','-DWITH_CUDA=OFF','-DWITH_TBB=OFF','-DWITH_OPENMP=ON']
manifest=prefix/'project-dependency.json'
if manifest.exists():
 old=json.loads(manifest.read_text());assert old['source']==c and old['flags']==flags
else:
 run(['cmake','-S',str(source),'-B',str(build),*flags]);run(['cmake','--build',str(build),'--parallel','8']);run(['cmake','--install',str(build)])
files={str(p.relative_to(prefix)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for parent in ['lib','include','share'] for p in sorted((prefix/parent).rglob('*')) if p.is_file()}
if manifest.exists():assert files==old['files']
result=dict(source=c,flags=flags,files=files,compiler=subprocess.check_output(['c++','--version'],text=True),pkg_config=subprocess.check_output(['pkg-config','--cflags','--libs',str(prefix/'lib/pkgconfig/opencv4.pc')],text=True).strip());manifest.write_text(json.dumps(result,indent=2)+'\n');print('OPENCV_RECEIPT='+json.dumps(result),flush=True)
'''
  rc=e.command(['ssh','nvidia-5090x2',shlex.join(['python3','-c',code,json.dumps(lock,separators=(',',':'))])],'build-private-pinned-CPU-OpenCV-no-system-SDK-changes',timeout=1800)
 receipt=None
 if not rc:
  receipt=json.loads(next(line.removeprefix('OPENCV_RECEIPT=') for line in (e.path/e.commands[-1]['stdout']).read_text().splitlines() if line.startswith('OPENCV_RECEIPT=')))
 v=dict(status='READY' if not rc else 'ENV_BLOCKED',return_code=rc,source=lock,receipt=receipt);write(e.path/'environment.json',v);v['evidence']=e.finish('EXECUTED' if not rc else 'ENV_BLOCKED');write(ROOT/'migration/reports/image-I3-native-OpenCV.json',v);record('I3','5090原例benchmark缺OpenCV C++开发环境，私有固定4.12.0/core+imgproc独立CPU依赖构建：'+v['status']+'；不改系统CUDA/全局SDK，无GPU支持计数。',[v['evidence']]);print(v['status'],v['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
