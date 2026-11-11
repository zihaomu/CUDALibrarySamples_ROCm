#!/usr/bin/env python3
"""Attempt unchanged original language workflows; keep API counterpart distinct."""
import json,shlex,tarfile
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def main():
 cpp=ROOT/'NPP/nppCanny/npp_canny_simple.cpp';py=cpp.with_suffix('.py');image=ROOT/'NPP+/cannyEdgeDetectorPython/Teapot.jpg';sdkfile=ROOT/'build/image-opencv/manifest.json'
 e=Experiment('I1','NPP/nppCanny::npp_canny_simple.cpp','cuda-original',sources=[__file__,cpp,image,sdkfile]);remote='/tmp/'+e.id;bundle=e.path/'source-and-OpenCV.tar.gz'
 with tarfile.open(bundle,'w:gz') as tar:
  tar.add(cpp,arcname='original.cpp');tar.add(image,arcname='image.jpg');tar.add(ROOT/'build/image-opencv',arcname='opencv')
 rc=e.command(['ssh','nvidia-5090x2',shlex.join(['mkdir','-p',remote+'/outputs'])],'prepare-original-workflow');rc=rc or e.command(['scp',str(bundle),'nvidia-5090x2:'+remote+'/source.tar.gz'],'upload-private-CPU-SDK-and-original');rc=rc or e.command(['ssh','nvidia-5090x2',shlex.join(['tar','-xzf',remote+'/source.tar.gz','-C',remote])],'extract-original')
 if not rc:
  code='''import pathlib,json,hashlib,sys
p=pathlib.Path(sys.argv[1]);manifest=json.loads((p/'opencv/manifest.json').read_text())
assert hashlib.file_digest((p/'original.cpp').open('rb'),'sha256').hexdigest()==sys.argv[2]
for n,v in manifest['headers'].items():assert hashlib.file_digest((p/'opencv'/n).open('rb'),'sha256').hexdigest()==v['sha256']
for n,v in manifest['libraries'].items():assert hashlib.file_digest((p/'opencv/lib'/n).open('rb'),'sha256').hexdigest()==v['sha256']
print(json.dumps(dict(original_source_sha256=sys.argv[2],OpenCV_manifest_sha256=hashlib.file_digest((p/'opencv/manifest.json').open('rb'),'sha256').hexdigest())))
'''
  rc=e.command(['ssh','nvidia-5090x2',shlex.join(['python3','-c',code,remote,digest(cpp)])],'verify-unmodified-source-and-actual-OpenCV-identities')
 if not rc:
  cmd=['/usr/local/cuda-13.4/bin/nvcc','-std=c++17','-O2','-arch=sm_120','-I'+remote+'/opencv/include/opencv4',remote+'/original.cpp','-L'+remote+'/opencv/lib','-Xlinker','-rpath','-Xlinker',remote+'/opencv/lib','-lopencv_imgcodecs','-lopencv_imgproc','-lopencv_core','-lnppif','-lnppc','-o',remote+'/original']
  rc=e.command(['ssh','nvidia-5090x2',shlex.join(cmd)],'build-unmodified-original-C++',timeout=300)
 binary_sha=None
 if not rc:
  rc=e.command(['ssh','nvidia-5090x2',shlex.join(['sha256sum',remote+'/original'])],'actual-original-binary-sha256');binary_sha=(e.path/'logs/0006-actual-original-binary-sha256.stdout.log').read_text().split()[0] if not rc else None
 if not rc:
  code='''import pathlib,hashlib,subprocess,os,sys
p=pathlib.Path(sys.argv[1]);binary=p/'original';assert hashlib.file_digest(binary.open('rb'),'sha256').hexdigest()==sys.argv[2]
sys.exit(subprocess.run([str(binary),str(p/'image.jpg')],cwd=p/'outputs',env=dict(os.environ,CUDA_VISIBLE_DEVICES='1',LD_LIBRARY_PATH=str(p/'opencv/lib')+':'+os.environ.get('LD_LIBRARY_PATH',''))).returncode)
'''
  rc=e.command(['ssh','nvidia-5090x2',shlex.join(['python3','-c',code,remote,binary_sha])],'actual-unmodified-original-file-benchmark',timeout=300)
 if not rc:
  (e.path/'outputs').mkdir();rc=e.command(['scp','-r','nvidia-5090x2:'+remote+'/outputs/.',str(e.path/'outputs')],'collect-three-original-PNGs')
 result=dict(status='EXECUTED' if not rc else 'FAILED',return_code=rc,experiment_id=e.id,original_source_sha256=digest(cpp),binary_sha256=binary_sha,SDK_manifest_sha256=digest(sdkfile),outputs=str((e.path/'outputs').relative_to(ROOT)));write(e.path/'result.json',result);result['evidence']=e.finish('EXECUTED' if not rc else 'NATIVE_MISMATCH');write(ROOT/'migration/reports/canny-color-original-cuda-cpp.json',result);record('I1','未改原始CUDA C++三图像/benchmark流程：'+result['status']+'；与项目经典变体和native API counterpart分别记录。',[result['evidence']]);print('cpp',rc,flush=True)
 p=Experiment('I1','NPP/nppCanny::npp_canny_simple.py','cuda-original',sources=[__file__,py]);prc=p.command(['ssh','nvidia-5090x2',shlex.join(['python3','-c','import torch,cv2;print(torch.__version__,torch.version.cuda,cv2.__version__)'])],'original-Python-toolchain-inventory',timeout=120);res=dict(status='READY' if not prc else 'BLOCKED',return_code=prc,original_source_sha256=digest(py),scope='Original Python dependency inventory; native NPP C3 API counterpart separately verified.');write(p.path/'result.json',res);res['evidence']=p.finish('OBSERVED' if not prc else 'ENV_BLOCKED');write(ROOT/'migration/reports/canny-color-original-cuda-python.json',res);record('I1','原CUDA Python依赖检查：'+res['status']+'；AMD完整Python入口独立验收，原始依赖缺口不改写成CUDA成功。',[res['evidence']]);print('python',prc)
 return 0
if __name__=='__main__':raise SystemExit(main())
