"""Read-only SDK identity and dependency inspection inside the locked foundation."""
import ctypes, hashlib, json, os, pathlib, shutil, subprocess
p = pathlib.Path(__file__).resolve().parents[2]
root = pathlib.Path('/opt/venv/lib/python3.13/site-packages')
libs = root / '_rocm_sdk_libraries'
core = root / '_rocm_sdk_core'
names = ['hipblas','rocblas','hipblaslt','hipsparse','rocsparse','hipsolver','rocsolver','hipfft','rocfft','hiprand','rocrand','hipsparselt','hiptensor','rocjpeg']
out = {'schema_version':1,'rocm_release':os.getenv('DEEPINFER_ROCM_RELEASE'),'image_id':os.getenv('DEEPINFER_IMAGE_ID'),'hip_visible_devices':os.getenv('HIP_VISIBLE_DEVICES'),'sdk_core':str(core),'sdk_libraries':str(libs),'libraries':{}}
for name in names:
 paths = sorted((libs/'lib').glob('lib'+name+'.so*'))
 info = {'present':bool(paths)}
 if paths:
  q=paths[0].resolve(); info.update(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest())
  try: ctypes.CDLL(str(q)); info['loadable']=True
  except OSError as e: info.update(loadable=False,error=str(e))
 out['libraries'][name]=info
for name in ['hipcc','amdclang++','cmake','hipify-perl','hipify-clang']:
 q=shutil.which(name);out[name]={'path':q}
 if q: out[name]['version']=subprocess.run([q,'--version'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT).stdout[:2500]
try:
 import torch
 out['devices']=[{'logical_id':i,'name':torch.cuda.get_device_name(i),'properties':str(torch.cuda.get_device_properties(i))} for i in range(torch.cuda.device_count())]
except Exception as e: out['device_query_error']=str(e)
out['native_math_headers']={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in pathlib.Path('/opt/rocm/core-10.1/include').glob('*/*version*.h')}
q=p/'migration/environments/amd-rocm10-inspection.json';q.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
