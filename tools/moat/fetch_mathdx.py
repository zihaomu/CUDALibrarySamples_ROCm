#!/usr/bin/env python3
import shlex
from pathlib import Path
from experiment import Experiment,ROOT,write
e=Experiment('R2','MathDx-26.06.1-CUDA13-SDK','cuda-sdk',sources=[Path(__file__)])
remote='/tmp/'+e.id;host='nvidia-5090x2';url='https://developer.nvidia.com/downloads/compute/cuSOLVERDx/redist/cuSOLVERDx/cuda13/nvidia-mathdx-26.06.1-cuda13.tar.gz'
commands=[(['mkdir','-p',remote],'prepare'),(['curl','-L','--fail','--max-time','180','-o',remote+'/sdk.tar.gz',url],'download'),(['sha256sum',remote+'/sdk.tar.gz'],'archive-sha256'),(['python3','-c','import tarfile,sys;t=tarfile.open(sys.argv[1]);t.extractall(sys.argv[2],filter="data");print("\\n".join(t.getnames()[:20]))',remote+'/sdk.tar.gz',remote+'/sdk'],'extract')]
rc=0
for cmd,phase in commands:
 rc=e.command(['ssh',host,shlex.join(cmd)],phase,timeout=200)
 if rc:break
evidence=e.finish('EXECUTED' if rc==0 else 'SDK_UNAVAILABLE',reason=None if rc==0 else f'{phase} exit {rc}')
write(ROOT/'migration/reports/rewrite-mathdx-sdk.json',dict(return_code=rc,remote=remote,evidence=evidence,url=url));print(evidence)
