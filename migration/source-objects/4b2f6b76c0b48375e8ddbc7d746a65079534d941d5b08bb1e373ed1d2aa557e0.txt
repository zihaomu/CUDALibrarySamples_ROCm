#!/usr/bin/env python3
"""Run both original cuSPARSELt FP16 programs with readback instrumentation."""
import json,shlex,shutil,tarfile
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
sdk=ROOT/'build/sparseLt-sdk/nvidia/cu13';host='nvidia-5090x2';results=[]
helper='''
#include <fstream>
#include <string>
#include <algorithm>
#include <stdexcept>
template<class T> void original_dump(const char*name,const T*data,size_t count){const char*root=std::getenv("REWRITE_OUTPUT");if(!root)throw std::runtime_error("REWRITE_OUTPUT required");std::ofstream out(std::string(root)+"/"+name+".bin",std::ios::binary);out.write(reinterpret_cast<const char*>(data),count*sizeof(T));if(!out)throw std::runtime_error("write failed");}
'''
for advanced in [False,True]:
 kind='matmul_advanced' if advanced else 'matmul';original=ROOT/f'cuSPARSELt/{kind}/{kind}_example.cpp';e=Experiment('R7','cuSPARSELt/'+kind,'cuda-original',case='original',sources=[__file__,original]);text=original.read_text();text=helper+text;allocation='    auto     hC             = new C_t[C_size]();' if advanced else '    auto     hC             = new C_t[C_size / sizeof(C_t)];';assert text.count(allocation)==1;text=text.replace(allocation,allocation+'\n    std::srand(1);'+('\n    std::fill(hA,hA+A_size,AB_t(0.0f));std::fill(hB,hB+B_size,AB_t(0.0f));' if advanced else ''))
 marker='    CHECK_CUDA( cudaMemcpy(dA, hA,';assert text.count(marker)==1;counts=('A_size','B_size','C_size') if advanced else ('A_size/sizeof(AB_t)','B_size/sizeof(AB_t)','C_size/sizeof(C_t)');text=text.replace(marker,'    original_dump("A",hA,'+counts[0]+');original_dump("B",hB,'+counts[1]+');original_dump("C",hC,'+counts[2]+');\n'+marker)
 if advanced:
  marker='    CHECK_CUDA( cudaMemcpy(dBias, hBias,';assert text.count(marker)==1;text=text.replace(marker,'    original_dump("bias",hBias,m);\n'+marker)
 for name,needle,count in [('A_pruned','    CHECK_CUDA( cudaMemcpy(hA, dA, '+('A_size_bytes' if advanced else 'A_size')+', cudaMemcpyDeviceToHost) )',counts[0]),('D','    CHECK_CUDA( cudaMemcpy(hC, '+('dC, C_size_bytes' if advanced else 'dD, C_size')+', cudaMemcpyDeviceToHost) )',counts[2])]:
  assert text.count(needle)==1,needle;text=text.replace(needle,needle+'\n    original_dump("'+name+'",'+('hA' if name=='A_pruned' else 'hC')+','+count+');')
 src=e.path/(kind+'.cu');src.write_text(text);write(e.path/'SDK.json',dict(version='0.10.0',header_sha256=digest(sdk/'include/cusparseLt.h'),library_sha256=digest(sdk/'lib/libcusparseLt.so.0'),original_sha256=digest(original),instrumented_sha256=digest(src),instrumentation='D2H outputs; srand(1); define inactive A/B padding as zero, original active generation and GPU algorithm unchanged'));bundle=e.path/'original.tar.gz'
 with tarfile.open(bundle,'w:gz') as f:
  f.add(src,arcname=kind+'.cu');f.add(sdk/'include',arcname='sdk/include');f.add(sdk/'lib/libcusparseLt.so.0',arcname='sdk/lib/libcusparseLt.so.0')
 remote='/tmp/'+e.id;steps=[(['ssh',host,shlex.join(['mkdir','-p',remote+'/outputs'])],'prepare'),(['scp',str(bundle),host+':'+remote+'/original.tar.gz'],'upload'),(['ssh',host,shlex.join(['tar','-xzf',remote+'/original.tar.gz','-C',remote])],'unpack'),(['ssh',host,shlex.join(['/usr/local/cuda-13.4/bin/nvcc','-std=c++17','-O2','-arch=sm_120',remote+'/'+kind+'.cu','-I'+remote+'/sdk/include','-L'+remote+'/sdk/lib','-Xlinker','-rpath='+remote+'/sdk/lib','-l:libcusparseLt.so.0','-o',remote+'/original'])],'native-original-build'),(['ssh',host,'REWRITE_OUTPUT='+shlex.quote(remote+'/outputs')+' '+shlex.quote(remote+'/original')],'native-original-run')];rc=0
 for argv,phase in steps:
  rc=e.command(argv,phase,timeout=240)
  if rc:break
 out=e.path/'outputs';out.mkdir();collect=e.command(['scp','-r',host+':'+remote+'/outputs/.',str(out)],'collect');r=dict(profile=kind,kind='sparse24_advanced' if advanced else 'sparse24',return_code=rc,collection_return_code=collect,output=str(out.relative_to(ROOT)),experiment_id=e.id,remote=remote,original_sha256=digest(original),instrumented_sha256=digest(src),sdk_version='0.10.0',scope='actual original FP16 cuSPARSELt harness with output-only instrumentation and defined inactive padding')
 r['evidence']=e.finish('EXECUTED' if rc==0 and collect==0 else 'NATIVE_SDK_FAILED');results.append(r);write(ROOT/'migration/reports/rewrite-sparse24-original-cuda.json',dict(profiles=results));print(kind,rc,collect,flush=True)
