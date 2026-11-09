#!/usr/bin/env python3
"""Full CPU FFT checks for the remaining original small 2D/3D profiles."""
import fcntl,json,re
from validate_blas import ROOT,np
from run import digest,evidence_directory
results=[]
with (ROOT/'migration/.state.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);p=ROOT/'migration/samples.yaml';cat=json.loads(p.read_text())
 for s in cat['samples']:
  if s['source'] not in {'cuFFT/2d_c2r_r2c/2d_c2r_r2c_example.cpp','cuFFT/3d_c2c/3d_c2c_example.cpp'}:continue
  a=s['original_port'];d=evidence_directory(a['evidence']);checks=[]
  if a['return_code']!=0 or digest(ROOT/a['implementation'])!=a['implementation_sha256']:continue
  if '/2d_' in s['source']:
   x=np.fromfile(d/'input.bin',np.complex64).reshape(2,2,3);intermediate=np.fromfile(d/'intermediate.bin',np.float32).reshape(2,2,6)[:,:,:4];y=np.fromfile(d/'output.bin',np.complex64).reshape(2,2,3);expected=np.fft.irfftn(x,s=(2,4),axes=(-2,-1));checks=[('padded-layout-normalized-c2r-full-cpu',intermediate,expected),('r2c-roundtrip-full-cpu',y,np.fft.rfftn(expected,axes=(-2,-1)))];oracle='NumPy irfftn/rfftn; all 16 real /12 complex values, explicit padded in-place strides';inputs=digest(d/'input.bin')
  else:
   blocks=(d/'run.log').read_text().split('=====');parse=lambda t:np.asarray([float(a)+1j*float(b) for a,b in re.findall(r'(-?\d+\.\d+) \+ (-?\d+\.\d+)j',t)]);forward=next(parse(b) for b in blocks if 'Output array after Forward transform:' in b);inverse=next(parse(b) for b in blocks if 'Normalization and Inverse transform:' in b);x=(np.arange(16)-1j*np.arange(16)).reshape(2,2,2,2);checks=[('original-3d-forward-all-values-cpu',forward,np.fft.fftn(x,axes=(-3,-2,-1)).ravel()),('original-3d-gpu-normalization-roundtrip',inverse,x.ravel())];oracle='NumPy FFTN, original n=2^3 batch2 input i-i*j, every printed value checked at original 6-decimal output precision';inputs='source-defined deterministic i-i*j'
  details=[]
  for name,actual,ref in checks:
   error=float(np.max(abs(actual-ref)));details.append({'case':name,'passed':bool(np.isfinite(actual).all() and np.allclose(actual,ref,atol=1e-5,rtol=1e-5)),'max_abs_error':error})
  passed=all(x['passed'] for x in details);r={'id':s['id'],'status':'PASSED' if passed else 'FAILED','checks':details,'oracle':oracle,'input_identity':inputs,'evidence':a['evidence'],'implementation_sha256':a['implementation_sha256']};results.append(r)
  if passed:s.update(status='PASSED',level='L4',actual_library='hipFFT',backend_library='rocFFT',required_cases=[v['case'] for v in details],passed_cases=[v['case'] for v in details],reason_code='VALIDATED_ORIGINAL_PROFILE',reason='使用 hipFFT/rocFFT 保留原始尺寸、batch 和 GPU scaling，全部数值经独立 CPU FFT 检查；2D 实现修复原始 real 输出显示的 padded stride，并显式同步异步回传。');s['selected_validation']=r;s['evidence'].append('migration/reports/small-fft-validation.json')
 p.write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n')
(ROOT/'migration/reports/small-fft-validation.json').write_text(json.dumps(results,indent=2)+'\n');print([(r['id'],r['status']) for r in results])
