#!/usr/bin/env python3
"""Publish the complete distance entry only after qualification is Git anchored."""
import json
from experiment import ROOT,write,digest
from qualify_image_distance import collect,load,SAMPLE,IMPLEMENTATION,COMPARISON,metadata,sealed
from selected_proofs import inspect

def validate(q,sample,review,closure=None):
 checks,refs,sources,b,spec=closure if closure is not None else collect(review);d,m,_=sealed(q['evidence']);frozen=json.loads((d/'qualification.json').read_text())
 if sample['id']!=SAMPLE or q['sample_id']!=SAMPLE or m['backend']!='composite-qualification' or m['sample_id']!=SAMPLE or m['experiment_id']!=q['qualification_id'] or m['experiment_outcome']!='PASSED' or q['kind']!='image-distance-full' or q['implementation']!=IMPLEMENTATION or q['implementation_sha256']!=digest(ROOT/IMPLEMENTATION) or q['source_commit']!=review['source_commit']:raise ValueError('distance qualification identity')
 if q['status']!='PASSED' or q['checks']!=checks or not checks or not all(c['passed'] for c in checks) or q['dependencies']!=load('frontend-build')['dependencies'] or set(q['evidence_references'])!=refs or any(q.get(k)!=v for k,v in frozen.items()) or set(q)!=set(frozen)|{'qualification_id','evidence'} or q['case_ids']!=[c['case'] for c in spec['cases']] or q['case_count']!=30 or q['comparison_mode']!=COMPARISON or any(q.get(k)!=v for k,v in metadata().items()):raise ValueError('incomplete or altered distance proof')
 result=inspect(dict(sample,implementation=IMPLEMENTATION,selected_validation=q))
 if result['status']!='PASSED':raise ValueError(str(result['errors']))

def main():
 q=load('qualification');review=load('review');catalog=json.loads((ROOT/'migration/samples.yaml').read_text());s=next(s for s in catalog['samples'] if s['id']==SAMPLE);validate(q,s,review);required=['image-distance/'+c for c in q['case_ids']]+['image-distance/full-five-input-twelve-file-originals','image-distance/typed-sites-Voronoi-visualization-padding','image-distance/arguments-streams-concurrency-extremes','image-distance/CLI-errors','image-distance/GPU-trace','image-distance/independent-CPU-and-native-comparison','image-distance/model-and-validator-checks','image-distance/legacy-EDT-NCC-regressions','image-distance/cold-checkout','image-distance/independent-review']
 s.update(status='PASSED',level='L4',reason_code='VALIDATED_MOAT_REWRITE',implementation=IMPLEMENTATION,selected_validation=q,required_cases=required,passed_cases=required,actual_library='Project HIP exact unsigned EDT + compact threshold-crossing signed site set + GPU FP64 search, deterministic Voronoi and visualization',backend_library='project HIP distance transform',equivalence=COMPARISON,reason='完整五图/12RAW C++入口，30全量输入，4流程48RAW，69参数、27状态/极值、19CLI、100CPU模型、57验收器检查及trace/12子记录冷检出/三复审通过。Signed使用预固定的线性阈值交点site距离与独立CPU定义；和NPP+闭源算法/锚点规则的差异完整单列，不承诺逐位vendor一致。',cuda_baseline='PASSED',cuda_baseline_reason='5090未改NPP+原始源码、7输入/12输出、binary与实际SDK库/GPU receipt完整成功。',cuda_comparison='OBSERVED',cuda_comparison_mode='EXACT_UNSIGNED_AND_DOCUMENTED_SIGNED_ALGORITHM_VARIANT',cuda_comparison_reason='原始unsigned距离一致；signed-circle最大差29.944444444444457、Lith最大差0.8653281413382601及Voronoi规则差异单列。项目HIP对独立CPU全部30输入maxAbs=0，预固定预算atol2e-11/rtol1e-12，非按vendor拟合。',benchmark='NOT_QUALIFIED',active_batch='I2',retry_condition='修改数值定义、tie/site规则、布局、接口或平台必须重新固定合同并实测。',next_step='继续I3分水岭、flood fill、Hough与图像基准；I9补齐既有NPP unsigned EDT六RAW原入口。',reproduce='python3 tools/moat/image_distance_contracts.py\npython3 tools/moat/image_distance_build.py\npython3 tools/moat/image_distance_run.py\npython3 tools/moat/image_distance_frontend_build.py\npython3 tools/moat/image_distance_originals.py')
 for ref in ['migration/reports/image-distance.md',q['evidence'],*q['evidence_references']]:
  if ref not in s['evidence']:s['evidence'].append(ref)
 if not any(a.get('qualification_id')==q['qualification_id'] for a in s['attempts']):s['attempts'].append(q)
 write(ROOT/'migration/samples.yaml',catalog);print('Published complete NPP+ unsigned/signed distance transform')
if __name__=='__main__':main()
