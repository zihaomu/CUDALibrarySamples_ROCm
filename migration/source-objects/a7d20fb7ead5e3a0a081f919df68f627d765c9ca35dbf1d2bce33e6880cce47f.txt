#!/usr/bin/env python3
"""Add input cases and lossless observation; retain original GPU mathematical calls."""
import json,pathlib,re,shutil
from catalog import ROOT
from batch2_spec import ALL,SPARSE,BLAS,TENSOR
from run import digest

def emit(name,expression,count):return f'migration_observer::emit("{name}",{expression},{count});\n'
for source,cases in ALL.items():
 for backend in ['rocm','cuda']:
  p=ROOT/('rocm/ported' if backend=='rocm' else 'build/cuda-observed')/source
  if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source,p)
  text=p.read_text()
  if 'MIGRATION_BATCH2' in text:continue
  text='#include "observe.hpp"\n#include <string>\n#include <cstdlib>\n'+text;start=text.index('{',text.index('int main'))+1
  text=text[:start]+'\n// MIGRATION_BATCH2: default is unchanged original input and mathematical GPU API.\nconst std::string migration_case=std::getenv("MIGRATION_CASE")?std::getenv("MIGRATION_CASE"):"original";\n'+text[start:]
  runtime='hip' if backend=='rocm' else 'cuda'
  if source in SPARSE:
   kind=pathlib.PurePosixPath(source).parent.name
   if kind=='spvv':
    marker='    // Device memory management';code='if(migration_case=="changed-values"){for(auto& x:hX_values)x*=-0.5f;result*=-0.5f;}\n'+emit('input_X_indices','hX_indices','nnz')+emit('input_X','hX_values','nnz')+emit('input_Y','hY','size');text=text.replace(marker,code+marker)
    marker='    // device result check';text=text.replace(marker,emit('result','&tmp_result','1')+marker)
   else:
    marker='    // Device memory management';code=''
    if kind=='spgemm':code='if(migration_case=="changed-values"){alpha=-0.5f;for(auto& x:hC_values)x*=-0.5f;}\n'
    code+=emit('alpha','&alpha','1')
    for name in ['hA_csrOffsets','hA_columns','hA_values','hB_csrOffsets','hB_columns','hB_values']:code+=emit('input_'+name,name,'sizeof('+name+')/sizeof('+name+'[0])')
    text=text.replace(marker,code+marker)
    if kind=='spgemm_reuse':
     marker='    // update dA_values, dB_values';code=f'float migration_first[C_NUM_NNZ];CHECK_CUDA({runtime}Memcpy(migration_first,dC_values,sizeof(migration_first),{runtime}MemcpyDeviceToHost))\n'+emit('first_values','migration_first','C_NUM_NNZ')+'if(migration_case=="changed-values"){for(auto& x:hA_values)x*=2;for(auto& x:hC_values)x*=2;}\n';text=text.replace(marker,code+marker)
    marker='    // device result check';text=text.replace(marker,'if(C_nnz!=C_NUM_NNZ)return EXIT_FAILURE;\n'+marker)
    marker='    int correct = 1;';code=''
    for name in ['hC_csrOffsets_tmp','hC_columns_tmp','hC_values_tmp']:code+=emit(name,name,'sizeof('+name+')/sizeof('+name+'[0])')
    if marker not in text:marker='    int correct = 1';
    text=text.replace(marker,code+marker)
  elif source in BLAS:
   kind=pathlib.PurePosixPath(source).parent.name;input_code='';output_code=''
   if kind in ['amax','amin']:
    text=text.replace('const std::vector<data_type> A','std::vector<data_type> A')
    text=text.replace('cublasIdamax(cublasH, A.size(),','cublasIdamax(cublasH, migration_case=="empty"?0:A.size(),').replace('cublasIdamin(cublasH, A.size(),','cublasIdamin(cublasH, migration_case=="empty"?0:A.size(),').replace('hipblasIdamax(cublasH, A.size(),','hipblasIdamax(cublasH, migration_case=="empty"?0:A.size(),').replace('hipblasIdamin(cublasH, A.size(),','hipblasIdamin(cublasH, migration_case=="empty"?0:A.size(),')
    input_code='if(migration_case=="ties"){A={-4,4,1,-1};}\n'+emit('input_A','A.data()','A.size()');output_code=emit('result','&result','1')
   elif kind=='rotg':
    input_code='if(migration_case=="zero"){A=0;B=0;}if(migration_case=="negative"){A=-3;B=4;}\n'
    for v in ['A','B']:input_code+=emit('input_'+v,'&'+v,'1')
    for v in ['A','B','c','s']:output_code+=emit(v,'&'+v,'1')
   elif kind=='rotmg':
    input_code='if(migration_case=="zero"){Y=0;}if(migration_case=="negative"){A=-1;}if(migration_case=="rescale"){A=1e-20;B=2e-20;X=2;Y=1;}\n'
    for v in ['A','B','X','Y']:input_code+=emit('input_'+v,'&'+v,'1');output_code+=emit(v,'&'+v,'1')
    input_code+=emit('input_param','param.data()','param.size()');output_code+=emit('param','param.data()','param.size()')
   elif kind=='rotm':
    input_code='if(migration_case=="flag-minus2")param[0]=-2;if(migration_case=="flag-minus1")param[0]=-1;if(migration_case=="flag-zero")param[0]=0;\n'
    for v in ['A','B','param']:input_code+=emit('input_'+v,v+'.data()',v+'.size()');output_code+=emit(v,v+'.data()',v+'.size()')
   else:
    text=text.replace('const data_type alpha = 1.0;','const data_type alpha = migration_case=="negative-alpha"?-0.5:1.0;').replace('const data_type alpha_array[group_count] = {1.0, 1.0};','const data_type alpha_array[group_count] = {migration_case=="negative-alpha"?-0.5:1.0,migration_case=="negative-alpha"?-0.5:1.0};')
    for v in ['A','B']:
     input_code+=f'for(size_t i=0;i<{v}_array.size();++i)migration_observer::emit(("input_{v}_"+std::to_string(i)).c_str(),{v}_array[i].data(),{v}_array[i].size());\n'
    out='B' if kind=='trsmBatched' else 'C';output_code+=f'for(size_t i=0;i<{out}_array.size();++i)migration_observer::emit(("{out}_"+std::to_string(i)).c_str(),{out}_array[i].data(),{out}_array[i].size());\n'
   marker='    /* step 1:';assert marker in text,source;text=text.replace(marker,input_code+marker,1)
   marker='/* free resources */';assert marker in text,source;text=text.replace(marker,output_code+marker,1)
  # Tensor observation and additional shapes are prepared separately after batch 2a.
  if source in TENSOR:continue
  p.write_text(text)
# Preserve native CUDA helper code; no changes to original upstream files.
for family in ['cuBLAS','cuSOLVER']:
 src=ROOT/family/'utils';dst=ROOT/'build/cuda-observed'/family/'utils'
 if src.exists():shutil.copytree(src,dst,dirs_exist_ok=True)
(ROOT/'migration/batch2.json').write_text(json.dumps({'samples':[{'source':k,'required_cases':v,'initial_status':'PARTIAL'} for k,v in ALL.items()],'scope':'17 user-selected original profiles plus listed input cases; original GPU algorithms/APIs retained'},indent=2)+'\n')
print('Prepared observation/case adapters for sparse3 + BLAS8 + solver2')
