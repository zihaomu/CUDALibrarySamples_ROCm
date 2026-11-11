#!/usr/bin/env python3
"""Install original benchmark dependencies without altering the foundation stack."""
from experiment import ROOT,Experiment,write
from snapshot import capture
from image_progress import record
def main():
 e=Experiment('I1','CannyPlus-private-Python-dependencies','rocm-setup',sources=[__file__,ROOT/'tools/migration/bootstrap_sdk.py']);write(e.path/'backend.observed.json',capture())
 packages=['opencv-python-headless==4.12.0.88','pandas==2.3.3','tabulate==0.9.0','python-dateutil==2.9.0.post0','pytz==2025.2','tzdata==2025.2','six==1.17.0']
 rc=e.command(['python3','tools/migration/bootstrap_sdk.py'],'create-project-SDK-overlay',timeout=300)
 if not rc:rc=e.command(['python3','-m','pip','install','--upgrade','--no-deps','--target',str(ROOT/'build/image-gpu-site'),*packages],'install-private-original-benchmark-packages',timeout=300)
 if not rc:rc=e.command(['env','PYTHONPATH='+str(ROOT/'build/image-gpu-site'),'python3','-c','import torch,torchvision,numpy,pandas,tabulate,cv2;assert torch.version.hip.startswith("7.16.");print(torch.__version__,torchvision.__version__,numpy.__version__,pandas.__version__,tabulate.__version__,cv2.__version__)'],'verify-pairing-and-actual-imports')
 ref=e.finish('EXECUTED' if not rc else 'ENV_BLOCKED');write(ROOT/'migration/reports/canny-plus-environment.json',dict(status='READY' if not rc else 'FAILED',evidence=ref,packages=packages));record('I1','原始benchmark的pandas/tabulate等依赖已在私有site安装/检查，基础Torch/NumPy不替换。',[ref]);return rc
if __name__=='__main__':raise SystemExit(main())
