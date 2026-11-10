#!/usr/bin/env python3
"""Restore the pinned local control checkout without writing to public remotes."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
lock=json.loads((ROOT/'migration/moat/lock.json').read_text());control=(ROOT/lock['control_checkout']).resolve()
def run(argv,cwd=None):subprocess.run(list(map(str,argv)),cwd=cwd,check=True)
if not control.exists():
 run(['git','clone','--no-checkout',lock['upstream_url'],control]);run(['git','remote','rename','origin','upstream'],control)
 bundle=ROOT/'migration/moat/control.bundle'
 if bundle.exists():
  run(['git','fetch',bundle,'port/CUDALibrarySamples_ROCm:refs/heads/port/CUDALibrarySamples_ROCm'],control)
  run(['git','checkout','port/CUDALibrarySamples_ROCm'],control)
 else:raise SystemExit('Missing saved project control bundle; refusing to invent project state')
 run(['git','init','--bare','.git/project-sync.git'],control)
 run(['git','remote','add','origin','.git/project-sync.git'],control)
 run(['git','push','-u','origin','port/CUDALibrarySamples_ROCm'],control)
 run(['git','push','origin',lock['upstream_commit']+':refs/heads/main'],control)
 run(['bash','utils/setup_git.sh'],control)
 src=control/'projects'/lock['project']/'src'
 if not src.exists():src.symlink_to(ROOT,target_is_directory=True)
for path,key in [(lock['skill'],'skill_sha256'),('utils/moatlib.py','state_library_sha256')]:
 if hashlib.sha256((control/path).read_bytes()).hexdigest()!=lock[key]:raise SystemExit('Pinned source mismatch: '+path)
run(['git','merge-base','--is-ancestor',lock['upstream_commit'],'HEAD'],control)
print('Verified pinned MOAT control checkout:',control)
