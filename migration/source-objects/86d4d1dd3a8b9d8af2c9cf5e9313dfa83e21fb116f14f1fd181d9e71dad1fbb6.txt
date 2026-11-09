#!/usr/bin/env python3
"""CUDA-side prerequisite checks for non-C++ original entrypoints."""
import ast,datetime,json,os,pathlib,shutil,subprocess
from catalog import ROOT
from run import command
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'artifacts'/stamp/'cuda-language-prerequisites';out.mkdir(parents=True);cat=json.loads((ROOT/'migration/samples.yaml').read_text());env=os.environ.copy();results=[]
identity={'host':'nvidia-5090x2','cuda_root':'/usr/local/cuda-13.4','compilers':{x:shutil.which(x) for x in ['nvfortran','gfortran','flang']},'scope':'Prerequisite checks only; GPU baseline not executed'};(out/'environment.json').write_text(json.dumps(identity,indent=2)+'\n')
for s in cat['samples']:
 src=ROOT/s['source']
 if src.suffix not in {'.py','.f90','.cuf'}:continue
 d=out/s['source'].replace('/','_');d.mkdir();body=src.read_text();rc=0;commands=[]
 if src.suffix=='.py':
  imports=[]
  for node in ast.parse(body).body:
   if isinstance(node,ast.Import):imports.extend(a.name for a in node.names)
   elif isinstance(node,ast.ImportFrom) and node.module:imports.append(node.module)
  code='import importlib\n'+''.join('importlib.import_module('+repr(x)+')\n' for x in imports);cmd=['python3','-c',code];commands.append(cmd);rc=command(cmd,src.parent,d/'prerequisites.log',env,30);reason='CUDA Python 原始绑定/测试可执行文件尚未通过原始 GPU 运行资格；import 检查返回码 '+str(rc)+'，不能从 import 成功推断 GPU 基线成功。'
 else:
  available=identity['compilers'];(d/'prerequisites.log').write_text(json.dumps(available,indent=2)+'\nCUDA vendor modules required: '+', '.join(__import__('re').findall(r'^\s*use\s+(\w+)',body,__import__('re').M|__import__('re').I)))
  reason='原始 Fortran 基线需要 NVIDIA SDK module（cuDSS/cudafor/cufftXt/MPI）及匹配编译器；已记录实际编译器可用性，当前缺少完整 vendor module/toolchain。'
 r={'sample_id':s['id'],'status':'BLOCKED','prerequisite_return_code':rc,'scope':'CUDA original frontend/import prerequisite; not GPU numerical baseline','reason':reason,'evidence':str(d.relative_to(ROOT)),'environment':identity};(d/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');(d/'summary.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n');results.append(r)
(ROOT/'migration/reports/cuda-language-prerequisites.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n');print('CUDA language prerequisite outcomes:',len(results))
