#!/usr/bin/env python3
"""Build GPU Huffman baseline JPEG bit-generation prototype."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,digest,write
from image_progress import record
from snapshot import capture
SOURCE=ROOT/'rocm/probes/image/jpeg_huffman_gpu.hip'
PROFILE=ROOT/'migration/rewrite/image-jpeg-encoder-entropy-profile.json'
REPORT=ROOT/'migration/reports/image-jpeg-encoder-entropy-build.json'
def main():
 profile=json.loads(PROFILE.read_text());core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core')
 jpeg=ROOT/'build/cpu-codecs';overlay=ROOT/'build/rocm-sdk-overlay'
 deps=[SOURCE,PROFILE,jpeg/'include/jpeglib.h',jpeg/'lib/libjpeg.so.62.4.0']
 e=Experiment('I5','GPU-Huffman-baseline-JPEG-build','rocm-build',sources=[__file__,*deps],parent=profile['evidence'].split('/')[-1]);write(e.path/'backend.observed.json',capture())
 binary=e.path/'jpeg_huffman_gpu';cmd=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
  '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201',
  '-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-I'+str(jpeg/'include'),'-x','hip',
  str(SOURCE),'-L'+str(core/'lib'),'-L'+str(jpeg/'lib'),'-Wl,-rpath,'+str(core/'lib'),
  '-Wl,-rpath,'+str(jpeg/'lib'),'-lamdhip64','-ljpeg','-o',str(binary)]
 rc=e.command(cmd,'build-GPU-baseline-Huffman',timeout=300)
 result=dict(status='BUILT' if rc==0 else 'BUILD_ERROR',return_code=rc,binary=str(binary.relative_to(ROOT)) if rc==0 else None,
  binary_sha256=digest(binary) if rc==0 else None,dependencies={str(p.relative_to(ROOT)):digest(p) for p in deps},experiment_id=e.id)
 write(e.path/'build.json',result);result['evidence']=e.finish('EXECUTED' if rc==0 else 'BUILD_ERROR',dict(status=result['status'],checks=[dict(check='HIP-Huffman-build',passed=rc==0)]));write(REPORT,result)
 record('I5','GPU baseline JPEG Huffman bitstream 原型编译：'+result['status']+'；两条冻结码流尚待逐字节验收。',[result['evidence']]);print(result['status'],result['evidence']);return int(rc!=0)
if __name__=='__main__':raise SystemExit(main())
