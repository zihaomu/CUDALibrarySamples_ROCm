#!/usr/bin/env python3
"""Native NPP on exactly the project image fixtures; independent of compatible CUDA kernels."""
import json,datetime,os,pathlib,subprocess,hashlib
from catalog import ROOT
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');d=ROOT/'artifacts'/stamp/'batch15-native-npp';d.mkdir(parents=True);source=ROOT/'tools/migration/probes/batch15_native_cuda.cu';binary=d/'sample';cmd=['/usr/local/cuda-13.4/bin/nvcc','-std=c++17','-O2','-arch=sm_120','-I'+str(ROOT/'rocm/common'),str(source),'-o',str(binary),'-lnppif','-lnppist','-lnppisu','-lnppc','-lcublas'];(d/'commands.json').write_text(json.dumps(cmd,indent=2)+'\n');r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=180);(d/'build.log').write_text(r.stdout+r.stderr);rows=[]
if not r.returncode:
 for kind in ['canny','ncc','distance']:
  for case in ['original','irregular','changed-values','boundary','repeat','singular-or-empty']:
   out=d/kind/case;out.mkdir(parents=True);env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',MIGRATION_CASE=case,MIGRATION_OUTPUT_DIR=str(out));run=[str(binary),kind];(out/'commands.json').write_text(json.dumps(run,indent=2)+'\n')
   try:x=subprocess.run(run,cwd=ROOT,env=env,text=True,capture_output=True,timeout=120);(out/'run.log').write_text(x.stdout+x.stderr);rc=x.returncode
   except subprocess.TimeoutExpired:rc=124;(out/'run.log').write_text('TIMEOUT\n')
   rows.append(dict(kind=kind,case=case,return_code=rc,evidence=str(out.relative_to(ROOT))));print(kind,case,rc,flush=True)
(ROOT/'migration/reports/batch15-native-npp.json').write_text(json.dumps(dict(build_return_code=r.returncode,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),evidence=str(d.relative_to(ROOT)),runs=rows),indent=2)+'\n')
