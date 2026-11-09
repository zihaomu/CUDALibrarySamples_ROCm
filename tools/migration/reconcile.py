#!/usr/bin/env python3
"""Select qualified implementations without hiding failed drafts or unimplemented bindings."""
import collections,fcntl,json,re
from catalog import ROOT,CANDIDATES
from run import digest

def read(name):return json.loads((ROOT/'migration/reports'/name).read_text())
def select(s,r,source,library,backend,cases,reason,reproduce):
 assert r['status']=='PASSED' and r['return_code']==0
 assert r['source_sha256']==digest(ROOT/source)
 s.update(status='PASSED',level='L4',implementation=source,actual_library=library,backend_library=backend,required_cases=cases,passed_cases=cases,reason_code='VALIDATED_LIBRARY_REWRITE',reason=reason,reproduce=reproduce)
 s['selected_validation']=dict(r,implementation=source,implementation_sha256=r['source_sha256'])
 if r['evidence'] not in s['evidence']:s['evidence'].append(r['evidence'])
 if not any(a.get('evidence')==r['evidence'] for a in s['attempts']):s['attempts'].append(s['selected_validation'])

def main():
 with (ROOT/'migration/.state.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);p=ROOT/'migration/samples.yaml';cat=json.loads(p.read_text());rows={s['source']:s for s in cat['samples']};probes=read('native-probes.json');decisions=json.loads((ROOT/'migration/ecosystem-decisions.json').read_text())
  select(rows['cuDSS/simple/simple.cpp'],probes['rocsolver_sparse_chol'],'rocm/cuDSS/simple/sample.cpp','rocSOLVER CSRRF + rocBLAS','GPU sparse Cholesky; CPU sparse symbolic analysis',['original-upper-csr-solution','original-upper-csr-residual','scaled-matrix-solution-residual'],'使用 CPU 稀疏图消去构造符号 L pattern，rocSOLVER CSRRF 在 GPU 上完成稀疏 Cholesky 数值分解和求解；保留原始 FP64 upper-CSR 5×5 SPD 与 RHS，解/残差及缩放矩阵检查通过。未转 dense；高级 cuDSS 接口未覆盖。','python tools/migration/probes.py rocsolver_sparse_chol')
  rows['cuDSS/simple/simple.cpp']['selected_validation']['dependencies']={'rocm/cuDSS/common/sparse_chol.hpp':digest(ROOT/'rocm/cuDSS/common/sparse_chol.hpp')}
  select(rows['cuTENSOR/contraction.cu'],probes['tensor_rocblas'],'rocm/probes/tensor_rocblas.hip','rocBLAS + HIP','FP32 GEMM and GPU tensor permutations',['small-four-dimensional-full-cpu-beta','original-extents-fp32-all-finite','original-extents-32-cpu-dot-products'],'hipTensor 在 gfx1201 拒绝 FP32 contraction，FP16 compute 探针亦有数值失败；选用 rocBLAS SGEMM + HIP 排列，保留原始 modes/extents、FP32、alpha=1.1/beta=0。小尺寸全量 CPU（beta=0.5）及原始规模全量有限值/32 个双精度 CPU 抽样点通过。未声称原始随机输入逐值等同或 JIT/cache 已实现。','python tools/migration/probes.py tensor_rocblas')
  select(rows['cuFFT/1d_mgpu_c2c/1d_mgpu_c2c_example.cpp'],probes['distributed_fft'],'rocm/probes/distributed_fft.hip','hipFFT + RCCL + HIP','Two GPU radix decomposition and GPU merge',['original-n256-seed3-two-gpu-full-cpu-dft'],'hipFFT Xt 不接受该单 batch 1D 配置，改用两卡各做 128 点 hipFFT、RCCL AllGather 和 HIP radix-2 合并；保留原始 n=256、FP32、两卡与全局布局，全部复数输出通过 CPU DFT。原 CUDA 重复 {0,0} 设备配置在对照副本中修正为 {0,1}。','python tools/migration/probes.py distributed_fft')
  partials=[('nvCOMP/examples/low_level_quickstart_example.cpp','hipcomp_lz4','rocm/probes/hipcomp_lz4.cpp','hipCOMP','LZ4 GPU 压缩/解压在 128/32768/65536 字节、单 chunk 输入逐字节往返通过；原始现代 nvCOMP status/options、batch 和其它 codec 契约未完成，保留 PARTIAL。'),('nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp','rocjpeg_decode','rocm/probes/rocjpeg_decode.cpp','rocJPEG','硬件 backend 对原仓库 64×64 baseline cat JPEG 解码 RGB，通过独立 Pillow/libjpeg 对照（最大像素误差 2）；原始所有输入/格式、batch/多实例/CLI 未覆盖，保留 PARTIAL。')]
  for src,name,code,lib,reason in partials:
   s=rows[src];r=probes[name];assert r['status']=='PASSED' and digest(ROOT/code)==r['source_sha256'];s.update(status='PARTIAL',level='L3',implementation=code,actual_library=lib,backend_library=lib,reason_code='SEMANTIC_GAP',reason=reason,reproduce='python tools/migration/probes.py '+name);s['selected_validation']=r;s['passed_cases']=['gpu-subset-probe'];s['required_cases']=['gpu-subset-probe','original-full-functional-contract'];s['evidence']+=['migration/reports/native-probes.json',r['evidence']]
  rng={r['sample_id']:r for r in read('rng-original-validation.json')}
  for s in cat['samples']:
   family=s['family'];s['candidate_libraries']=CANDIDATES[family];s['retry_condition']=decisions[family]['retry_condition']
   if family=='cuSPARSELt':
    s.update(status='UNSUPPORTED',reason_code='HW_UNSUPPORTED',reason='锁定 ROCm 10.1.0 hipSPARSELt 已编译，但 gfx1201 缺少 kernel bundle；实机返回 NOT_IMPLEMENTED/无法加载 TensileLibrary_lazy_gfx1201，固定源码架构检查也拒绝 gfx1201。仅限此版本/硬件/后端；保留 structured prune/compress/matmul 契约，未改成 dense。');s['evidence']+=['migration/reports/upstream-support/hipsparselt-gfx1201-configure.log','migration/reports/upstream-support/sources.json']
   if s['level']=='L1':s['actual_library']=None;s['backend_library']=None
   if s['status']!='PASSED' and s['source'].endswith(('.py','.f90','.cuf')):
    s['attempted_source']=s.get('implementation');s['implementation']=None;s['level']='L0';s['actual_library']=None;s['backend_library']=None
    if s['source']=='nvJPEG/nvJPEG-Decoder/tests/test_decoder.py':s.update(status='BLOCKED',reason_code='ENV_MISSING_DEP',reason='Python imports 已通过，但 AMD decoder executable 与完整原始 CLI/GPU 测试前置条件尚未实现；只做 import 资格检查不能推断 GPU 成功。')
   if not s['required_cases']:s['required_cases']=['original-functional-contract','independent-numerical-or-semantic-reference']
   if s['status']=='PARTIAL' and not s['passed_cases']:
    s['passed_cases']=['build-and-original-profile-execution'];s['required_cases']=list(dict.fromkeys(s['passed_cases']+s['required_cases']))
    if '独立' not in s['reason']:s['reason']+='；原始功能的独立数值/语义验收未完成。'
   s['evidence']=list(dict.fromkeys(s['evidence']))
   # This metadata is a reproducible source index, not a claim of full semantic review.
   text=(ROOT/s['source']).read_text(errors='replace');s['original_semantics']={'contract_source':s['source'],'source_sha256':s['source_sha256'],'api_tokens':sorted(set(re.findall(r'\b(?:cublas|cusparse|cusolver|cufft|curand|cutensor|cudss|nvjpeg|nvtiff|nvcomp|cuest)[A-Za-z0-9_]+',text))),'review_scope':'Original source is the authoritative dtype/layout/batch/API contract; qualified subset and deviations are explicit in reason and required_cases.'}
   s['equivalence']='HYBRID_HIP' if s['source'] in {'cuTENSOR/contraction.cu','cuFFT/1d_mgpu_c2c/1d_mgpu_c2c_example.cpp'} or s['family']=='cuPQC' and s['status']=='PASSED' else 'LIBRARY_REWRITE' if s['family']=='cuDSS' and s['status']=='PASSED' else 'API_PORT' if s['implementation'] else 'UNIMPLEMENTED_BINDING'
   if s['id'] in rng and s['milestone']!='M1':
    r=rng[s['id']];assert r['status']=='PASSED' and r['original_port_sha256']==digest(ROOT/s['implementation']);s['selected_validation']=dict(r,implementation=s['implementation'],implementation_sha256=r['original_port_sha256'])
   if not s['milestone']:s['milestone']='M4' if family in {'cuBLASMp','cuFFTMp','cuSOLVERMp','cuTENSORMg','cuTENSORMp'} or family=='cuFFT' and 'mgpu' in s['source'] else 'M2' if family in {'cuBLAS','cuBLASLt','cuSPARSE','cuSOLVER','cuFFT','cuRAND'} else 'M3' if family in {'cuTENSOR','cuSPARSELt','NPP','NPP+','nvCOMP','nvJPEG','nvJPEG2000','nvTIFF'} else 'M5'
   if s['status']=='FAILED':s['next_step']='按当前逐例错误和 retry_condition 改写/补齐，再运行原始 profile 与独立参考。'
  # Performance is a separate gate; numerical correctness remains valid.
  rows['cuBLAS/Level-3/gemm/cublas_gemm_example.cu']['benchmark']='BLOCKED'
  cat['execution_scope']='All 639 distinct source entrypoints attempted. Terminal outcomes include failed drafts, partial implementations and scoped prerequisites; not all ported successfully.'
  p.write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n');print(collections.Counter(s['status'] for s in cat['samples']))
if __name__=='__main__':main()
