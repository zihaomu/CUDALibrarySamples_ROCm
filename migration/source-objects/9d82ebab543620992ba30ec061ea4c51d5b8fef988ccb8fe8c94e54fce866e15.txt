#!/usr/bin/env python3
"""Additional original-profile comparisons; no success from exit code alone."""
import collections,fcntl,json,re
from validate_blas import ROOT,np,observed
from run import digest,evidence_directory
from solver_reference import validate as solver_checks

def read(name):return json.loads((ROOT/'migration/reports'/name).read_text())
def main():
 results=[];cuda={r['sample_id']:r for r in read('original-cuda-latest.json')['results']};rng_cuda={r['sample_id']:r for r in read('rng-cuda-validation.json')};rng_amd={r['sample_id']:r for r in read('rng-original-validation.json')};hash_cuda={r['sample_id']:r for r in read('hash-cuda.json')};hash_amd={r['sample_id']:r for r in read('hash-rocm.json')};callbacks={r['name']:r for r in read('cuda-callback-observed.json')};jit={r['mode']:r for r in read('jit-fft-validation.json')};prereq={r['sample_id']:r for r in read('cuda-language-prerequisites.json')}
 with (ROOT/'migration/.state.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);p=ROOT/'migration/samples.yaml';cat=json.loads(p.read_text())
  for s in cat['samples']:
   b=cuda.get(s['id']);r=None
   if s['id'] in prereq:
    s['cuda_baseline']='BLOCKED';s['cuda_prerequisite']=prereq[s['id']];s['evidence'].append(prereq[s['id']]['evidence'])
   if b:
    s['original_cuda']=b;s['evidence'].append(b['evidence']);d=ROOT/b['evidence'];log=(d/'run.log').read_text(errors='replace') if (d/'run.log').exists() else '';build=(d/'build.log').read_text(errors='replace') if (d/'build.log').exists() else ''
    missing=bool(re.search(r'No such file|cannot find -l|file not found',build,re.I));usage=bool(re.search(r'usage:|Usage:|No (?:input|file)|no (?:input|file)|waived|SKIPPED',log))
    baseline='BLOCKED' if missing or usage else 'PASSED' if b['return_code']==0 else 'FAILED';s['cuda_baseline']=baseline;s['cuda_baseline_scope']='Original source with observation-only output where present; build/run qualification, separate from independent correctness comparison.'
    s['cuda_baseline_reason']='Missing optional CUDA SDK/input or skipped compute' if baseline=='BLOCKED' else b['reason']
   if s['id'] in rng_amd:
    a=rng_amd[s['id']];b_rng=rng_cuda.get(s['id']);checks=[]
    if b_rng:
     ca={c['case']:c for c in a['cases']};cb={c['case']:c for c in b_rng['cases']}
     for name,c in ca.items():checks.append({'case':name,'passed':bool(c['passed'] and name in cb and cb[name]['passed'] and c.get('parameters')==cb[name].get('parameters'))})
    r={'status':'PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED','scope':'Original generator parameters and within-library same-seed/offset repeat, analytic moments independently checked on both GPUs; cross-library raw sequences need not match.','checks':checks,'rocm_evidence':a['evidence'],'cuda_evidence':b_rng['evidence'] if b_rng else None}
    s['cuda_baseline']='PASSED' if b_rng and b_rng['status']=='PASSED' else 'BLOCKED'
   elif s['id'] in hash_amd:
    a=hash_amd[s['id']];bh=hash_cuda[s['id']];checks=[{'case':x['case'],'passed':bool(x['passed'] and y['passed'] and x['input_sha256']==y['input_sha256'] and x['actual']==y['actual']==x['expected']==y['expected'])} for x,y in zip(a['cases'],bh['cases'])];r={'status':'PASSED' if len(checks)==14 and all(c['passed'] for c in checks) else 'FAILED','checks':checks,'scope':'Custom HIP SHA implementation built for AMD and CUDA plus independent hashlib; NVIDIA cuPQC SDK original baseline remains unavailable.','rocm_evidence':a['evidence'],'cuda_evidence':bh['evidence']};s['cuda_vendor_comparison']='BLOCKED'
   elif s['family']=='cuFFT' and 'callback_window' in s['source'] and s['status']=='PASSED':
    name=s['source'].split('/')[-1].split('.')[0];cb=callbacks[name]
    a=s['original_port'] if 'legacy' in name else jit['runtime' if 'nvrtc' in name else 'bitcode'];da=evidence_directory(a['evidence']);db=evidence_directory(cb['evidence']);xa=da/'input.bin';xb=db/'input.bin';ya=np.fromfile(da/'output.bin',np.float32).reshape(830,330)[:,:328];yb=np.fromfile(db/'output.bin',np.float32).reshape(830,330)[:,:328];error=float(np.linalg.norm(ya-yb)/max(1,np.linalg.norm(yb)));same=digest(xa)==digest(xb)==cb['fixture_sha256'];r={'status':'PASSED' if same and np.isfinite(ya).all() and np.isfinite(yb).all() and error<1e-5 else 'FAILED','relative_l2':error,'threshold':1e-5,'input_sha256':digest(xa),'identical_input_bytes':same,'semantic_elements':int(ya.size),'scope':'Full original 830x328 window32 CUDA callback and HIP callback output, same saved input; independent CPU reference separately passed.','rocm_evidence':a['evidence'],'cuda_evidence':cb['evidence']};s['cuda_baseline']=cb['status']
   elif s['family']=='cuFFT' and 'mgpu' in s['source'] and s['status']=='PASSED' and b and b['return_code']==0:
    a=s['selected_validation'] if '1d_mgpu' in s['source'] else s['original_port'];da=evidence_directory(a['evidence']);db=evidence_directory(b['evidence']);xa=da/'input.bin';xb=db/'input.bin'
    if xb.exists():
     realpair='r2c' in s['source'];dtype=np.float32 if realpair else np.complex64;ya=np.fromfile(da/'output.bin',dtype);yb=np.fromfile(db/'output.bin',dtype)
     if realpair:ya=ya.reshape(256,256,258)[...,:256];yb=yb.reshape(256,256,258)[...,:256]
     error=float(np.linalg.norm((ya-yb).ravel())/max(1,np.linalg.norm(yb.ravel())));same=digest(xa)==digest(xb);r={'status':'PASSED' if same and np.isfinite(ya).all() and np.isfinite(yb).all() and error<1e-5 else 'FAILED','relative_l2':error,'threshold':1e-5,'identical_input_bytes':same,'input_sha256':digest(xa),'semantic_elements':int(ya.size),'scope':'Actual two GPU original-profile outputs with explicit identical input fixture; CPU reference separately qualified.','rocm_evidence':a['evidence'],'cuda_evidence':b['evidence']}
   elif s['family']=='cuBLASLt' and 'HSHgemm' in s['source'] and s['status']=='PASSED' and b and b['return_code']==0:
    a=s['original_port'];oa=observed(ROOT/a['evidence']/'run.log');ob=observed(ROOT/b['evidence']/'run.log');checks=[]
    for name in ['A','B','D' if 'D' in oa else 'C']:
     yes=name in ob and oa[name].shape==ob[name].shape and np.isfinite(oa[name]).all() and np.isfinite(ob[name]).all() and np.allclose(oa[name],ob[name],atol=1e-5,rtol=1e-5);checks.append({'buffer':name,'passed':bool(yes),'max_abs_error':float(np.max(abs(oa[name]-ob[name]))) if name in ob else None})
    r={'status':'PASSED' if all(c['passed'] for c in checks) else 'FAILED','checks':checks,'scope':'Original fixed HSH 4x4 batch2; same input matrices and every output value, independent CPU GEMM/half rounding separately passed.','rocm_evidence':a['evidence'],'cuda_evidence':b['evidence']}
   elif s['family']=='cuSOLVER' and s['status']=='PASSED' and s.get('original_profile_validation',{}).get('status')=='PASSED' and b and b['return_code']==0 and s['milestone']!='M1':
    try:
     checks,o=solver_checks(s['source'],ROOT/b['evidence']/'run.log');a=s['original_port'];oa=observed(ROOT/a['evidence']/'run.log');spectra=[k for k in ['W','S'] if k in o and k in oa]
     for k in spectra:checks.append({'check':'cross-GPU-'+k,'passed':bool(np.allclose(np.sort(o[k]),np.sort(oa[k]),atol=1e-10,rtol=1e-10))})
     r={'status':'PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED','checks':checks,'scope':'Same literal original matrix; independent CPU residual/reconstruction/orthogonality on CUDA as well as ROCm. Sign/phase-invariant comparison.','rocm_evidence':a['evidence'],'cuda_evidence':b['evidence']}
    except Exception as exc:r={'status':'BLOCKED','reason':str(exc),'scope':'Lossless CUDA observation or independent oracle missing'}
   if r:
    r.update(id=s['id'],original_source_sha256=s['source_sha256']);s['cuda_comparison']=r['status'];s['additional_comparison']=r;s['evidence'].append('migration/reports/additional-comparison.json');results.append(r)
   elif s['cuda_comparison']!='PASSED':
    s['cuda_comparison']='BLOCKED';s['cuda_comparison_reason']=('CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。' if s['cuda_baseline']=='BLOCKED' else '当前 AMD 路线尚未通过正确性验收。' if s['status']!='PASSED' else 'AMD 已通过所列 CPU/数学参考，但同输入跨 GPU 独立对照尚未完成。')
   s['evidence']=list(dict.fromkeys(s['evidence']))
  p.write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n')
 (ROOT/'migration/reports/additional-comparison.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n');print(collections.Counter(r['status'] for r in results));print([(r['id'],r.get('reason',r.get('relative_l2'))) for r in results if r['status']!='PASSED'])
if __name__=='__main__':main()
