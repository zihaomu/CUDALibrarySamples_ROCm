#!/usr/bin/env python3
"""Observe actual default, live and destroyed HIP stream queries in ROCm 10.1."""
import ctypes as C,json,sys
from pathlib import Path
from experiment import ROOT,Experiment,write
from snapshot import capture
from image_progress import record
def child(output):
 import _rocm_sdk_core
 hip=C.CDLL(str(Path(_rocm_sdk_core.__file__).parent/'lib/libamdhip64.so.7'));s=C.c_void_p();hip.hipStreamCreateWithFlags.argtypes=[C.POINTER(C.c_void_p),C.c_uint];hip.hipStreamGetDevice.argtypes=[C.c_void_p,C.POINTER(C.c_int)];hip.hipStreamGetFlags.argtypes=[C.c_void_p,C.POINTER(C.c_uint)];hip.hipStreamDestroy.argtypes=[C.c_void_p];device=C.c_int();flags=C.c_uint();rows=[]
 rows.append(dict(case='default',get_flags=hip.hipStreamGetFlags(None,C.byref(flags)),get_device=hip.hipStreamGetDevice(None,C.byref(device)),device=device.value))
 rc=hip.hipStreamCreateWithFlags(C.byref(s),1);assert rc==0;rows.append(dict(case='live',get_flags=hip.hipStreamGetFlags(s,C.byref(flags)),get_device=hip.hipStreamGetDevice(s,C.byref(device)),device=device.value));rc=hip.hipStreamDestroy(s);assert rc==0;rows.append(dict(case='destroyed',get_device=hip.hipStreamGetDevice(s,C.byref(device))));Path(output).write_text(json.dumps(rows,indent=2)+'\n');print(rows)
def main():
 if len(sys.argv)>1:child(sys.argv[1]);return 0
 e=Experiment('I2','CCL-default-and-invalid-stream-API-observation','rocm-probe',sources=[__file__]);write(e.path/'backend.observed.json',capture());rc=e.command([sys.executable,__file__,str(e.path/'queries.json')],'actual-default-live-destroyed-stream-queries');ref=e.finish('OBSERVED' if not rc else 'PROBE_FAILED');write(ROOT/'migration/reports/image-ccl-stream-query-research.json',dict(return_code=rc,evidence=ref));record('I2','ROCm10.1实际默认/有效/销毁stream查询探针rc='+str(rc)+'；生产预检改为GetDevice并核对当前设备，默认流与外设备流将单独验收。',[ref]);print(ref);return rc
if __name__=='__main__':raise SystemExit(main())
