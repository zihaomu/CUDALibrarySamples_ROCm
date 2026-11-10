#!/usr/bin/env python3
"""Record current scope gaps for all 24 R3 entries; never infer numerical support."""
import argparse,fcntl,json,sys
from experiment import ROOT,Experiment,write,digest

def assessment(sample):
 original=ROOT/sample['source'];implementation=ROOT/sample['implementation'];missing=sorted(set(sample['required_cases'])-set(sample['passed_cases']))
 proofs=[sample.get('selected_validation',{})]+list(reversed(sample['attempts']));current=next((p for p in proofs if p.get('implementation_sha256')==digest(implementation)),{})
 stale={name:dict(expected=sha,observed=digest(ROOT/name) if (ROOT/name).is_file() else None) for name,sha in current.get('dependencies',{}).items() if not (ROOT/name).is_file() or digest(ROOT/name)!=sha}
 # These lines identify the source contract to inspect; absence of a token is
 # not used as proof that an algorithm is impossible or a GPU is unsupported.
 terms=['IA','JA','IB','JB','tile','grid','CUDSS_CONFIG','CUDSS_DATA','progressive','backend','LEGACY','ordering','rank','RnrmF','NVBENCH','nvbench','-noise','paint','nppiFilterCanny','GEMM']
 lines=[dict(line=i,text=line[:250]) for i,line in enumerate(original.read_text().splitlines(),1) if any(t in line for t in terms)][:70]
 return dict(sample_id=sample['id'],source=sample['source'],status=sample['status'],observation='STATIC_CONTRACT_REVIEW; no new GPU result claimed',original_sha256=digest(original),implementation_sha256=digest(implementation),current_missing_contract=missing,current_reason=sample['reason'],actual_library=sample['actual_library'],previous_evidence=sample['evidence'],current_proof_dependencies_stale=stale,source_contract_lines=lines,next_condition=sample['retry_condition'],checks=[dict(check='original-source-identity',passed=digest(original)==sample['source_sha256']),dict(check='explicit-unfulfilled-contract',passed=bool(missing))])

def main():
 p=argparse.ArgumentParser();p.add_argument('--single');p.add_argument('--output');a=p.parse_args();cat=json.loads((ROOT/'migration/samples.yaml').read_text());tasks=json.loads((ROOT/'migration/moat/tasks.json').read_text())
 if a.single:
  s=next(s for s in cat['samples'] if s['id']==a.single);r=assessment(s);write(a.output,r);print(json.dumps(r,ensure_ascii=False));return int(not all(c['passed'] for c in r['checks']))
 rows=[];samples={s['id']:s for s in cat['samples']}
 for task in tasks['tasks']:
  if task['primary_phase']!='R3':continue
  sample=samples[task['sample_id']];e=Experiment('R3',sample['id'],'host-contract-review',sources=[__file__,ROOT/sample['source'],ROOT/sample['implementation']]);output=e.path/'contract-audit.json';rc=e.command([sys.executable,__file__,'--single',sample['id'],'--output',str(output)],'inspect-current-contract');r=json.loads(output.read_text());r['experiment_id']=e.id;r['evidence']=e.finish('CONTRACT_GAP_RECORDED' if rc==0 else 'CONTRACT_AUDIT_FAILED',dict(status='NOT_NUMERIC_VALIDATION',checks=r['checks']));rows.append(r)
  task['state']='NUMERIC_CANDIDATE_REVIEW_PENDING' if sample['reason_code']=='REWRITE_REVIEW_PENDING' else 'ASSESSED_GAP_REMAINS';task['experiments'].append(e.id);task['remaining_contract']=r['current_missing_contract'];task['assessment_evidence']=r['evidence']
  write(ROOT/'migration/reports/rewrite-R3-gap-audit.json',dict(scope='24 PARTIAL source contracts; static review is not GPU qualification',entries=rows));print(sample['source'],len(r['current_missing_contract']),flush=True)
 write(ROOT/'migration/moat/tasks.json',tasks)
 lines=['# R3 逐例合同缺口复审','', '本表覆盖原始24个PARTIAL。静态合同审查不作为新的GPU通过证据。NCC与SVD候选另有新数值试验；其它项目保留原数值范围及明确缺项。','', '| 原始入口 | 当前缺少合同 | 当前实际路线 | 当前证据 / 恢复条件 |','| --- | --- | --- | --- |']
 for r in rows:lines.append('| `'+r['source']+'` | '+', '.join('`'+c+'`' for c in r['current_missing_contract'])+' | '+str(r['actual_library']).replace('|','/')+' | [逐项审查]('+r['evidence'].removeprefix('migration/reports/')+'/contract-audit.json)；'+r['next_condition'].replace('|','/')+' |')
 (ROOT/'migration/reports/rewrite-R3-gaps.md').write_text('\n'.join(lines)+'\n')
 return 0
if __name__=='__main__':raise SystemExit(main())
