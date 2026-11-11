#!/usr/bin/env python3
"""Publish two complete C3 callers only after recomputation and Git anchoring."""
import json
from experiment import ROOT,write,digest
from qualify_canny_color import load,collect,sealed
from selected_proofs import inspect

def validate(q,sample,language,review):
 checks,refs,sources,b,spec=collect(language,review);expected='rocm/ported/NPP/nppCanny/npp_canny_simple.'+('cpp' if language=='cpp' else 'py');d,m,_=sealed(q['evidence']);frozen=json.loads((d/'qualification.json').read_text())
 if m['backend']!='composite-qualification' or m['sample_id']!=sample['id'] or m['experiment_id']!=q['qualification_id'] or m['experiment_outcome']!='PASSED' or q['kind']!='image-canny-c3-full/'+language or q['sample_id']!=sample['id'] or q['implementation']!=expected or q['implementation_sha256']!=digest(ROOT/expected) or q['source_commit']!=review['source_commit']:raise ValueError('C3 qualification/entry/language identity')
 if q['status']!='PASSED' or q['checks']!=checks or not checks or not all(c['passed'] for c in checks) or q['dependencies']!=b['dependencies'] or set(q['evidence_references'])!=refs or any(q.get(k)!=v for k,v in frozen.items()) or q['case_ids']!=[c['case'] for c in spec['cases']] or q['case_count']!=22:raise ValueError('Incomplete or altered C3 proof')
 result=inspect(dict(sample,implementation=expected,selected_validation=q))
 if result['status']!='PASSED':raise ValueError(str(result['errors']))

def main():
 group=load('qualification');review=load('review');catalog=json.loads((ROOT/'migration/samples.yaml').read_text());expected={'NPP/nppCanny::npp_canny_simple.cpp':'cpp','NPP/nppCanny::npp_canny_simple.py':'python'};rows=group['qualifications'];samples={s['id']:s for s in catalog['samples']}
 if group['status']!='PASSED' or len(rows)!=2 or {r['sample_id'] for r in rows}!=set(expected):raise ValueError('Complete two-language C3 publication required')
 for q in rows:validate(q,samples[q['sample_id']],expected[q['sample_id']],review)
 for q in rows:
  s=samples[q['sample_id']];language=expected[q['sample_id']];required=['image-C3/'+name for name in q['case_ids']]+['image-C3/full-original-three-files-and-10-loops','image-C3/runtime-and-actual-ABI','image-C3/real-C++-class-ROI-errors-and-instances','image-C3/default-file-errors-and-no-device','image-C3/raw-GPU-trace','image-C3/validator-negative','image-C3/cold-checkout','image-C3/independent-source-review'];s.update(status='PASSED',level='L4',reason_code='VALIDATED_MOAT_REWRITE',implementation=q['implementation'],selected_validation=q,required_cases=required,passed_cases=required,actual_library='HIP C3 Sobel/NMS/GPU union-find hysteresis + OpenCV file IO/CPU comparisons'+(' + ROCm Torch' if language=='python' else ''),backend_library='project HIP classical C3 Canny',equivalence='ALGORITHM_VARIANT_C3_CLASSICAL_HYSTERESIS',reason='完整C++/Python原例三PNG、1预热/10测量及两类OpenCV比较；22组mask/padding对独立CPU精确，55项运行合同、真实C++ ROI/错误/并发实例、10 CLI/无设备、39正反例、trace、冷检出和三复审通过。采用经典8连接强种子滞后：原图比NPP少4328个弱边缘像素（IoU0.6323），全部强种子保留，实测项目边缘均包含在native边缘中；不宣称NPP mask逐点兼容。',cuda_baseline='PASSED' if language=='cpp' else 'BLOCKED',cuda_baseline_reason='原始未改CUDA C++三PNG与native NPP API逐像素一致。' if language=='cpp' else '5090系统Python缺Torch；依赖检查BLOCKED，native NPP C3 API同输入对照成功，AMD真实Python完整流程通过。',cuda_comparison='PASSED',cuda_comparison_mode='NATIVE_NPP_ORIGINAL_PLUS_API_ALGORITHM_VARIANT' if language=='cpp' else 'NATIVE_NPP_API_COUNTERPART_ALGORITHM_VARIANT',cuda_comparison_reason='22组真实native NPP成功；18组mask精确，原图、孤立弱边缘、高强阈值、零阈值按已固定的经典8连接变体完整记录差异。原始CUDA C++另实测成功；原Python依赖缺口单列。',benchmark='NOT_QUALIFIED',active_batch='I1',retry_condition='变更算法/阈值/布局/规模/平台或性能声明需新冻结并完整实测。',next_step='已完成登记的C3完整调用方；CCL/contour/EDT等I2项目继续单列。',reproduce='python3 tools/moat/canny_color_build.py\npython3 tools/moat/canny_color_run.py\npython3 tools/moat/canny_color_run.py --originals')
  for ref in ['migration/reports/canny-color.md',q['evidence'],*q['evidence_references']]:
   if ref not in s['evidence']:s['evidence'].append(ref)
  if not any(a.get('qualification_id')==q['qualification_id'] for a in s['attempts']):s['attempts'].append(q)
 write(ROOT/'migration/samples.yaml',catalog);print('Published two complete C3 classical Canny callers')
if __name__=='__main__':main()
