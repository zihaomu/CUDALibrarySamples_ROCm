#!/usr/bin/env python3
"""Reject excluded/reserved physical GPUs before experiment allocations."""
import ctypes,json,os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
def allowed_devices(require_idle=False):
 if os.environ.get('DEEPINFER_ROCM_RELEASE')!='10.1.0':raise RuntimeError('ROCm 10.1.0 foundation required')
 mapping=json.loads((ROOT/'migration/environments/physical-device-map.json').read_text())
 entries=mapping if isinstance(mapping,list) else mapping.get('gpu_data',mapping.get('gpu_list',[]))
 if not entries:
  # Preserve the complete source for auditing if the CLI schema changes.
  raise RuntimeError('unrecognized physical GPU map schema')
 known={}
 for e in entries:
  pci=e.get('bdf',e.get('pci_bdf',e.get('pci',{}).get('bdf','')))
  if pci:known[pci.lower()[-12:]]=int(e['gpu'])
 lib=ctypes.CDLL('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core/lib/libamdhip64.so.7');n=ctypes.c_int();rc=lib.hipGetDeviceCount(ctypes.byref(n))
 if rc:raise RuntimeError('hipGetDeviceCount '+str(rc))
 reservation=ROOT.parents[1]/'deepinfer_workspace/artifacts/amd/rocm10/gpu-reservation.json';reserved=[]
 if reservation.exists():
  r=json.loads(reservation.read_text())
  if r.get('status')=='active':reserved=r.get('physical_gpus',[])
 result=[]
 for i in range(n.value):
  b=ctypes.create_string_buffer(64);rc=lib.hipDeviceGetPCIBusId(b,len(b),i)
  if rc:raise RuntimeError('hipDeviceGetPCIBusId '+str(rc))
  pci=b.value.decode().lower()[-12:];physical=known.get(pci)
  if physical is None:raise RuntimeError('unmapped PCI GPU '+pci)
  if physical==3 or physical in reserved:raise RuntimeError(f'physical GPU{physical} at {pci} is excluded/reserved')
  if require_idle:
   lib.hipSetDevice(i);free=ctypes.c_size_t();total=ctypes.c_size_t();rc=lib.hipMemGetInfo(ctypes.byref(free),ctypes.byref(total))
   busy_path=pathlib.Path('/sys/bus/pci/devices')/pci/'gpu_busy_percent';busy=int(busy_path.read_text()) if busy_path.exists() else None
   if rc or free.value<.9*total.value or busy is None or busy>2:raise RuntimeError(f'physical GPU{physical} is occupied; free={free.value}/{total.value}, busy={busy}; timing is unqualified')
  result.append({'logical_id':i,'pci_bdf':pci,'physical_id':physical})
 return result
if __name__=='__main__':print(json.dumps(allowed_devices(),indent=2))
