#!/usr/bin/env python3
"""Use the pinned MOAT state machine with this existing fork's branch."""
import importlib.util
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT.parent / 'MOAT_CUDALibrarySamples_ROCm'
lock_path=ROOT/'migration/moat/lock.json'
if lock_path.exists():
    lock=json.loads(lock_path.read_text());CONTROL=(ROOT/lock['control_checkout']).resolve()
    for name,key in [(lock['skill'],'skill_sha256'),('utils/moatlib.py','state_library_sha256')]:
        if hashlib.sha256((CONTROL/name).read_bytes()).hexdigest()!=lock[key]:
            raise RuntimeError('MOAT pinned source mismatch: '+name)
sys.path.insert(0, str(CONTROL/'utils'))
spec = importlib.util.spec_from_file_location('moatlib', CONTROL/'utils/moatlib.py')
moatlib = importlib.util.module_from_spec(spec)
sys.modules['moatlib'] = moatlib
spec.loader.exec_module(moatlib)
# Explicit adapter: the user adopted an existing fork and its rocm branch.
moatlib.PORT_BRANCH = 'rocm'
if __name__ == '__main__':
    raise SystemExit(moatlib.main())
