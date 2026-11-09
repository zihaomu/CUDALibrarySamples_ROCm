#!/usr/bin/env python3
"""Independent full NumPy FFT / analytic roundtrip checks for binary observations."""
import fcntl,hashlib,json
from validate_blas import ROOT,np
from run import digest,evidence_directory
results=[]
with (ROOT/'migration/.state.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);p=ROOT/'migration/samples.yaml';cat=json.loads(p.read_text())
 for s in cat['samples']:
  if s['family']!='cuFFT':continue
  a=s.get('original_port',{})
  if a.get('return_code')!=0 or not a.get('qualified_physical_devices') or digest(ROOT/a['implementation'])!=a['implementation_sha256']:continue
  d=evidence_directory(a['evidence']);inp=d/'input.bin';output=d/'output.bin'
  if not inp.exists() or not output.exists():continue
  name=s['source'].split('/')[1];x=np.fromfile(inp,dtype=np.float32);y=np.fromfile(output,dtype=np.float32)
  if name=='3d_mgpu_c2c':x=x.view(np.complex64).reshape((256,256,256));y=y.view(np.complex64).reshape(x.shape);expected=np.fft.fftn(x);oracle='NumPy/pocketfft full 256^3 C2C transform'
  elif name=='3d_mgpu_r2c_c2r':x=x.reshape((256,256,258))[...,:256];y=y.reshape((256,256,258))[...,:256];expected=x.astype(np.float64)*(2*256**3);oracle='Analytic R2C -> spectrum*2 -> unnormalized C2R = input*2*N, original padded layout; padding is excluded from semantic elements'
  elif 'lto_callback_window_1d' in s['source']:
   x=x.reshape((830,330))[:,:328];y=y.reshape((830,330))[:,:328];f=np.fft.rfft(x,axis=-1);f[:,32:]=0;expected=np.fft.irfft(f,n=328,axis=-1)*328;oracle='Independent CPU rfft, frequency truncation at bin32, irfft*328 on all 830 signals'
  else:continue
  diff=y-expected;error=float(np.linalg.norm(diff.ravel())/max(np.linalg.norm(expected.ravel()),1));passed=bool(np.all(np.isfinite(y)) and error<1e-5);r={'id':s['id'],'status':'PASSED' if passed else 'FAILED','relative_l2':error,'threshold':1e-5,'max_abs_error':float(np.max(abs(diff))),'semantic_elements':int(y.size),'oracle':oracle,'input_sha256':digest(inp),'output_sha256':digest(output),'implementation_sha256':a['implementation_sha256'],'original_sha256':s['source_sha256'],'devices':a['devices'],'evidence':a['evidence']};results.append(r)
  if passed:
   s.update(status='PASSED',level='L4',actual_library='hipFFT',backend_library='rocFFT',required_cases=['original-profile-independent-cpu','original-profile-reference-pipeline'],passed_cases=['original-profile-independent-cpu','original-profile-reference-pipeline'],reason_code='VALIDATED_ORIGINAL_PROFILE',reason='使用 hipFFT/rocFFT 保留原始 '+('双 GPU descriptor/分布与数据规模' if 'mgpu' in name else 'device load callback 融合与原始 window/batch 配置')+'；全量输出通过独立 CPU '+oracle+'，相对 L2='+str(error)+'。性能未验收。');s['original_profile_validation']=r;s['evidence'].append('migration/reports/fft-original-validation.json')
 p.write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n')
(ROOT/'migration/reports/fft-original-validation.json').write_text(json.dumps(results,indent=2)+'\n');print([(v['id'],v['status'],v['relative_l2']) for v in results])
