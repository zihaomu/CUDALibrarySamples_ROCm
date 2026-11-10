#!/usr/bin/env python3
"""Qualify actual numeric/execution contracts; keep original vendor and compatible baselines distinct."""
import argparse,fcntl,importlib,json,pathlib
from catalog import ROOT
from run import digest,evidence_directory
from batches12_15_spec import GROUPS,kind,LIMITS,ROUTES,route
p=argparse.ArgumentParser();p.add_argument('groups',nargs='+',choices=list(GROUPS));p.add_argument('--qualify',action='store_true');a=p.parse_args()
def records(name):
 p=ROOT/'migration/reports'/name;return {r['source']:r for r in json.loads(p.read_text())} if p.exists() else {}
amd=records('batches12_15-rocm.json');cuda=records('batches12_15-cuda.json');native=records('batches12_15-native-cuda.json');results=[]
for group in a.groups:
 ref=importlib.import_module('batch'+group[1:]+'_reference')
 for source,cases in GROUPS[group].items():
  r=amd.get(source);cr=cuda.get(source);nr=native.get(source)
  if not r:continue
  checks=[];comparisons=[]
  def one(record,case):
   if not record or record['build_return_code']:raise ValueError('build missing/failed')
   c=next(x for x in record['runs'] if x['case']==case)
   if c['return_code']:raise ValueError('run failed '+str(c['return_code']))
   d=evidence_directory(c['evidence']);v=ref.validate(source,case,d);manifest={str(f.relative_to(d)):dict(sha256=digest(f),bytes=f.stat().st_size) for f in d.rglob('*') if f.is_file() and f.name!='outputs-manifest.json' and f.suffix in ['.bin','.log','.json','.txt']};mp=d/'outputs-manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');v['output_manifest']=dict(path=str(mp.relative_to(ROOT)),sha256=digest(mp),files=len(manifest));return v
  for case in cases:
   try:v=one(r,case)
   except Exception as e:v=dict(status='FAILED',reason=str(e))
   v['case']=case;checks.append(v)
   try:cv=one(cr,case);same=v.get('input_sha256')==cv.get('input_sha256');comparisons.append(dict(case=case,status='PASSED' if same and cv['status']==v['status']=='PASSED' else 'FAILED',identical_input=same,cuda_cpu_checks=cv))
   except Exception as e:comparisons.append(dict(case=case,status='BLOCKED',reason=str(e)))
  good=all(v['status']=='PASSED' for v in checks);comp=all(v['status']=='PASSED' for v in comparisons);deps=dict(r['dependencies']);deps['tools/migration/batch'+group[1:]+'_reference.py']=digest(ROOT/('tools/migration/batch'+group[1:]+'_reference.py'));deps['tools/migration/batches12_15_spec.py']=digest(ROOT/'tools/migration/batches12_15_spec.py');source_current=digest(ROOT/r['implementation'])==r['implementation_sha256'] and all(digest(ROOT/n)==h for n,h in r['dependencies'].items());cuda_current=bool(cr and digest(ROOT/cr['implementation'])==cr['implementation_sha256'] and all(digest(ROOT/n)==h for n,h in cr['dependencies'].items()));qualified=good and comp and source_current and cuda_current;k=kind(source);missing=list(LIMITS[k][:1]) if k in LIMITS else [];row=dict(r,status='PASSED' if good else 'FAILED',level='L4' if good else 'L3' if r['build_return_code']==0 else 'L1',cases=checks,cuda_cases=comparisons,cuda_comparison='PASSED' if comp else 'FAILED',contract_status=('PARTIAL' if missing else 'PASSED') if qualified else 'FAILED',missing_contract=missing,limitation=LIMITS[k][1] if missing else '仅登记profile/规模/执行方式通过，不外推其它dtype、规模、网格或性能；内部数据重分配/CPU布局编排与项目GPU算法已公开。',dependencies=deps,cuda_dependencies=cr.get('dependencies',{}) if cr else {},current_source_proof=source_current,current_cuda_source_proof=cuda_current,cuda_evidence=cr.get('evidence') if cr else None,cuda_implementation_sha256=cr.get('implementation_sha256') if cr else None,cuda_baseline_kind='COMPATIBLE_CUDA_MATH_BASELINE',native_cuda_attempt=nr,validation_source_sha256=digest(pathlib.Path(__file__)))
  results.append(row);print(source,row['status'],'CUDA',row['cuda_comparison'],'CONTRACT',row['contract_status'],[(x['case'],x.get('reason'),[y['check'] for y in x.get('checks',[]) if not y['passed']][:3]) for x in checks if x['status']!='PASSED'],flush=True)
report=ROOT/'migration/reports/batches12_15-validation.json';old=records(report.name);old.update({r['source']:r for r in results});report.write_text(json.dumps(list(old.values()),indent=2,ensure_ascii=False)+'\n')
if a.qualify:
 with (ROOT/'migration/.state.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);path=ROOT/'migration/samples.yaml';cat=json.loads(path.read_text())
  for r in results:
   s=next(s for s in cat['samples'] if s['source']==r['source']);s['attempts'].append(r);s['evidence']=list(dict.fromkeys(s['evidence']+[r['evidence'],'migration/reports/batches12_15-validation.json']+([r['cuda_evidence']] if r['cuda_evidence'] else [])))
   if r['contract_status']=='FAILED':continue
   nr=r.get('native_cuda_attempt');baseline='PASSED' if nr and nr['build_return_code']==nr['run_return_code']==0 else 'FAILED' if nr else 'BLOCKED';labels=['batches12_15/'+c['case'] for c in r['cases']];s.update(status=r['contract_status'],level='L4',implementation=r['implementation'],actual_library=route(r['source']),backend_library=route(r['source']),equivalence='API_PORT_WITH_EXECUTION_ADAPTER',required_cases=labels+['batches12_15/'+x for x in r['missing_contract']],passed_cases=labels,reason_code='VALIDATED_B12_B15' if r['contract_status']=='PASSED' else 'VALIDATED_B12_B15_SUBSET',reason='使用'+route(r['source'])+'；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。'+r['limitation'],cuda_baseline=baseline,cuda_comparison='PASSED',cuda_comparison_mode=r['cuda_baseline_kind'],cuda_baseline_reason='原始vendor尝试与兼容CUDA数学实现分别留证；原始程序退出成功不代表同输入输出已对比。',selected_validation=r,retry_condition='未完成合同：'+','.join(r['missing_contract'])+'；补实现/真实后端并重验。' if r['missing_contract'] else '扩展其它dtype、规模、线程块/进程网格、多节点或性能需新增登记case并重验。',reproduce='HIP_VISIBLE_DEVICES=2,1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches12_15_run.py '+r['batch']+'\nOPENBLAS_NUM_THREADS=2 python3 tools/migration/batches12_15_validate.py '+r['batch']+' --qualify')
   if nr:s['evidence']=list(dict.fromkeys(s['evidence']+[nr['evidence']]))
  path.write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n')
