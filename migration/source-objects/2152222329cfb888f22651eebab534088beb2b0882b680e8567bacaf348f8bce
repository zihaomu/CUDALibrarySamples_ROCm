#!/usr/bin/env python3
"""Add only private OpenCV bindings while retaining the foundation Torch stack."""
import json
from experiment import ROOT,Experiment,write
from image_progress import record
from snapshot import capture

def main():
 e=Experiment('I0','image-private-GPU-Python-dependency','rocm-build',sources=[__file__]);write(e.path/'backend.observed.json',capture());target=ROOT/'build/image-gpu-site';rc=e.command(['python3','-m','pip','install','--no-deps','--target',str(target),'opencv-python-headless==4.12.0.88'],'private-cv2-wheel-no-foundation-dependency-changes',timeout=300)
 code='import torch,torchvision,numpy,cv2,json;print(json.dumps(dict(torch=torch.__version__,hip=torch.version.hip,numpy=numpy.__version__,cv2=cv2.__version__,cv2_file=cv2.__file__)));assert torch.version.hip.startswith("7.16.");assert cv2.Canny(numpy.zeros((8,8),numpy.uint8),50,100).shape==(8,8)'
 rc=rc or e.command(['env','PYTHONPATH='+str(target),'python3','-c',code],'actual-private-import-and-Torch-pairing');v=dict(status='PASSED' if rc==0 else 'FAILED',checks=[dict(check='cv2-import-and-original-ROCm-Torch-pair-retained',passed=rc==0)]);ref=e.finish('PASSED' if rc==0 else 'ENV_BLOCKED',v);write(ROOT/'migration/reports/image-I0-GPU-Python.json',dict(**v,site=str(target.relative_to(ROOT)),evidence=ref));record('I0','ROCm Python私有cv2绑定安装与实际导入已记录；使用--no-deps保留原Torch/torchvision/NumPy配对，不把CPU Canny测试视作GPU成功。',[ref]);print(rc,ref)
if __name__=='__main__':main()
