#!/usr/bin/env python3
"""Publish the complete contour pair only after first Git qualification anchoring."""
import json
from experiment import ROOT,write,digest
from qualify_image_contour import collect,load,ENTRIES,sealed
from selected_proofs import inspect

def validate(q,sample,review,closure=None):
 checks,refs,sources,b,spec=closure if closure is not None else collect(review);implementation=ENTRIES[sample['id']];d,m,_=sealed(q['evidence']);frozen=json.loads((d/'qualification.json').read_text())
 if m['backend']!='composite-qualification' or m['sample_id']!=sample['id'] or m['experiment_id']!=q['qualification_id'] or m['experiment_outcome']!='PASSED' or q['kind']!='image-contour-full' or q['sample_id']!=sample['id'] or q['implementation']!=implementation or q['implementation_sha256']!=digest(ROOT/implementation) or q['source_commit']!=review['source_commit']:raise ValueError('contour qualification identity')
 if q['status']!='PASSED' or q['checks']!=checks or not checks or not all(c['passed'] for c in checks) or q['dependencies']!=load('frontends-build')['dependencies'] or set(q['evidence_references'])!=refs or any(q.get(k)!=v for k,v in frozen.items()) or q['case_ids']!=[c['case'] for c in spec['cases']] or q['case_count']!=22:raise ValueError('incomplete or altered contour proof')
 result=inspect(dict(sample,implementation=implementation,selected_validation=q))
 if result['status']!='PASSED':raise ValueError(str(result['errors']))

def main():
 group=load('qualification');review=load('review');catalog=json.loads((ROOT/'migration/samples.yaml').read_text());samples={s['id']:s for s in catalog['samples']};rows=group['qualifications']
 if group['status']!='PASSED' or len(rows)!=2 or {q['sample_id'] for q in rows}!=set(ENTRIES):raise ValueError('complete two-entry contour publication required')
 closure=collect(review)
 for q in rows:validate(q,samples[q['sample_id']],review,closure)
 for q in rows:
  s=samples[q['sample_id']];required=['image-contour/'+c for c in q['case_ids']]+['image-contour/full-original-files-and-ordered-diagnostics','image-contour/ranges-bypass-and-single-ID-override','image-contour/closed-geometry-and-reconstruction','image-contour/actual-runtime-streams-concurrency','image-contour/CLI-and-invalid-device-data','image-contour/GPU-trace','image-contour/validator-mutations','image-contour/cold-checkout','image-contour/independent-review'];s.update(status='PASSED',level='L4',reason_code='VALIDATED_MOAT_REWRITE',implementation=q['implementation'],selected_validation=q,required_cases=required,passed_cases=required,actual_library='Project HIP equal-value 8-connected CCL + directed cell-edge loops + GPU ordering and geometry rasterization',backend_library='project HIP contour geometry',equivalence='ALGORITHM_VARIANT_EXACT_PROJECT_GEOMETRY',reason='两个完整C++入口；22组全像素/逐edge闭环顺序/bbox/count/范围重建，15个实际流程/55RAW/逐点诊断，32CLI、61参数、26畸形设备数据、11状态/stream、58验收器反例及trace/冷检出/三复审通过。保持原例输出与范围/bypass行为；使用公开项目有向单元边表示，非NPP packed ABI。原生错误分区和早期ABI1缺边失败保留单列。',cuda_baseline='PASSED',cuda_baseline_reason='5090未改NPP/NPP+原始源码完整build/run成功；原生分区数学差异另外记录。',cuda_comparison='OBSERVED',cuda_comparison_mode='NATIVE_EXECUTION_AND_PARTITION_FAILURES_SEPARATE',cuda_comparison_reason='原图正确262分量，NPP273/NPP+266，72002/13246像素分区不同；原生0边界编码与其自身标签对应，HIP按独立CPU正确分区。',benchmark='NOT_QUALIFIED',active_batch='I2',retry_condition='修改连接、几何、布局、范围、接口或平台须重新固定合同并实测。',next_step='继续NPP+ signed/unsigned距离变换及原EDT/NCC回归。',reproduce='python3 tools/moat/image_contour_contracts.py\npython3 tools/moat/image_contour_build.py\npython3 tools/moat/image_contour_run.py\npython3 tools/moat/image_contour_frontends_build.py\npython3 tools/moat/image_contour_originals.py')
  for ref in ['migration/reports/image-contour.md',q['evidence'],*q['evidence_references']]:
   if ref not in s['evidence']:s['evidence'].append(ref)
  if not any(a.get('qualification_id')==q['qualification_id'] for a in s['attempts']):s['attempts'].append(q)
 write(ROOT/'migration/samples.yaml',catalog);print('Published two complete contour entries')
if __name__=='__main__':main()
