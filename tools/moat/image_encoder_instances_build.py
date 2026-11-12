#!/usr/bin/env python3
"""Build original nvJPEG encoder entrypoint against project HIP implementation."""
import json
from pathlib import Path
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

REPORT=ROOT/'migration/reports/image-jpeg-encoder-instances-build.json'
def main():
 profile=ROOT/'migration/rewrite/image-jpeg-encoder-instances-profile.json'
 if json.loads(profile.read_text())['status']!='FROZEN':raise ValueError('frozen profile required')
 src=ROOT/'rocm/ported/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp'
 headers=[ROOT/'rocm/common/image/jpeg_encoder_instances.hpp',ROOT/'rocm/common/image/jpeg_encoder_gpu.hpp',
          ROOT/'rocm/common/image/jpeg_full_gpu.hpp',ROOT/'rocm/common/image/jpeg_entropy_gpu.hpp']
 jpeg=ROOT/'build/cpu-codecs';core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay'
 deps=[src,*headers,profile,ROOT/'migration/rewrite/image-jpeg-encoder-instances-full-gpu-profile.json',
       jpeg/'include/jpeglib.h',jpeg/'lib/libjpeg.so.62.4.0']
 e=Experiment('I5','original-nvJPEG-Encoder-MultipleInstances-GPU-build','rocm-build',sources=[__file__,*deps]);write(e.path/'backend.observed.json',capture())
 binary=e.path/'sample';cmd=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
  '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201',
  '-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-x','hip',str(src),'-o',str(binary),
  '-I'+str(ROOT/'rocm/common'),'-I'+str(jpeg/'include'),'-I'+str(core/'include'),
  '-L'+str(jpeg/'lib'),'-L'+str(core/'lib'),'-Wl,-rpath,'+str(jpeg/'lib'),
  '-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-ljpeg']
 rc=e.command(cmd,'build-original-nvJPEG-encoder',timeout=300)
 result=dict(status='BUILT' if rc==0 else 'BUILD_ERROR',return_code=rc,
  binary=str(binary.relative_to(ROOT)) if rc==0 else None,
  binary_sha256=digest(binary) if rc==0 else None,
  dependencies={str(p.relative_to(ROOT)):digest(p) for p in deps},experiment_id=e.id)
 write(e.path/'build.json',result);result['evidence']=e.finish('EXECUTED' if rc==0 else 'BUILD_ERROR',dict(status=result['status'],checks=[dict(check='original-entry-hipcc-build',passed=rc==0)]));write(REPORT,result)
 record('I5','nvJPEG 多实例原始 C++ 入口接入 HIP encoder 编译：'+result['status']+'；七组原生 CLI 合同待跑。',[result['evidence']]);print(result['status'],result['evidence']);return int(rc!=0)
if __name__=='__main__':raise SystemExit(main())
