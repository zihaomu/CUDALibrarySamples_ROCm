#!/usr/bin/env python3
"""B4 API-signature fixes and input/output observation; upstream stays immutable."""
import pathlib,re,shutil
from catalog import ROOT
from batches4_8_spec import GROUPS,kind
def emit(n,p,c):return f'migration_observer::emit("{n}",{p},{c});\n'
for source in GROUPS['b4']:
 for backend in ['rocm','cuda']:
  p=ROOT/('rocm/ported' if backend=='rocm' else 'build/cuda-observed')/source;p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists():shutil.copyfile(ROOT/source,p)
  text=p.read_text();k=kind(source);rt='hip' if backend=='rocm' else 'cuda'
  if 'MIGRATION_BATCH4' in text:continue
  if k in ['trttp','tpttr']:
   license=(ROOT/source).read_text().split('#include')[0];p.write_text(license+'// MIGRATION_BATCH4: packed layout GPU implementation; independent CUDA vendor API.\n#include "batch4_packed.hpp"\nint main(){return migration_batch::packed_main('+('true' if k=='tpttr' else 'false')+');}\n');continue
  if k in ['spsv_sell','sddmm_bsr']:continue
  text='#include "observe.hpp"\n#include <string>\n'+text
  start=text.index('{',text.index('int main'))+1;text=text[:start]+'\n// MIGRATION_BATCH4\nconst std::string migration_case=std::getenv("MIGRATION_CASE")?std::getenv("MIGRATION_CASE"):"original";\n'+text[start:]
  if k in ['CherkEx','CsyrkEx']:
   text=text.replace('const float beta = 0.0;','const float beta = migration_case=="nonzero-beta"?-0.5f:0.f;')
   text=text.replace('const data_type beta = {0.0, 0.0};','const data_type beta = migration_case=="nonzero-beta"?data_type{-.5f,.25f}:data_type{0,0};')
   marker='    /* step 1:';code='if(migration_case=="nonzero-beta")for(size_t i=0;i<C.size();++i)C[i]=data_type{float(i+1),float(i%2)};\n'
   pref='HIPBLAS' if backend=='rocm' else 'CUBLAS'
   code+=f'if(migration_case=="lower")uplo={pref}_FILL_MODE_LOWER;\n'
   code+=f'if(migration_case=="'+('conjugate' if k=='CherkEx' else 'transpose')+f'")trans={pref}_OP_'+('C' if k=='CherkEx' else 'T')+';\n'
   for n in ['A','C']:code+=emit('input_'+n,n+'.data()',n+'.size()')
   code+=emit('input_beta','&beta','1')+emit('input_alpha','&alpha','1');text=text.replace(marker,code+marker,1)
   marker='    /* step 3: compute */';code=f'CUDA_CHECK({rt}MemcpyAsync(d_C,C.data(),sizeof(data_type)*C.size(),{rt}MemcpyHostToDevice,stream));\n';text=text.replace(marker,code+marker,1)
   if backend=='rocm':text=text.replace('traits<data_type>::cuda_data_type, ldc));','traits<data_type>::cuda_data_type, ldc, HIP_C_32F));')
  elif k=='GemmBatchedEx':
   text=text.replace('const data_type beta = 0.0;','const data_type beta = migration_case=="nonzero-beta"?-0.5:0.0;')
   if backend=='rocm':text=text.replace('(void **)d_A_array','(const void **)d_A_array').replace('(void **)d_B_array','(const void **)d_B_array')
   marker='    /* step 1:';code='if(migration_case=="transpose")transa='+('HIPBLAS' if backend=='rocm' else 'CUBLAS')+'_OP_T;\n'
   code+='if(migration_case=="changed-values")for(auto& v:A_array)for(auto& x:v)x*=-0.5;\n'
   code+='if(migration_case=="nonzero-beta")for(auto& v:C_array)for(size_t i=0;i<v.size();++i)v[i]=i+1;\n'
   for n in ['A','B','C']:code+=f'for(size_t i=0;i<{n}_array.size();++i)migration_observer::emit(("input_{n}_"+std::to_string(i)).c_str(),{n}_array[i].data(),{n}_array[i].size());\n'
   code+=emit('input_beta','&beta','1')+emit('input_alpha','&alpha','1');text=text.replace(marker,code+marker,1)
   # Original beta=0 did not need a C upload. Extended cases do.
   marker='    /* step 3: compute */';code=f'for(int i=0;i<batch_count;++i)CUDA_CHECK({rt}MemcpyAsync(d_C[i],C_array[i].data(),sizeof(data_type)*C_array[i].size(),{rt}MemcpyHostToDevice,stream));\n';text=text.replace(marker,code+marker,1)
  elif k=='ormqr':
   text=text.replace('migration_observer::emit("X",X.data(),X.size());','')
   text=text.replace('const std::vector<double> A','std::vector<double> A').replace('const std::vector<double> B','std::vector<double> B')
   text=text.replace('const int nrhs = 1;','const int nrhs = migration_case=="multiple-rhs"?2:1;')
   marker='    /* device memory */';code='if(migration_case=="changed-matrix"){A[0]+=1.;A[4]+=0.5;}if(nrhs==2){B.insert(B.end(),{1.,-2.,3.});}\n'+emit('input_A','A.data()','A.size()')+emit('input_B','B.data()','B.size()');text=text.replace(marker,code+marker,1)
   marker='    /* step 6:';pos=text.index(marker);code=f'''std::vector<double> migration_QR(A.size()),migration_tau(m),migration_QTB(B.size());
CUDA_CHECK({rt}Memcpy(migration_QR.data(),d_A,A.size()*sizeof(double),{rt}MemcpyDeviceToHost));
CUDA_CHECK({rt}Memcpy(migration_tau.data(),d_tau,m*sizeof(double),{rt}MemcpyDeviceToHost));
CUDA_CHECK({rt}Memcpy(migration_QTB.data(),d_B,B.size()*sizeof(double),{rt}MemcpyDeviceToHost));
'''+emit('QR','migration_QR.data()','migration_QR.size()')+emit('tau','migration_tau.data()','migration_tau.size()')+emit('QTB','migration_QTB.data()','migration_QTB.size()')+emit('info','&info','1');text=text[:pos]+code+text[pos:]
   # A second RHS tests a different Q application rather than duplicating a case.
   text=text.replace('if(nrhs==2){B.insert', 'if(migration_case=="Q-application"){B={2.,-1.,5.};}if(nrhs==2){B.insert')
  if 'MIGRATION_OBSERVE_ORIGINAL' not in text:
   marker='/* free resources */';names=['A','C'] if k in ['CherkEx','CsyrkEx'] else ['A','B','XC'] if k=='ormqr' else []
   code=''.join(emit(n,n+'.data()',n+'.size()') for n in names)
   if k=='GemmBatchedEx':code+='for(size_t i=0;i<C_array.size();++i)migration_observer::emit(("C_"+std::to_string(i)).c_str(),C_array[i].data(),C_array[i].size());\n'
   text=text.replace(marker,code+marker,1)
  p.write_text(text)
for family in ['cuBLAS','cuSOLVER']:shutil.copytree(ROOT/family/'utils',ROOT/'build/cuda-observed'/family/'utils',dirs_exist_ok=True)
print('Prepared B4 BLAS/solver sources')
