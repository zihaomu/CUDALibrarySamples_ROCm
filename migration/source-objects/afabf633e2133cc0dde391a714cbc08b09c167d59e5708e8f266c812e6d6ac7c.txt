#!/usr/bin/env python3
"""Build and smoke-run unchanged upstream sources; record exit-only evidence honestly."""
import datetime,json,os,pathlib,subprocess,sys
from run import ROOT, command, digest
specs=json.loads((ROOT/'migration/m1.json').read_text());out=ROOT/'artifacts'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')/'cuda-original';out.mkdir(parents=True)
results=[];env=os.environ.copy()
for spec in specs:
 d=out/spec['name'];d.mkdir();source=ROOT/spec['upstream_source'];binary=d/'original';family=spec['path'].split('/')[0]
 includes=[ROOT/family/'utils',ROOT/'cuBLASLt/Common',source.parent]
 sources=[str(source)]
 if family=='cuBLASLt':sources += [str(source.parent/'sample_cublasLt_LtSgemm.cu')]
 cmd=['/usr/local/cuda-13.4/bin/nvcc','-x','cu','-std=c++17','-O2','-arch=sm_120']+sources+['-o',str(binary)]+['-I'+str(x) for x in includes]+['-l'+x for x in spec['cuda_libraries']]
 (d/'commands.json').write_text(json.dumps({'build':cmd,'run':[str(binary)]},indent=2)+'\n');rc=command(cmd,ROOT,d/'build.log',env);stage='build'
 if rc==0:rc=command([str(binary)],ROOT,d/'run.log',env,60);stage='run'
 result={'source':spec['upstream_source'],'source_sha256':digest(source),'status':'PASSED' if rc==0 else 'FAILED','stage':stage,'return_code':rc,'correctness':'NOT_INDEPENDENTLY_VALIDATED','evidence':str(d.relative_to(ROOT))};(d/'summary.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result);print(spec['name'],stage,result['status'],flush=True)
p=ROOT/'migration/reports/cuda-original-latest.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({'results':results},indent=2)+'\n');print('Evidence:',out)
sys.exit(int(any(r['status']!='PASSED' for r in results)))
