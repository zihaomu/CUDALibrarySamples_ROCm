#!/usr/bin/env python3
from pathlib import Path
import os
from experiment import Experiment, ROOT

e = Experiment('P0', 'locked-environment', 'rocm', sources=[__file__, ROOT/'tools/moat/snapshot.py'])
output = e.path / 'backend.observed.json'
cmd = ['/home/zihaomu/zihaomu_workspace/rocm10-launch.sh', 'python',
       'tools/moat/snapshot.py', '--output', str(output)]
rc = e.command(cmd, 'preflight', timeout=120,
               env={'HIP_VISIBLE_DEVICES': os.environ.get('HIP_VISIBLE_DEVICES','2')})
print(e.finish('EXECUTED' if rc == 0 else 'ENV_BLOCKED', reason=None if rc == 0 else f'preflight exit {rc}'))
raise SystemExit(rc)
