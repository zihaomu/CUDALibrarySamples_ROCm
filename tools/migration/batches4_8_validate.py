#!/usr/bin/env python3
"""Independent CPU qualification and same-input CUDA comparison for batch 3."""
import argparse,fcntl,json,pathlib
from catalog import ROOT
from batches4_8_spec import GROUPS,kind
from run import digest,evidence_directory
from validate_blas import np
from batches4_8_reference import validate

def json_scalar(value):
 if isinstance(value,np.generic):return value.item()
 raise TypeError(type(value).__name__)


def main():
 p=argparse.ArgumentParser();p.add_argument('groups',nargs='+',choices=list(GROUPS));p.add_argument('--qualify',action='store_true');a=p.parse_args();amd={r['source']:r for r in json.loads((ROOT/'migration/reports/batches4_8-rocm.json').read_text())};cp=ROOT/'migration/reports/batches4_8-cuda.json';cuda={r['source']:r for r in json.loads(cp.read_text())} if cp.exists() else {};results=[]
 for group in a.groups:
  for source,cases in GROUPS[group].items():
   r=amd.get(source);r_cuda=cuda.get(source);checks=[];comparisons=[]
   if not r:continue
   for case in cases:
    def one(run):
     if not run or run['build_return_code']!=0:raise ValueError('Build missing/failed')
     c=next(x for x in run['runs'] if x['case']==case)
     if c['return_code']!=0:raise ValueError('Run failed: '+str(c['return_code']))
     return validate(source,case,evidence_directory(c['evidence']))
    try:v=one(r)
    except Exception as e:v={'status':'FAILED','reason':str(e)}
    v['case']=case;checks.append(v)
    try:
     cv=one(r_cuda);same=v.get('input_sha256')==cv.get('input_sha256');yes=v['status']==cv['status']=='PASSED' and same
     # For solver factors use independent phase-invariant CPU checks on both.
     for name,vals in v.get('output_values',{}).items():yes=bool(yes and name in cv['output_values'] and np.allclose(vals,cv['output_values'][name],atol=1e-3 if kind(source)=='LtHSHgemmGroupedSimple' else 2e-6,rtol=1e-3 if kind(source)=='LtHSHgemmGroupedSimple' else 2e-6))
     comparisons.append({'case':case,'status':'PASSED' if yes else 'FAILED','identical_input':same,'cuda_cpu_checks':cv})
    except Exception as e:comparisons.append({'case':case,'status':'BLOCKED','reason':str(e)})
   passed=r['build_return_code']==0 and len(checks)==len(cases) and all(v['status']=='PASSED' for v in checks);comparison='PASSED' if all(v['status']=='PASSED' for v in comparisons) else 'BLOCKED' if any(v['status']=='BLOCKED' for v in comparisons) else 'FAILED';record=dict(r,status='PASSED' if passed else 'FAILED',level='L4' if passed else 'L3' if r['build_return_code']==0 else 'L1',cases=checks,cuda_comparison=comparison,cuda_cases=comparisons,cuda_evidence=r_cuda.get('evidence') if r_cuda else None,reference_library={'numpy':np.__version__,'scipy':__import__('scipy').__version__},validation_source_sha256=digest(pathlib.Path(__file__)))
   record['batch']=group
   record['cuda_baseline_kind']='COMPATIBLE_CUDA_MATH_BASELINE' if kind(source) in ['spmat_convert','spmv_symmetric_csr','spmvop_csr'] else 'CUDA_LIBRARY_DRIVER'
   record['cuda_implementation_sha256']=r_cuda.get('implementation_sha256') if r_cuda else None
   record['cuda_environment']=r_cuda.get('environment') if r_cuda else None
   record['dependencies']=dict(r.get('dependencies',{}),**{'tools/migration/batches4_8_reference.py':digest(ROOT/'tools/migration/batches4_8_reference.py')})

   record['dependencies']['tools/migration/batch'+group[1:]+'_reference.py']=digest(ROOT/('tools/migration/batch'+group[1:]+'_reference.py'))
   results.append(record);print(source,record['status'],'CUDA',comparison,[(c['case'],c.get('reason')) for c in checks if c['status']!='PASSED'],flush=True)
 if a.qualify:
  with (ROOT/'migration/.state.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);p=ROOT/'migration/samples.yaml';cat=json.loads(p.read_text())
   for r in results:
    s=next(s for s in cat['samples'] if s['source']==r['source']);assert digest(ROOT/r['implementation'])==r['implementation_sha256'];s['attempts'].append(r);s['evidence']+=list(dict.fromkeys([r['evidence'],'migration/reports/batches4_8-validation.json']+([r['cuda_evidence']] if r['cuda_evidence'] else [])))
    if r['status']=='PASSED' and r['cuda_comparison']=='PASSED':
     labels=['batches4_8/'+v['case'] for v in r['cases']];lib={'cuSPARSE':('hipSPARSE + hipBLAS','rocSPARSE/rocBLAS'),'cuBLAS':('hipBLAS','rocBLAS'),'cuSOLVER':('hipSOLVER','rocSOLVER/rocBLAS'),'cuTENSOR':('hipTensor','hipTensor'),'cuBLASLt':('hipBLASLt','hipBLASLt')}[s['family']];lib=('hipSPARSE + HIP Graph','rocSPARSE + HIP runtime') if '/graph_capture/' in s['source'] else lib;s.update(status='PASSED',level='L4',implementation=r['implementation'],actual_library=lib[0],backend_library=lib[1],required_cases=labels,passed_cases=labels,reason_code='VALIDATED_B4_B8',reason='使用 '+lib[0]+' / '+lib[1]+' 保留原始 profile 与数学 API；'+str(len(labels))+' 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。'+('同输入 CUDA 与 CPU 三方对照通过。' if r['cuda_comparison']=='PASSED' else 'CUDA 对照受前置条件限制，未计为通过。'),cuda_comparison=r['cuda_comparison'],selected_validation=r,reproduce='HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches4_8_run.py '+next(g for g,m in GROUPS.items() if s['source'] in m)+'\npython3 tools/migration/batches4_8_validate.py '+next(g for g,m in GROUPS.items() if s['source'] in m)+' --qualify');s['cuda_baseline']='PASSED' if r['cuda_comparison']=='PASSED' else s['cuda_baseline'];s.pop('cuda_comparison_reason',None)
     k=kind(s['source'])
     if k in ['trttp','tpttr']:s.update(actual_library='HIP GPU packed conversion',backend_library='HIP runtime',equivalence='HYBRID_HIP')
     if k in ['spsv_sell','sddmm_bsr']:s.update(actual_library='hipSPARSE + HIP format adapter',backend_library='rocSPARSE + HIP runtime',equivalence='HYBRID_HIP')
     if k in ['CherkEx','CsyrkEx']:s['reason']+=' 原始固定complex32使用类型化hipBLAS Cherk/Csyrk保留dtype和数学方程；原生Ex包装失败另存。';s['evidence'].append('migration/reports/b4-native-ex-failure.json')
     if k in ['trttp','tpttr','spsv_sell','sddmm_bsr']:s['reason']='使用 '+s['actual_library']+' / '+s['backend_library']+' 保留原始dtype/布局与数学运算；'+str(len(labels))+' 个预登记输入case通过独立CPU与同输入CUDA，GPU适配和数值路径均已检查。'
     if r['batch']=='b5':
      routes={'elementwise_permute_padding':('HIP GPU permutation/padding','HIP runtime'),'einsum':('hipTensor + rocBLAS + HIP','hipTensor/rocBLAS'),'contraction_trinary':('rocBLAS + HIP tensor adapter','rocBLAS/HIP runtime'),'contraction_plan_cache':('rocBLAS + HIP tiled-plan/cache adapter','rocBLAS/HIP runtime')};s.update(actual_library=routes[k][0],backend_library=routes[k][1],equivalence='HYBRID_HIP');s['reason']='使用 '+s['actual_library']+'；保留原始规模和FP32精度，'+str(len(labels))+' cases全输出独立FP64 CPU及同输入CUDA通过。缓存为项目真实GPU分块策略搜索/持久化适配，包含损坏、descriptor变化和新进程重放；不宣称原生hipTensor缓存API等价。' if k=='contraction_plan_cache' else '使用 '+s['actual_library']+'；保留原始规模和FP32精度，'+str(len(labels))+' cases全输出独立FP64 CPU及同输入CUDA通过。'
     if r['batch']=='b6':
      routes={'Xgetrf':('rocSOLVER ILP64','rocSOLVER'),'Xtrtri':('hipBLAS Dtrsm_64 + HIP diagonal/info adapter','rocBLAS/HIP runtime'),'Xsyevdx':('rocSOLVER dsyevx + checked dimension bridge','rocSOLVER'),'Xgesvd':('rocSOLVER dgesvd + checked dimension bridge','rocSOLVER')};s.update(actual_library=routes[k][0],backend_library=routes[k][1],equivalence='HYBRID_HIP');s['reason']='使用 '+s['actual_library']+'，原始FP64 profile及'+str(len(labels))+' cases通过CPU/CUDA数值、返回数量与info检查。'+('公开typed接口限制INT_MAX，调用前显式检查，不宣称全尺寸ILP64支持。' if k in ['Xsyevdx','Xgesvd'] else '64位尺寸/主元保留。')
     if r['batch']=='b7':
      s.update(actual_library='hipBLASLt + project search/group dispatch' if s['family']=='cuBLASLt' else 'hipBLAS + project search/group dispatch',backend_library='hipBLASLt/rocBLAS' if s['family']=='cuBLASLt' else 'rocBLAS',equivalence='HYBRID_HIP');s['reason']='使用 '+s['actual_library']+'，保持原始dtype/规模，全部候选完整输出、所选方案重放及workspace限制通过CPU/CUDA。分组为项目分发适配；搜索ID仅在对应后端有效，不跨库照搬CUDA算法ID；共享GPU计时不计性能资格。'
     if r['batch']=='b8':
      routes={'spmat_convert':'hipSPARSE Csr2cscEx2','spgemm_mem':'HIP GPU budgeted CSR SpGEMM adapter','spmv_symmetric_csr':'HIP symmetric expansion + rocSPARSE v2','spmvop_csr':'HIP GPU fused custom SpMV epilogue','spmm_csr_op':'HIP GPU fused custom SpMM add/mul/epilogue'};s.update(actual_library=routes[k],backend_library='rocSPARSE/HIP runtime' if k in ['spmat_convert','spmv_symmetric_csr'] else 'HIP runtime',equivalence='HYBRID_HIP');s['reason']='使用 '+routes[k]+'，保留原始稀疏布局/精度和数学公式；结构、全量数值、自定义行为/内存预算通过CPU/CUDA。'+('CUDA SDK缺失原始新API，CUDA为兼容数学基线（原生编译失败另存），不宣称原始CUDA API已运行。' if k in ['spmat_convert','spmv_symmetric_csr','spmvop_csr'] else '原生CUDA SpGEMM ALG3/SpMMOp通过。');s['evidence'].append('migration/reports/b8-native-cuda-api-failure.json')
     s['retry_condition']='已登记profile通过；扩展其它精度/规模/矩阵性质或API配置时，新增预登记输入并重新做CPU/CUDA及运行语义验收。'
     if '/graph_capture/' in s['source']:s.update(equivalence='API_PORT_WITH_EXECUTION_ADAPTER',reason=s['reason']+'初始化确定性输入并改用device pointer mode；实际GPU图节点及三次输入变化replay均已检查。')
     hip=str(r['environment'].get('visible_devices','2'));s['reproduce']=s['reproduce'].replace('HIP_VISIBLE_DEVICES=2','HIP_VISIBLE_DEVICES='+hip)
     if r['cuda_comparison']=='PASSED':
      s['cuda_baseline_reason']='CUDA library mathematical calls and the same registered inputs independently passed CPU numerical checks.'
      if r['cuda_baseline_kind']=='COMPATIBLE_CUDA_MATH_BASELINE':s.update(cuda_baseline='FAILED',cuda_comparison_mode=r['cuda_baseline_kind'],cuda_baseline_reason='Original new cuSPARSE API absent in installed CUDA SDK; native compile failure retained. A compatible cuSPARSE/CUDA GPU mathematical baseline passed same-input CPU checks.')
    s['evidence']=list(dict.fromkeys(s['evidence']))
   p.write_text(json.dumps(cat,indent=2,ensure_ascii=False,default=json_scalar)+'\n')
 report=ROOT/'migration/reports/batches4_8-validation.json';old=json.loads(report.read_text()) if report.exists() else [];merged={r['source']:r for r in old};merged.update({r['source']:r for r in results});report.write_text(json.dumps(list(merged.values()),indent=2,ensure_ascii=False,default=json_scalar)+'\n')
if __name__=='__main__':main()
