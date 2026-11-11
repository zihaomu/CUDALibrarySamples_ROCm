#!/usr/bin/env python3
"""Verify every frozen RGB byte, including row padding and mode parameters."""
import json
from experiment import ROOT,digest
def load_case(case):
 d=ROOT/case['fixture']
 if digest(d/'manifest.json')!=case['manifest_sha256']:raise ValueError('frozen flood manifest')
 files=json.loads((d/'manifest.json').read_text())['files']
 if set(files)!={'input.bin','config.json'}:raise ValueError('exact flood input inventory')
 for name,v in files.items():
  p=d/name
  if p.stat().st_size!=v['bytes'] or digest(p)!=v['sha256']:raise ValueError('frozen input/config bytes '+name)
 keys=['case','width','height','pitch','mode','seed','lower','upper','fill','boundary']
 if json.loads((d/'config.json').read_text())!={k:case[k] for k in keys} or files['input.bin']['bytes']!=case['height']*case['pitch']:raise ValueError('frozen flood geometry and parameters')
 return (d/'input.bin').read_bytes()
