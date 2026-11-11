#!/usr/bin/env python3
"""Attempt the byte-identical upstream Python script separately from the API oracle."""
import json,shlex
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def main():
 source=ROOT/'NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py';image=source.parent/'Teapot.jpg'
 e=Experiment('I1','NPP+/cannyEdgeDetectorPython::cannyEdgeDetector.py','cuda-original',sources=[__file__,source,image]);remote='/tmp/'+e.id
 sdk=next(s for s in json.loads((ROOT/'migration/reports/image-I0-native-private-SDKs.json').read_text()) if s['SDK']=='nppplus')
 prefix=sdk['remote']+'/libnpp_plus-linux-x86_64-'+sdk['identity']['version']+'_'+sdk['identity']['variant']+'-archive'
 rc=e.command(['ssh','nvidia-5090x2',shlex.join(['python3','-c','import torch,torchvision,cv2,pandas,tabulate; print(torch.__version__,torch.version.cuda,torchvision.__version__,cv2.__version__)'])],'actual-Python-environment',timeout=120)
 stage='Python-environment'
 if not rc:
  rc=e.command(['ssh','nvidia-5090x2',shlex.join(['mkdir','-p',remote])],'prepare-original-workdir')
  if not rc:rc=e.command(['scp',str(source),str(image),'nvidia-5090x2:'+remote+'/'],'copy-unmodified-script-and-image')
  if not rc:
   code='import pathlib,hashlib,os,subprocess,sys; p=pathlib.Path('+repr(remote)+'); assert hashlib.file_digest((p/"cannyEdgeDetector.py").open("rb"),"sha256").hexdigest()=='+repr(digest(source))+'; assert hashlib.file_digest((p/"Teapot.jpg").open("rb"),"sha256").hexdigest()=='+repr(digest(image))+'; env=dict(os.environ,CUDA_VISIBLE_DEVICES="1",LD_LIBRARY_PATH='+repr(prefix+'/lib')+'+":"+os.environ.get("LD_LIBRARY_PATH","")); sys.exit(subprocess.run([sys.executable,"cannyEdgeDetector.py"],cwd=p,env=env).returncode)'
   rc=e.command(['ssh','nvidia-5090x2',shlex.join(['python3','-c',code])],'actual-unmodified-8-size-1000-loop-script',timeout=1800);stage='unmodified-script'
   if not rc:rc=e.command(['scp','-r','nvidia-5090x2:'+remote+'/Teapot_resolutions',str(e.path/'outputs')],'collect-original-files')
 result=dict(status='EXECUTED' if rc==0 else 'BLOCKED' if stage=='Python-environment' else 'FAILED',return_code=rc,stage=stage,original_source_sha256=digest(source),original_image_sha256=digest(image),SDK=sdk['identity'],experiment_id=e.id)
 write(e.path/'result.json',result);result['evidence']=e.finish('EXECUTED' if not rc else 'ENV_BLOCKED' if stage=='Python-environment' else 'RUNTIME_ERROR');write(ROOT/'migration/reports/canny-plus-original-cuda.json',result)
 record('I1','原始CUDA Python脚本单列：'+result['status']+'（'+stage+'）；正确NppStreamContext的31组native API对照另行保留，不混作原脚本成功。',[result['evidence']]);print(result['status'],result['evidence'])
 return 0
if __name__=='__main__':raise SystemExit(main())
