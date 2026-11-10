#!/usr/bin/env python3
import json
from pathlib import Path
import shlex
from experiment import Experiment,ROOT,write
e=Experiment('R1','native-COL4_4R2_8C-transform','cuda_native',sources=[ROOT/'tools/moat/native_packing.cu'])
host='nvidia-5090x2';remote='/tmp/'+e.id
commands=[(['ssh',host,shlex.join(['mkdir','-p',remote])],'prepare'),
          (['scp',str(ROOT/'tools/moat/native_packing.cu'),host+':'+remote+'/probe.cu'],'upload'),
          (['ssh',host,shlex.join(['/usr/local/cuda-13.4/bin/nvcc',remote+'/probe.cu','-o',remote+'/probe','-lcublasLt','-lcublas','-arch=sm_120'])],'build'),
          (['ssh',host,remote+'/probe'],'native-transform')]
for cmd,phase in commands:
    rc=e.command(cmd,phase,timeout=180)
    if rc:
        print(e.finish('COMMAND_FAILED',reason=f'{phase} exit {rc}'));raise SystemExit(rc)
r=json.loads((e.path/e.commands[-1]['stdout']).read_text())
checks=[dict(check='native-map-is-bijection',passed=sorted(r['map'])==list(range(256)))]
write(ROOT/'migration/rewrite/native-col4-map.json',dict(**r,experiment_id=e.id))
print(e.finish('PASSED',dict(status='PASSED',checks=checks)))
