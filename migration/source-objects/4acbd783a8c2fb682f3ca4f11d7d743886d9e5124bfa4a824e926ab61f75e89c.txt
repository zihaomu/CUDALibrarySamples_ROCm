#!/usr/bin/env python3
"""Extend HIPIFY mappings only where the installed SDK declares the exact HIP token."""
import json,pathlib,re
from catalog import ROOT
inc=pathlib.Path('/opt/rocm/core-10.1/include');declared=set()
for family in ['hipblas','hipblaslt','hipsolver','hipsparse','hipfft','hiprand','hipsparselt']:
 for p in (inc/family).rglob('*.h'):declared.update(re.findall(r'\b(?:hip\w+|HIP\w+)\b',p.read_text(errors='replace')))
changes=[]
prefixes=[('cublasLt','hipblasLt'),('cublas','hipblas'),('cusolverDn','hipsolverDn'),('cusolver','hipsolver'),('cusparse','hipsparse'),('cufft','hipfft'),('curand','hiprand'),('CUBLASLT_','HIPBLASLT_'),('CUBLAS_','HIPBLAS_'),('CUSOLVER_','HIPSOLVER_'),('CUSPARSE_','HIPSPARSE_')]
for p in (ROOT/'rocm/ported').rglob('*'):
 if p.suffix not in {'.c','.cpp','.cu','.h','.hpp','.cuh','.hxx'}:continue
 before=p.read_text();s=before;applied={}
 for original in set(re.findall(r'\b(?:cublas\w*|cusolver\w*|cusparse\w*|CUBLAS\w*|CUSOLVER\w*|CUSPARSE\w*)\b',s)):
  for a,b in prefixes:
   if original.startswith(a):
    target=b+original[len(a):]
    if target in declared:s=re.sub(r'\b'+re.escape(original)+r'\b',target,s);applied[original]=target
    break
 if 'CUBLAS_GEMM_DEFAULT_TENSOR_OP' in s:
  s=s.replace('CUBLAS_GEMM_DEFAULT_TENSOR_OP','HIPBLAS_GEMM_DEFAULT');applied['CUBLAS_GEMM_DEFAULT_TENSOR_OP']='HIPBLAS_GEMM_DEFAULT (backend algorithm preference; no instruction-level parity claim)'
 if s!=before:p.write_text(s);changes.append({'source':str(p.relative_to(ROOT)),'mappings':applied})
(ROOT/'migration/api-mapping-extensions.json').write_text(json.dumps(changes,indent=2)+'\n');print('Patched files:',len(changes))
