#!/usr/bin/env python3
"""Record actual image migration capabilities in the locked ROCm process."""
import ctypes,importlib,importlib.metadata,json,shutil,subprocess
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record

def main():
 e=Experiment('I0','image-AMD-environment','rocm-probe',sources=[__file__,ROOT/'tools/moat/snapshot.py']);observed=capture();write(e.path/'backend.observed.json',observed);libs=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_libraries/lib');core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core/lib');hip=ctypes.CDLL(str(core/'libamdhip64.so.7'));free=ctypes.c_size_t();total=ctypes.c_size_t();hip.hipSetDevice(0);rc=hip.hipMemGetInfo(ctypes.byref(free),ctypes.byref(total));packages={}
 for name in ['torch','torchvision','numpy','cv2','PIL']:
  try:
   m=importlib.import_module(name);packages[name]=dict(version=getattr(m,'__version__',None),file=getattr(m,'__file__',None),hip=getattr(getattr(m,'version',None),'hip',None))
  except Exception as error:packages[name]=dict(error=repr(error))
 candidates=[p for directory in [core,libs,Path('/opt/rocm/core-10.1/lib'),ROOT/'build/rocm-sdk-overlay/lib'] for p in directory.glob('librocjpeg.so*') if p.exists()];library=candidates[0] if candidates else None;jpeg=dict(searched=[str(core),str(libs),'/opt/rocm/core-10.1/lib',str(ROOT/'build/rocm-sdk-overlay/lib')])
 if library:
  lib=ctypes.CDLL(str(library));jpeg=dict(path=str(library),sha256=digest(library),symbols={n:hasattr(lib,n) for n in ['rocJpegCreate','rocJpegDestroy','rocJpegStreamCreate','rocJpegStreamParse','rocJpegGetDecoderCaps']})
  for backend in [0,1]:
   handle=ctypes.c_void_p();fn=lib.rocJpegCreate;fn.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.POINTER(ctypes.c_void_p)];fn.restype=ctypes.c_int;status=fn(backend,0,ctypes.byref(handle));jpeg['create_backend_'+str(backend)]=dict(status=status)
   if status==0:lib.rocJpegDestroy.argtypes=[ctypes.c_void_p];jpeg['create_backend_'+str(backend)]['destroy_status']=lib.rocJpegDestroy(handle)
 result=dict(environment=observed,memory=dict(return_code=rc,free=free.value,total=total.value),packages=packages,rocJPEG=jpeg,tools={n:shutil.which(n) for n in ['hipcc','cmake','pkg-config','rocprofv3','flang']},opencv_headers=Path('/usr/include/opencv4').exists(),record_type='capability observation; actual file decode is separate')
 write(e.path/'capabilities.json',result);ref=e.finish('OBSERVED');result['evidence']=ref;write(ROOT/'migration/reports/image-I0-AMD-environment.json',result);record('I0','锁定ROCm环境/允许设备及实际库、Python包、rocJPEG创建能力调查完成；这不是图像功能验收。',[ref]);print(json.dumps(result))
if __name__=='__main__':main()
