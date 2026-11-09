#!/usr/bin/env python3
"""Map library names only when installed/project SDK headers expose the token.
This does not claim signature equivalence; independent compilation follows.
"""
import json,pathlib,re
from catalog import ROOT
routes={'cuTENSOR':('cutensor','hiptensor',ROOT/'build/deps/rocm-libraries/projects/hiptensor/library/include'),'nvCOMP':('nvcomp','hipcomp',ROOT/'build/deps/hipCOMP-core/include')}
report=[]
for family,(old,new,headers) in routes.items():
 corpus='\n'.join(p.read_text(errors='replace') for p in headers.rglob('*') if p.suffix in {'.h','.hpp','.inl'});tokens=set(re.findall(r'\b\w+\b',corpus))
 for p in (ROOT/'rocm/ported'/family).rglob('*'):
  if p.suffix not in {'.h','.hpp','.cu','.cpp','.cuh'}:continue
  s=p.read_text();mapped={}
  for t in set(re.findall(r'\b(?:'+old+'|'+old.upper()+r')\w*\b',s)):
   dst=t.replace(old,new,1) if t.startswith(old) else t.replace(old.upper(),new.upper(),1)
   if dst in tokens:mapped[t]=dst
  s=re.sub(r'\b(?:'+old+'|'+old.upper()+r')\w*\b',lambda m:mapped.get(m[0],m[0]),s)
  for q in re.findall(r'#include\s*[<"]([^">]+)[">]',s):
   dst=q.replace(old,new)
   if (headers/dst).exists():s=s.replace(q,dst)
  # Tensor datatype enums have a library-specific namespace rather than HIP's.
  if family=='cuTENSOR':
   s=s.replace('hipDataType_t','hiptensorDataType_t').replace('hipDataType','hiptensorDataType_t')
   for token in set(re.findall(r'\bHIP_[RC]_\w+\b',s)):
    dst=token.replace('HIP_','HIPTENSOR_',1)
    if dst in tokens:s=re.sub(r'\b'+token+r'\b',dst,s)
  if s!=p.read_text():p.write_text(s)
  report.append({'file':str(p.relative_to(ROOT)),'mapped':mapped,'header_root':str(headers.relative_to(ROOT))})
(ROOT/'migration/ecosystem-mappings.json').write_text(json.dumps(report,indent=2)+'\n');print('Reviewed mappings in',len(report),'files')
