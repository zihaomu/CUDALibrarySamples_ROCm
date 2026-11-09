#!/usr/bin/env python3
"""Validate complete callback outputs with independent CPU frequency filtering."""
import fcntl,json
from validate_blas import ROOT,np
from run import digest,evidence_directory
results=json.loads((ROOT/'migration/reports/jit-fft.json').read_text())
with (ROOT/'migration/.state.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);p=ROOT/'migration/samples.yaml';cat=json.loads(p.read_text())
 for r in results:
  if r['return_code']!=0:continue
  source=ROOT/'rocm/cuFFT/lto_callback_window_1d/sample_jit.cpp';callback=source.parent/'window_callback.hip'
  if digest(source)!=r['source_sha256'] or digest(callback)!=r['callback_sha256']:continue
  d=evidence_directory(r['evidence']);x=np.fromfile(d/'input.bin',np.float32).reshape(830,330)[:,:328];y=np.fromfile(d/'output.bin',np.float32).reshape(830,330)[:,:328];f=np.fft.rfft(x,axis=-1);f[:,32:]=0;expected=np.fft.irfft(f,n=328,axis=-1)*328;error=float(np.linalg.norm(y-expected)/np.linalg.norm(expected));passed=bool(np.isfinite(y).all() and error<1e-5);r.update(status='PASSED' if passed else 'FAILED',relative_l2=error,threshold=1e-5,oracle='NumPy/pocketfft full 830x328 rfft + bin32 truncation + irfft*328',input_sha256=digest(d/'input.bin'),output_sha256=digest(d/'output.bin'),semantic_elements=int(y.size))
  source_id='cuFFT/lto_callback_window_1d/src/r2c_c2r_lto_'+('nvrtc_' if r['mode']=='runtime' else '')+'callback_example.cpp';s=next(s for s in cat['samples'] if s['source']==source_id)
  if passed:s.update(status='PASSED',level='L4',actual_library='hipFFT/rocFFT JIT callbacks'+(' + HIPRTC' if r['mode']=='runtime' else ' + HIP compiler SPIR-V'),backend_library='rocFFT SPIR-V JIT integration',implementation=str(source.relative_to(ROOT)),required_cases=['original-window32-batch830-size328-independent-cpu','runtime-HIPRTC-SPIRV' if r['mode']=='runtime' else 'compiled-SPIRV-JIT'],passed_cases=['original-window32-batch830-size328-independent-cpu','runtime-HIPRTC-SPIRV' if r['mode']=='runtime' else 'compiled-SPIRV-JIT'],reason_code='VALIDATED_ORIGINAL_PROFILE',reason=('HIPRTC 运行时编译 SPIR-V' if r['mode']=='runtime' else 'HIP 编译器预生成 SPIR-V')+'，经 hipfftXtSetJITCallback 与 FFT 内核 JIT 集成，保留 device callback 融合；原始 830×328、window32 全量输出通过独立 CPU FFT/filter/inverse 检查，L2='+str(error)+'。');s['attempts'].append(r);s['evidence'].append(r['evidence']);s['selected_validation']=r
 p.write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n')
(ROOT/'migration/reports/jit-fft-validation.json').write_text(json.dumps(results,indent=2)+'\n');print([(r['mode'],r['status'],r.get('relative_l2')) for r in results])
