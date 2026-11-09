#!/usr/bin/env python3
"""Add lossless host-result observation to copies of original BLAS examples.
This adds output only; it does not change their mathematical calls or inputs.
"""
import argparse,pathlib,re,subprocess
from catalog import ROOT,BASE
parser=argparse.ArgumentParser();parser.add_argument('--family',default='cuBLAS');args=parser.parse_args();family=args.family;names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines();count=0
for name in names:
 if not name.startswith(family+'/') or pathlib.Path(name).suffix not in {'.cu','.cpp'}:continue
 original=(ROOT/name).read_text()
 if not re.search(r'\bint\s+main\s*\(',original):continue
 for base in [ROOT/'rocm/ported',ROOT/'build/cuda-observed']:
  p=base/name
  if not p.exists():
   if 'cuda-observed' in str(base):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(original)
   else:continue
  s=p.read_text()
  if 'MIGRATION_OBSERVE_ORIGINAL' in s:continue
  variables=re.findall(r'(?:const\s+)?std::vector<\s*(?:data_type|double|float|int|cu\w*Complex|hip\w*Complex)\s*>\s+(\w+)',s[s.find('int main'):])
  i=s.find('/* free resources */')
  if i<0:continue
  calls='\n// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.\n'+''.join(f'migration_observer::emit("{v}",{v}.data(),{v}.size());\n' for v in dict.fromkeys(variables))
  s=s[:i]+calls+s[i:];s='#include "observe.hpp"\n'+s;p.write_text(s);count+=1
print('Instrumented original-profile files:',count)
