#!/usr/bin/env python3
"""Retain original tensor API/precision/extents; capture inputs and complete outputs."""
import pathlib,re,shutil
from catalog import ROOT
from batch2_spec import TENSOR
for source in TENSOR:
 for backend in ['rocm','cuda']:
  root=ROOT/('rocm/ported' if backend=='rocm' else 'build/cuda-observed');p=root/source
  if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source,p)
  s=p.read_text()
  if 'MIGRATION_BATCH2_TENSOR' in s:continue
  kind=pathlib.PurePosixPath(source).stem;runtime='hip' if backend=='rocm' else 'cuda';s='#include "batch2_tensor_io.hpp"\n'+s
  marker='    std::vector<int64_t> extent';pos=s.index(marker)
  sizes={'a':5,'b':3,'c':7} if kind.startswith('elementwise_') and kind!='elementwise_permute' else {'h':3,'w':5,'c':7,'n':2} if kind=='elementwise_permute' else {'m':5,'v':3,'h':7,'k':2}
  code='// MIGRATION_BATCH2_TENSOR: unchanged original profile is the default.\nconst std::string migration_case=std::getenv("MIGRATION_CASE")?std::getenv("MIGRATION_CASE"):"original";\nif(migration_case!="original"){'+''.join(f"extent['{k}']={v};" for k,v in sizes.items())+'alpha=migration_case=="small-zero"?0.f:-.75f;'
  if kind in ['reduction','elementwise_trinary']:code+='beta=migration_case=="small-zero"?-.5f:.5f;'
  if kind in ['elementwise_binary','elementwise_trinary']:code+='gamma=migration_case=="small-zero"?.25f:1.25f;'
  code+='}\n';s=s[:pos]+code+s[pos:]
  pos=s.index('    handle_error('+runtime+'Memcpy');inputs=['A','C']+(['B'] if kind=='elementwise_trinary' else []);capture=''.join(f'batch2_tensor::input("{v}",{v}.get(),elements{v});\n' for v in inputs);b='modeB' if kind=='elementwise_trinary' else 'std::vector<int>{}';beta='beta' if kind in ['reduction','elementwise_trinary'] else '0.';gamma='gamma' if kind in ['elementwise_binary','elementwise_trinary'] else '0.';capture+=f'batch2_tensor::config(modeA,{b},modeC,extent,alpha,{beta},{gamma});\n';s=s[:pos]+capture+s[pos:]
  target='D_d' if kind=='elementwise_trinary' else 'C_d';capture=f'handle_error({runtime}DeviceSynchronize());\nstd::vector<float> migration_output(elementsC);\nhandle_error({runtime}Memcpy(migration_output.data(),{target}.get(),sizeC,{runtime}MemcpyDeviceToHost));\nbatch2_tensor::snapshot("output",migration_output.data(),migration_output.size());\n'
  s=s.replace('    return EXIT_SUCCESS;',capture+'    return EXIT_SUCCESS;',1);p.write_text(s)
shutil.copyfile(ROOT/'cuTENSOR/utils.cuh',ROOT/'build/cuda-observed/cuTENSOR/utils.cuh')
print('Prepared 4 tensor observation adapters for both backends')
