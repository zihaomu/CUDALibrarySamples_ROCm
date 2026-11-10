#!/usr/bin/env python3
"""Retain native CUDA tensor operations; AMD uses explicit full-precision routes."""
import pathlib,re,shutil
from catalog import ROOT
from batches4_8_spec import GROUPS,kind
for source in GROUPS['b5']:
 k=kind(source);raw=(ROOT/source).read_text();license=raw.split('#include')[0]
 amd=ROOT/'rocm/ported'/source;amd.write_text(license+'// MIGRATION_BATCH5: full original tensor precision/extents and execution adapter.\n#include "batch5_tensor.hpp"\nint main(){return migration_batch::tensor_main("'+k+'");}\n')
 p=ROOT/'build/cuda-observed'/source;p.parent.mkdir(parents=True,exist_ok=True)
 s='#include "batch5_io.hpp"\n#include "observe.hpp"\n'+raw
 pos=s.index('{',s.index('int main'))+1;s=s[:pos]+'\n// MIGRATION_BATCH5\nconst std::string migration_case=batch5::selected_case();\n'+s[pos:]
 if k=='einsum':
  s=s.replace('    einsum(handle, {2, 4, 5}', '    einsum(handle, migration_Ashape').replace('{4, 8, 7}', 'migration_Bshape')
  marker='    einsum(handle, migration_Ashape';pos=s.index(marker);s=s[:pos]+'std::vector<int> migration_Ashape=migration_case=="non-square"?std::vector<int>{3,5,7}:std::vector<int>{2,4,5};\nstd::vector<int> migration_Bshape=migration_case=="non-square"?std::vector<int>{5,4,3}:std::vector<int>{4,8,7};\n'+s[pos:]
  marker='    auto ret = myEinsum.execute';pos=s.index(marker);code='''static int migration_operation=0;int migration_id=migration_operation++;
std::vector<float> migration_A(totalElementsA),migration_B(totalElementsB);
batch5::input("A"+std::to_string(migration_id),migration_A.data(),migration_A.size());batch5::input("B"+std::to_string(migration_id),migration_B.data(),migration_B.size());
handle_error(cudaMemcpy(A_raw.get(),migration_A.data(),migration_A.size()*sizeof(float),cudaMemcpyHostToDevice));
handle_error(cudaMemcpy(B_raw.get(),migration_B.data(),migration_B.size()*sizeof(float),cudaMemcpyHostToDevice));
''';s=s[:pos]+code+s[pos:]
  marker='    if (!ret)';pos=s.index(marker);code='''if(!ret)throw std::runtime_error("native einsum execution failed");
handle_error(cudaDeviceSynchronize());std::vector<float> migration_result(totalElementsC);handle_error(cudaMemcpy(migration_result.data(),output_raw.get(),migration_result.size()*sizeof(float),cudaMemcpyDeviceToHost));batch5::snapshot("output"+std::to_string(migration_id),migration_result);
std::vector<std::string> migration_am={"ijn","ijn","nij","nij","nij"},migration_bm={"jmk","jmk","","",""},migration_cm={"inkm","ikmn","ijn","ijn","ji"};
std::unordered_map<int,int64_t> migration_extents;
for(size_t i=0;i<A_shape.size();++i)migration_extents[migration_am[migration_id][i]]=A_shape[i];
for(size_t i=0;i<B_shape.size();++i)migration_extents[migration_bm[migration_id][i]]=B_shape[i];
std::reverse(migration_am[migration_id].begin(),migration_am[migration_id].end());std::reverse(migration_bm[migration_id].begin(),migration_bm[migration_id].end());std::reverse(migration_cm[migration_id].begin(),migration_cm[migration_id].end());
batch5::config("einsum",batch5::modes(migration_am[migration_id]),batch5::modes(migration_bm[migration_id]),batch5::modes(migration_cm[migration_id]),{},migration_extents,1,0,",\\"operation\\":"+std::to_string(migration_id));
std::ifstream migration_cfg(batch2_tensor::output_path("tensor5.json"));std::ofstream migration_saved(batch2_tensor::output_path("tensor5-"+std::to_string(migration_id)+".json"));migration_saved<<migration_cfg.rdbuf();
''';s=s[:pos]+code+s[pos:]
 else:
  for name in ['A','B','C','D']:
   pattern=r'std::generate\('+name+r'\.get\(\),'+name+r'\.get\(\)\+elements'+name+r',\s*randomgen<floatType'+name+r'>\(\)\s*\);'
   s=re.sub(pattern,f'batch5::input("{name}",{name}.get(),elements{name});',s)
  if k=='elementwise_permute_padding':
   marker='    std::vector<int64_t> extentA;';pos=s.index(marker);code='''if(migration_case!="original"){extent['h']=3;extent['w']=5;extent['c']=7;extent['n']=2;paddingLeft['h']=2;paddingRight['h']=1;paddingLeft['w']=1;paddingRight['w']=2;}
std::vector<int64_t> migration_as(4),migration_cs(4),migration_left(4),migration_right(4);int64_t migration_a_stride=1,migration_c_stride=1;
for(int i=0;i<4;++i){migration_as[i]=migration_a_stride;migration_a_stride*=extent[modeA[i]];migration_cs[i]=migration_c_stride;migration_left[i]=paddingLeft[modeC[i]];migration_right[i]=paddingRight[modeC[i]];migration_c_stride*=extent[modeC[i]]+migration_left[i]+migration_right[i];}
if(migration_case=="small-strided"){migration_as[0]=2;for(int i=1;i<4;++i)migration_as[i]=migration_as[i-1]*extent[modeA[i-1]]+3;}
''';s=s[:pos]+code+s[pos:]
   marker='    size_t sizeA =';pos=s.index(marker);s=s[:pos]+'''elementsA=1;elementsC=1;for(int i=0;i<4;++i){elementsA+=(extent[modeA[i]]-1)*migration_as[i];elementsC+=(extent[modeC[i]]+migration_left[i]+migration_right[i]-1)*migration_cs[i];}
'''+s[pos:]
   s=s.replace('nullptr /* stride */,\n                                                typeA','migration_as.data(),\n                                                typeA')
   s=s.replace('nullptr /* stride */,\n                                                typeC','migration_cs.data(),\n                                                typeC')
   config='batch5::config("'+k+'",modeA,{},modeC,{},extent,alpha,0,",\\"stridesA\\":"+batch5::numbers(migration_as)+",\\"stridesC\\":"+batch5::numbers(migration_cs)+",\\"left\\":"+batch5::numbers(migration_left)+",\\"right\\":"+batch5::numbers(migration_right));\n'
  else:
   sizes={'m':5,'a':3,'b':2,'n':4,'r':3,'k':2,'i':3,'j':7} if k=='contraction_trinary' else {'m':5,'n':3,'u':4,'v':2,'h':7,'k':2}
   marker='    std::vector<int64_t> extent';pos=s.index(marker);s=s[:pos]+'if(migration_case!="original"){'+''.join(f"extent['{key}']={v};" for key,v in sizes.items())+'}\n'+s[pos:]
   s=s.replace('floatTypeCompute alpha = (floatTypeCompute)1.1f;', 'floatTypeCompute alpha = migration_case=="original"?1.1f:migration_case=="small-zero-alpha"?0.f:-.75f;').replace('floatTypeCompute beta  = (floatTypeCompute)0.f;', 'floatTypeCompute beta = migration_case=="original"?0.f:.5f;')
   config=f'batch5::config("{k}",modeA,modeB,modeC,'+('modeD' if k=='contraction_trinary' else 'std::vector<int>{}')+',extent,alpha,beta);\n'
   if k=='contraction_plan_cache':
    s=s.replace('const char planCacheFilename[] = "./planCache.bin";', 'const std::string migration_cache_file=batch2_tensor::output_path("planCache.bin");\n    const char* planCacheFilename=migration_cache_file.c_str();')
    marker='    if (status == CUTENSOR_STATUS_IO_ERROR)';pos=s.index(marker);s=s[:pos]+'migration_observer::emit("cache_read_status",reinterpret_cast<int*>(&status),1);\n'+s[pos:]
    marker='    status = cutensorHandleWritePlanCacheToFile(handle, planCacheFilename);';s=s.replace(marker,marker+'\nmigration_observer::emit("cache_write_status",reinterpret_cast<int*>(&status),1);')
  target='D' if k=='contraction_trinary' else 'C';capture=f'handle_error(cudaDeviceSynchronize());std::vector<float> migration_output(elements{target});handle_error(cudaMemcpy(migration_output.data(),{target}_d.get(),size{target},cudaMemcpyDeviceToHost));batch5::snapshot("output",migration_output);\n'+config
  s=s.replace('    return EXIT_SUCCESS;',capture+'    return EXIT_SUCCESS;',1)
 p.write_text(s)
shutil.copyfile(ROOT/'cuTENSOR/utils.cuh',ROOT/'build/cuda-observed/cuTENSOR/utils.cuh')
print('Prepared four B5 original native CUDA profiles and AMD adapters')
