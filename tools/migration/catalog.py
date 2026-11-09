#!/usr/bin/env python3
"""Inventory the immutable upstream tree; JSON serialization is valid YAML 1.2.

Entrypoint discovery is deliberately provisional: build graph audit remains explicit.
Never turn discovery or an executable exit status into a correctness result.
"""
import argparse, ast, collections, hashlib, json, pathlib, re, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = '8b0573b11d183d9b3a36cd2955aa31c16cc61b95'
CANDIDATES = {
'cuBLAS':['hipBLAS','rocBLAS'],'cuBLASLt':['hipBLASLt'],'cuBLASMp':['rocBLAS','RCCL','MPI'],
'cuDSS':['rocSOLVER (limited refactorization subset; full solver unresolved)'],'cuEST':['unresolved'],
'cuFFT':['hipFFT','rocFFT'],'cuFFTMp':['hipFFT','rocFFT','GPU-aware MPI'],'cuPQC':['unresolved'],
'cuRAND':['hipRAND','rocRAND'],'cuSOLVER':['hipSOLVER','rocSOLVER'],'cuSOLVERMp':['rocSOLVER','rocBLAS','MPI','RCCL'],
'cuSOLVERSp2cuDSS':['hipSOLVER','rocSOLVER (subset)'],'cuSPARSE':['hipSPARSE','rocSPARSE'],'cuSPARSELt':['hipSPARSELt'],
'cuTENSOR':['hipTensor'],'cuTENSORMg':['hipTensor','RCCL','MPI'],'cuTENSORMp':['hipTensor','MPI','RCCL'],
'MathDx/cuBLASDx':['rocWMMA','Composable Kernel'],'MathDx/cuFFTDx':['unresolved device FFT'],
'MathDx/cuRANDDx':['rocRAND device API'],'MathDx/cuSolverDx':['unresolved device solver'],
'MathDx/libmathdx':['HIPRTC + device algorithms'],'MathDx/nvCOMPDx':['hipCOMP algorithm reuse (device API unresolved)'],
'NPP':['RPP HIP','rocPRIM'],'NPP+':['RPP HIP','rocPRIM'],'nvJPEG':['rocJPEG (decode only)','RPP'],
'nvJPEG2000':['unresolved'],'nvTIFF':['unresolved'],'nvCOMP':['hipCOMP'],'nvMatmulHeuristics':['hipBLASLt heuristics (subset)']}
CANDIDATES['cuTENSOR']=['hipTensor','rocBLAS + HIP permutations']
CANDIDATES['cuFFT']=['hipFFT','rocFFT','RCCL + HIP (distributed alternative)']
CANDIDATES['cuDSS']=['rocSOLVER CSRRF','rocSPARSE/HIP','ISO_C_BINDING']
CANDIDATES['cuPQC']=['custom HIP SHA2/SHA3','unresolved post-quantum device APIs']
M1_DIRS=['cuBLAS/Level-1/axpy','cuBLAS/Level-1/dot','cuBLAS/Level-2/gemv','cuBLAS/Level-3/gemm','cuBLAS/Level-3/gemmStridedBatched','cuBLAS/Extensions/GemmEx','cuBLASLt/LtSgemm','cuSPARSE/spmv_csr','cuSPARSE/spmm_csr','cuSPARSE/spsv_csr','cuSOLVER/getrf','cuSOLVER/potrfBatched','cuFFT/1d_c2c','cuFFT/1d_r2c_c2r']
M1_FILES=['cuRAND/Host/philox/curand_philox_uniform_example.cpp','cuRAND/Host/philox/curand_philox_normal_example.cpp']

def main():
 oldpath=ROOT/'migration/samples.yaml'
 if oldpath.exists():
  print('Existing catalog preserved; use audit_builds.py to refresh build bindings without losing discovered entries/history.');return
 old=json.loads(oldpath.read_text()) if oldpath.exists() else {}
 previous={s['id']:s for s in old.get('samples',[])}
 names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines()
 sources=[]; samples=[]; builds=[]
 for name in names:
  p=ROOT/name; family='/'.join(p.relative_to(ROOT).parts[:2]) if name.startswith('MathDx/') else name.split('/')[0]
  if p.name=='CMakeLists.txt' or 'makefile' in p.name.lower(): builds.append({'path':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'audit':'PENDING'})
  if p.suffix not in {'.cu','.cpp','.c','.f90','.cuf','.py'}: continue
  body=p.read_text(errors='replace'); code=re.sub(r'/\*.*?\*/|//[^\n]*','',body,flags=re.S)
  entry=bool(re.search(r'\b(?:int|auto|void)\s+main\s*\(|^\s*program\s+\w+',code,re.M|re.I))
  if p.suffix=='.py': entry=bool(re.search(r'__name__\s*==\s*[\'"]__main__',body)) or p.name in {'run.py','setup.py'}
  classification='entrypoint_candidate' if entry else ('test_module' if p.suffix=='.py' and (p.name.startswith('test') or '/test/' in name or '/tests/' in name) else 'auxiliary_or_unresolved')
  if p.name=='setup.py': entry=False;classification='packaging'
  sources.append({'path':name,'family':family,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'classification':classification,'review':'PENDING' if classification=='auxiliary_or_unresolved' else 'DISCOVERED'})
  if not entry: continue
  sid=str(pathlib.PurePosixPath(name).parent)+'::'+p.name
  sample={'id':sid,'family':family,'source':name,'source_sha256':sources[-1]['sha256'],'target':None,'discovery':'ENTRYPOINT_CANDIDATE','build_audit':'PENDING','candidate_libraries':CANDIDATES[family],'actual_library':None,'backend_library':None,'implementation':None,'status':'NOT_STARTED','level':'L0','required_cases':[],'passed_cases':[],'reason_code':None,'reason':'尚未移植；构建目标映射待审计','cuda_baseline':'NOT_RUN','cuda_comparison':'NOT_RUN','benchmark':'NOT_RUN','evidence':[],'attempts':[],'milestone':'M1' if (str(p.relative_to(ROOT).parent) in M1_DIRS and 'dotc' not in name) or name in M1_FILES else None}
  sample.update(previous.get(sid,{})); sample['milestone']='M1' if (str(p.relative_to(ROOT).parent) in M1_DIRS and 'dotc' not in name) or name in M1_FILES else None; samples.append(sample)
 if len({s['id'] for s in samples})!=len(samples): raise ValueError('duplicate sample id')
 out={'schema_version':1,'upstream_commit':BASE,'inventory_status':'PROVISIONAL_BUILD_AUDIT_PENDING','format':'JSON (YAML 1.2 subset; Python stdlib reader)','sources':sources,'build_definitions':builds,'samples':samples}
 oldpath.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'source_files':len(sources),'entrypoint_candidates':len(samples),'build_files':len(builds),'m1':sum(s['milestone']=='M1' for s in samples),'families':len(CANDIDATES)},ensure_ascii=False))

if __name__=='__main__': main()
