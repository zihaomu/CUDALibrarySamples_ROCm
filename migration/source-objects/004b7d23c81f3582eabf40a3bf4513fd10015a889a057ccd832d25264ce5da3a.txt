#!/usr/bin/env python3
"""Create CUDA validation drivers from explicit HIP API ports.
These are shared-fixture comparators, not the unchanged upstream CUDA baseline.
"""
import pathlib,re,json
ROOT=pathlib.Path(__file__).resolve().parents[2]
headers={'hip/hip_runtime.h':'cuda_runtime.h','hipblas/hipblas.h':'cublas_v2.h','hipblaslt/hipblaslt.h':'cublasLt.h','hipsolver/hipsolver.h':'cusolverDn.h','hipsparse/hipsparse.h':'cusparse.h','hipfft/hipfft.h':'cufft.h','hiprand/hiprand.h':'curand.h'}
def convert(s):
 for a,b in headers.items():s=s.replace(a,b)
 for a,b in [('hipblasLt','cublasLt'),('hipblas','cublas'),('hipsolver','cusolver'),('hipsparse','cusparse'),('hipfft','cufft'),('hiprand','curand'),('HIPBLASLT','CUBLASLT'),('HIPBLAS','CUBLAS'),('HIPSPARSE','CUSPARSE'),('HIPFFT','CUFFT'),('HIPRAND','CURAND'),('HIP_R_','CUDA_R_')]:s=s.replace(a,b)
 s=re.sub(r'\bhip([A-Z]\w*)',r'cuda\1',s)
 s=s.replace('HIP implementation','CUDA validation implementation')
 return s.replace('CUFFT_BACKWARD','CUFFT_INVERSE')
overrides={v['path']+'/sample.cpp':v['cuda_reference_source'] for v in json.loads((ROOT/'migration/m1.json').read_text()) if v.get('cuda_reference_source')}
for p in (ROOT/'rocm').rglob('*'):
 if p.name not in {'sample.cpp','check.hpp','scaling.hpp','scaling.hip'}:continue
 q=ROOT/'build/cuda-validation'/p.relative_to(ROOT/'rocm');q=q.with_suffix('.cu') if p.suffix=='.hip' else q;q.parent.mkdir(parents=True,exist_ok=True);q.write_text((ROOT/overrides[str(p.relative_to(ROOT/'rocm'))]).read_text() if str(p.relative_to(ROOT/'rocm')) in overrides else convert(p.read_text()))
bench=ROOT/'rocm/bench/gemm.cpp'
if bench.exists():
 q=ROOT/'build/cuda-validation/bench/gemm.cpp';q.parent.mkdir(parents=True,exist_ok=True);q.write_text(convert(bench.read_text()))
print('CUDA shared-fixture comparators prepared')
