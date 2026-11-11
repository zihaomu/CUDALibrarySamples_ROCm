#!/usr/bin/env python3
"""Publish one complete image entry only after immutable qualification publication."""
import json
from experiment import ROOT,write,digest
from qualify_canny_plus import collect,load,sealed
from selected_proofs import inspect

def main():
 q=load('qualification');review=load('review');checks,refs,sources,build,spec=collect(review)
 catalog=json.loads((ROOT/'migration/samples.yaml').read_text());sample=next(s for s in catalog['samples'] if s['id']==spec['sample_id'])
 d,m,_=sealed(q['evidence']);frozen=json.loads((d/'qualification.json').read_text())
 if q['status']!='PASSED' or q['checks']!=checks or not checks or not all(c['passed'] for c in checks) or set(q['evidence_references'])!=refs or q['dependencies']!=build['dependencies'] or any(q.get(k)!=v for k,v in frozen.items()) or q['source_commit']!=review['source_commit'] or q['case_ids']!=[c['case'] for c in spec['cases']] or q['case_count']!=31:raise ValueError('Incomplete or changed qualification')
 proposal=dict(sample,implementation=q['implementation'],selected_validation=q)
 result=inspect(proposal)
 if result['status']!='PASSED':raise ValueError(str(result['errors']))
 required=['image/'+c for c in q['case_ids']]+['image/full-original-8-sizes-1000-loops','image/runtime-and-ABI','image/GPU-trace','image/positive-negative-validator','image/independent-review']
 sample.update(status='PASSED',level='L4',reason_code='VALIDATED_MOAT_REWRITE',implementation=q['implementation'],selected_validation=q,required_cases=required,passed_cases=required,actual_library='Project HIP Canny + ROCm Torch (C1 Sobel3/L2/local threshold)',backend_library='project HIP image C ABI',equivalence='ALGORITHM_VARIANT',reason='完整C1原例8分辨率、5 warmup/1000测量及PNG/CSV通过；31组最终mask与独立CPU逐像素一致，native NPP+全部内部像素一致，仅两研究用例合计3外圈点不同。两stream/并发/类型转换/非法span与trace、验收器反向和独立复审通过。',cuda_baseline=load('original-cuda')['status'],cuda_baseline_reason='原始Python脚本的5090系统Python缺少Torch；原始依赖状态保留，正确NppStreamContext的native NPP+ C++ API对照31组成功。',cuda_comparison='PASSED',cuda_comparison_mode='NATIVE_NPP_PLUS_API_COUNTERPART',cuda_comparison_reason='同字节输入、同阈值、NPP+真实API及SDK/二进制回执；完整内部mask一致，3个外圈差异按项目明确边界规则接受。',benchmark='NOT_QUALIFIED',active_batch='I1',retry_condition='扩展kernel/算法/dtype/布局/平台或性能声明时重新冻结合同并实测。',next_step='当前C1完整范围已通过；C3和其它图像模块单列。',reproduce='python3 tools/moat/canny_plus_build.py\npython3 tools/moat/canny_plus_run.py\npython3 tools/moat/canny_plus_run.py --original')
 for ref in ['migration/reports/canny-plus.md',q['evidence'],*q['evidence_references']]:
  if ref not in sample['evidence']:sample['evidence'].append(ref)
 if not any(a.get('qualification_id')==q['qualification_id'] for a in sample['attempts']):sample['attempts'].append(q)
 write(ROOT/'migration/samples.yaml',catalog);print('Published complete NPP+ C1 Python sample')
if __name__=='__main__':main()
