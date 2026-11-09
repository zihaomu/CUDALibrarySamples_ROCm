#!/usr/bin/env python3
"""Compare saved CUDA and AMD result values, treating RNG statistically."""
import json,math,pathlib,hashlib
from catalog import ROOT
cat=json.loads((ROOT/'migration/samples.yaml').read_text());cuda=json.loads((ROOT/'migration/reports/m1-cuda-latest.json').read_text());original=json.loads((ROOT/'migration/reports/cuda-original-latest.json').read_text())
cudas={r['sample_id']:r for r in cuda['results']};baselines={r['source']:r for r in original['results']};comparisons=[]
specs={v['upstream_source']:v for v in json.loads((ROOT/'migration/m1.json').read_text())}
for s in cat['samples']:
 if s['id'] not in cudas:continue
 cr=cudas[s['id']];ar=next((v for v in reversed(s['attempts']) if v.get('scope','').startswith('M1 extended') and v.get('implementation_sha256')==hashlib.sha256((ROOT/s['implementation']).read_bytes()).hexdigest()),None)
 comparison={'id':s['id'],'cuda_evidence':cr['evidence'],'rocm_evidence':ar['evidence'] if ar else None,'status':'BLOCKED','cases':[]}
 if ar and ar['status']=='PASSED' and cr['status']=='PASSED' and ar['fixture_sha256']==cr['fixture_sha256']:
  cp=ROOT/cr['evidence']/'run.log';ap=ROOT/ar['evidence']/'run.log'
  crows={v['case']:v for line in cp.read_text().splitlines() if line.startswith('{') for v in [json.loads(line)]};arows={v['case']:v for line in ap.read_text().splitlines() if line.startswith('{') for v in [json.loads(line)]}
  okay=set(crows)==set(arows)==set(s['required_cases'])
  for case in sorted(set(crows)&set(arows)):
   x=arows[case]['values'];y=crows[case]['values'];rng=s['family']=='cuRAND';tol=0.04 if rng else (2e-5 if s['family'] in ['cuFFT','cuSPARSE','cuBLASLt'] else 1e-10)
   err=max((abs(a-b) for a,b in zip(x,y)),default=0.);passed=len(x)==len(y) and all(math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol+tol*abs(b) for a,b in zip(x,y));okay &= passed
   comparison['cases'].append({'case':case,'passed':passed,'max_abs_diff':err,'criterion':'distribution_summary' if rng else 'atol+rtol*abs(reference)','atol':tol,'rtol':tol})
  comparison['status']='PASSED' if okay else 'FAILED'
 s['cuda_comparison']=comparison['status'];s['cuda_baseline']=baselines[s['source']]['status']
 if comparison['status']=='PASSED' and specs[s['source']].get('original_profile_covered') and ar['implementation_sha256']==hashlib.sha256((ROOT/s['implementation']).read_bytes()).hexdigest():
  s.update(status='PASSED',reason_code=None,reason=f'使用 {s["actual_library"]}（{s["backend_library"]}）成功实现原始 profile 和 {len(s["passed_cases"])} 个数值用例，并通过 CUDA 对照')
 comparison['cuda_original']=baselines[s['source']];comparisons.append(comparison)
(ROOT/'migration/reports/m1-comparison.json').write_text(json.dumps(comparisons,indent=2)+'\n');(ROOT/'migration/samples.yaml').write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n')
print('Comparison:',{state:sum(r['status']==state for r in comparisons) for state in ['PASSED','FAILED','BLOCKED']})
