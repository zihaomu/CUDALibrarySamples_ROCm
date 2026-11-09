#!/usr/bin/env python3
"""Record actual frontend/import failures for every non-C++ entrypoint.
No CPU fallback or import alias is counted as AMD implementation.
"""
import ast,datetime,fcntl,json,os,pathlib,re,shutil,subprocess
from catalog import ROOT
from device_guard import allowed_devices
from run import command,digest
from progress import checkpoint
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'artifacts'/stamp/'languages';out.mkdir(parents=True);env=os.environ.copy();identity={'devices':allowed_devices(),'image_id':env.get('DEEPINFER_IMAGE_ID'),'rocm_release':env.get('DEEPINFER_ROCM_RELEASE')};(out/'environment.json').write_text(json.dumps(identity,indent=2)+'\n');cat=json.loads((ROOT/'migration/samples.yaml').read_text());results=[]
# Qualify the available Fortran C ABI independently from proprietary SDK modules.
d=out/'iso-c-hip';d.mkdir();src=ROOT/'rocm/probes/fortran_hip.f90';lib=pathlib.Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core/lib');cmd=['/opt/rocm/core-10.1/lib/llvm/bin/flang',str(src),str(lib/'libamdhip64.so.7'),'-Wl,-rpath,'+str(lib),'-o',str(d/'probe')];(d/'commands.json').write_text(json.dumps(cmd));rc=command(cmd,ROOT,d/'build.log',env,60)
if rc==0:rc=command([str(d/'probe')],ROOT,d/'run.log',env,30)
results.append({'id':'fortran-hip-c-abi-probe','return_code':rc,'evidence':str(d.relative_to(ROOT))});print('Fortran C ABI probe:',rc,flush=True)
for s in cat['samples']:
 suffix=pathlib.Path(s['source']).suffix
 if suffix not in {'.py','.f90','.cuf'}:continue
 if s['status']=='PASSED':continue
 d=out/s['source'].replace('/','_');d.mkdir();src=ROOT/s['source'];body=src.read_text();dst=ROOT/'rocm/ported'/s['source'];dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(body)
 if suffix=='.py':
  tree=ast.parse(body);imports=[]
  for node in tree.body:
   if isinstance(node,ast.Import):imports += [a.name for a in node.names]
   elif isinstance(node,ast.ImportFrom) and node.module:imports.append(node.module)
  code='import importlib\n'+''.join('importlib.import_module('+repr(x)+')\n' for x in imports)+'print("IMPORTS_RESOLVED_ONLY_NOT_GPU_VALIDATION")\n';cmd=['python','-c',code];rc=command(cmd,src.parent,d/'build.log',env,30);reason='Python 原始入口依赖 '+', '.join(imports)+'；锁定 AMD 环境中的 import 资格检查未通过，尚无保留该例 API/算法的 AMD Python 改写。安装 CPU 包不能充作 GPU 迁移。'
 else:
  cmd=['/opt/rocm/core-10.1/lib/llvm/bin/flang','-cpp','-fsyntax-only','-x','f95',str(dst)];rc=command(cmd,d,d/'build.log',env,30);uses=re.findall(r'^\s*use\s+(\w+)',body,re.I|re.M);reason='Fortran 原始入口使用 '+', '.join(dict.fromkeys(uses))+'；当前 flang 编译失败，CUDA/cuDSS/cuFFT/NVFortran module 和 device 语法需用经验证的 ISO_C_BINDING 与 AMD API 重写。C ABI 探针另记，不代表该例已实现。'
 if rc==0:reason='原始 import/前端资格检查通过，但原始 GPU 测试所需的 AMD 可执行文件/绑定尚未实现，不能据此报告 GPU 成功。'
 (d/'commands.json').write_text(json.dumps({'build_or_import':cmd,'cwd':str(src.parent)},indent=2)+'\n');log=(d/'build.log').read_text(errors='replace');result={'sample_id':s['id'],'scope':'language_frontend_and_binding_attempt','status':'FAILED' if rc else 'BLOCKED','level':'L0','return_code':rc,'reason_code':'BINDING_OR_FRONTEND_MIGRATION_REQUIRED' if rc else 'ENV_MISSING_DEP','reason':reason+' 日志：'+log[-500:].replace('\n',' '),'implementation':None,'attempted_source':str(dst.relative_to(ROOT)),'attempted_source_sha256':digest(dst),'source_sha256':s['source_sha256'],'evidence':str(d.relative_to(ROOT)),'environment':str((out/'environment.json').relative_to(ROOT))};(d/'summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 with (ROOT/'migration/.state.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);p=ROOT/'migration/samples.yaml';current=json.loads(p.read_text());row=next(v for v in current['samples'] if v['id']==s['id']);row.update({k:result[k] for k in ['status','level','reason_code','reason','implementation']});row['attempts'].append(result);row['evidence'].append(result['evidence']);p.write_text(json.dumps(current,indent=2,ensure_ascii=False)+'\n')
 results.append(result);print(s['source'],rc,flush=True)
(ROOT/'migration/reports/languages.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n');checkpoint('S26 Fortran/Python 入口实际资格与改写尝试',f'{len(results)-1} 个非 C++ 入口均保留独立命令/编译或 import 错误；Fortran ISO_C_BINDING 到 HIP GPU 内存往返返回码 {results[0]["return_code"]}。未将 CPU 路线记为成功。','继续逐功能后端验证与差异说明')
