#!/usr/bin/env python3
"""Run the independent batch10 CPU oracle in its pinned Python environment."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/migration'))
import batch10_reference as reference

p = argparse.ArgumentParser()
p.add_argument('--source', required=True)
p.add_argument('--case', required=True)
p.add_argument('--folder', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
try:
    result = reference.validate(a.source, a.case, a.folder)
except Exception as error:
    result = dict(status='FAILED', checks=[], error=repr(error))
a.out.write_text(json.dumps(result, indent=2) + '\n')
print(a.source, a.case, result['status'])
raise SystemExit(int(result['status'] != 'PASSED'))
