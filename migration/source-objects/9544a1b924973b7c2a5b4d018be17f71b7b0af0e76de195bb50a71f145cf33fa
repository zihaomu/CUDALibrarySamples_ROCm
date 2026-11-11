#!/usr/bin/env python3
"""Read only byte-identical frozen distance inputs and their exact configurations."""
import json
from experiment import ROOT,digest

def load_case(case):
 directory=ROOT/case['fixture'];manifest=directory/'manifest.json'
 if digest(manifest)!=case['manifest_sha256']:raise ValueError('frozen input manifest identity')
 records=json.loads(manifest.read_text())['files']
 if set(records)!={'input.bin','config.json'}:raise ValueError('complete frozen input/config inventory')
 for name,row in records.items():
  path=directory/name
  if not path.is_file() or path.stat().st_size!=row['bytes'] or digest(path)!=row['sha256']:raise ValueError('frozen distance input/config bytes '+name)
 expected={k:case[k] for k in ['case','width','height','pitch','dtype','input_type','mode','cutoff','remap_circle']}
 if json.loads((directory/'config.json').read_text())!=expected or records['input.bin']['bytes']!=case['height']*case['pitch']:raise ValueError('frozen distance configuration/length')
 return (directory/'input.bin').read_bytes()
