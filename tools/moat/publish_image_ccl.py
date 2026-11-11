#!/usr/bin/env python3
"""Publish only the complete reviewed and first-Git-anchored CCL group."""
import json
from experiment import ROOT,write,digest
from qualify_image_ccl import collect,load,ENTRIES,sealed
from selected_proofs import inspect

def validate(q,sample,review):
 checks,refs,sources,b,spec=collect(review);implementation=ENTRIES[sample['id']];d,m,_=sealed(q['evidence']);frozen=json.loads((d/'qualification.json').read_text())
 if m['backend']!='composite-qualification' or m['sample_id']!=sample['id'] or m['experiment_id']!=q['qualification_id'] or m['experiment_outcome']!='PASSED' or q['kind']!='image-ccl-full' or q['sample_id']!=sample['id'] or q['implementation']!=implementation or q['implementation_sha256']!=digest(ROOT/implementation) or q['source_commit']!=review['source_commit']:raise ValueError('CCL qualification identity')
 if q['status']!='PASSED' or q['checks']!=checks or not checks or not all(c['passed'] for c in checks) or q['dependencies']!=b['dependencies'] or set(q['evidence_references'])!=refs or any(q.get(k)!=v for k,v in frozen.items()) or q['case_ids']!=[c['case'] for c in spec['cases']] or q['case_count']!=27:raise ValueError('Incomplete or altered CCL proof')
 result=inspect(dict(sample,implementation=implementation,selected_validation=q))
 if result['status']!='PASSED':raise ValueError(str(result['errors']))

def main():
 group=load('qualification');review=load('review');catalog=json.loads((ROOT/'migration/samples.yaml').read_text());samples={s['id']:s for s in catalog['samples']};rows=group['qualifications']
 if group['status']!='PASSED' or len(rows)!=2 or {q['sample_id'] for q in rows}!=set(ENTRIES):raise ValueError('Complete two-entry CCL publication required')
 for q in rows:validate(q,samples[q['sample_id']],review)
 for q in rows:
  s=samples[q['sample_id']];required=['image-CCL/'+c for c in q['case_ids']]+['image-CCL/full-original-individual-and-heterogeneous-batch','image-CCL/all-five-batch-counts','image-CCL/conditional-batch-compression','image-CCL/actual-runtime-ABI-streams-instances','image-CCL/default-foreign-destroyed-streams','image-CCL/complete-CLI-errors-and-no-device','image-CCL/raw-GPU-dispatch','image-CCL/independent-BFS-and-validator-mutations','image-CCL/cold-checkout','image-CCL/independent-review'];s.update(status='PASSED',level='L4',reason_code='VALIDATED_MOAT_REWRITE',implementation=q['implementation'],selected_validation=q,required_cases=required,passed_cases=required,actual_library='Project HIP equal-value 8-connected union/find + hierarchical GPU prefix-scan compression',backend_library='project HIP CCL',equivalence='EXACT_CPU_PARTITION_ARBITRARY_VENDOR_IDS',reason='原始五输入/单图与异构batch、NPP+默认及CUDA11U1压缩分支完整；27组全像素/padding、44运行合同及3项默认/外设备/销毁stream、1..5 batch共15个完整流程/165文件、39CLI、31正反例/BFS、trace/冷检出/三复审通过。包括零值所有区域，编号按最小像素确定；当前NPP/NPP+原生分区错误单列，不复制厂商错误。',cuda_baseline='PASSED',cuda_baseline_reason='5090未改原始NPP与NPP+默认/条件编译三配置均运行成功，55原始输出完整保留；原生数学分区验收另外记录FAILED项。',cuda_comparison='OBSERVED',cuda_comparison_mode='NATIVE_NPP_AND_NPPPLUS_CONFORMANCE_RECORDED',cuda_comparison_reason='54次真实API及55原始输出对独立CPU完整比较。3x3两库返回5分量，CPU/HIP为4；其它分裂/合并均逐输入记录，native程序成功不等于数学正确。',benchmark='NOT_QUALIFIED',active_batch='I2',retry_condition='修改连接、编号、类型、布局、范围或平台须重新冻结并实测。',next_step='两个CCL完整入口已完成；I2的轮廓与signed/unsigned EDT继续单列。',reproduce='python3 tools/moat/image_ccl_contracts.py\npython3 tools/moat/image_ccl_build.py\npython3 tools/moat/image_ccl_run.py\npython3 tools/moat/image_ccl_originals.py')
  for ref in ['migration/reports/image-ccl.md',q['evidence'],*q['evidence_references']]:
   if ref not in s['evidence']:s['evidence'].append(ref)
  if not any(a.get('qualification_id')==q['qualification_id'] for a in s['attempts']):s['attempts'].append(q)
 write(ROOT/'migration/samples.yaml',catalog);print('Published two complete CCL entries')
if __name__=='__main__':main()
