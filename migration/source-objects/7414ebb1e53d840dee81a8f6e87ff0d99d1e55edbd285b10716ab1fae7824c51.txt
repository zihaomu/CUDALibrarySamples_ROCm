#!/usr/bin/env python3
"""Publish the original encoder's Git-anchored GPU subset as PARTIAL."""
import json
from experiment import ROOT,digest,write
from image_progress import record
from selected_proofs import anchored_seal,publication

def main():
 q=json.loads((ROOT/'migration/reports/image-jpeg-encoder-instances-subset-qualification.json').read_text())
 proof=ROOT/q['evidence'];sealed=json.loads((proof/'qualification.json').read_text())
 catalog=json.loads((ROOT/'migration/samples.yaml').read_text())
 sample=next(s for s in catalog['samples'] if s['id']==q['sample_id'])
 if (not anchored_seal(proof,publication(proof),qualification=True) or
  q['kind']!='image-JPEG-multiple-instances-optimized-GPU-subset' or q['status']!='PASSED' or
  q['contract_status']!='PARTIAL' or q['case_count']!=10 or len(q['case_ids'])!=10 or
  any(not c['passed'] for c in q['checks']) or
  {k:v for k,v in q.items() if k not in {'qualification_id','evidence'}}!=sealed or
  q['implementation']!=sample['implementation'] or
  q['implementation_sha256']!=digest(ROOT/q['implementation']) or
  any(digest(ROOT/n)!=h for n,h in q['dependencies'].items()) or
  any(not anchored_seal(ROOT/ref,publication(ROOT/ref)) for ref in q['evidence_references'])):
  raise ValueError('unanchored or stale I5 multi-instance subset')
 missing=['I5/pinned-host-device-workspace-and-event-overlap',
          'I5/parallel-GPU-prefix-and-throughput',
          'I5/original-auto-calibration-and-backend-selection-semantics',
          'I9/fixed-commit-cold-replay-and-independent-review']
 sample.update(status='PARTIAL',level='L4',reason_code='VALIDATED_I5_OPTIMIZED_GPU_JPEG_INSTANCES_SUBSET',
  actual_library='Project HIP multi-stream baseline and optimized JPEG color/downsample/FDCT/quant/Huffman/pack/stuff; CPU libjpeg-turbo standard markers and optimized DHT design',
  backend_library='project HIP full baseline/optimized JPEG encoder + CPU libjpeg-turbo DHT/header design',
  equivalence='GPU_BASELINE_AND_OPTIMIZED_HUFFMAN_WITH_CPU_DHT_DESIGN',selected_validation=q,
  required_cases=q['case_ids']+missing,passed_cases=q['case_ids'],
  reason='原始 C++ 七组 CLI 和16件JPEG独立跨解码通过；13件baseline与旧RGB精确，3件优化产品与同源GPU FDCT plain RGB精确，旧CPU优化结果差异单独留档。baseline 7图/84 GPU kernel，-f优化3图/39 GPU kernel，两条HIP stream及改输入重放通过。CPU仅设计优化DHT/标准header。pinned buffer/事件重叠/自动标定与GPU prefix性能尚未完整验收，因此PARTIAL。',
  cuda_comparison='BLOCKED',cuda_comparison_mode='NATIVE_CUDA_BASELINE_UNAVAILABLE',
  cuda_comparison_reason='历史原生 nvJPEG 编码器 CUDA baseline 未成功构建；本阶段使用独立 libjpeg/Pillow 跨解码与量化表参考，不把它冒充同输入原始 CUDA 入口对照。',
  active_batch='I5',
  retry_condition='完成 pinned host/device workspace/事件重叠、并行 prefix 吞吐和原自动标定/后端选择，补原生CUDA对照与固定提交冷检出。',
  next_step='I5 多实例剩余调度与性能语义；I6–I8 JPEG2000；I9 全局验收。',
  reproduce='HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 python3 tools/moat/image_encoder_instances_build.py\n'
            'HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 /opt/venv/bin/python tools/moat/image_encoder_instances_run.py\n'
            'HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 /opt/venv/bin/python tools/moat/image_encoder_instances_trace.py\n'
            'build/image-cpu-venv/bin/python tools/moat/image_encoder_instances_full_compare.py')
 if not any(a.get('qualification_id')==q['qualification_id'] for a in sample['attempts']):sample['attempts'].append(q)
 for ref in [q['evidence'],q['rocm_evidence'],'migration/reports/image-jpeg-encoder.md',
  'migration/reports/image-jpeg-encoder-instances-runs.json',
  'migration/reports/image-jpeg-encoder-instances-trace.json',
  'migration/reports/image-jpeg-encoder-instances-full-comparison.json']:
  if ref not in sample['evidence']:sample['evidence'].append(ref)
 write(ROOT/'migration/samples.yaml',catalog)
 write(ROOT/'migration/reports/image-jpeg-encoder-instances-publication.json',
  dict(status='PUBLISHED_PARTIAL',sample_id=q['sample_id'],qualification=q['evidence'],
       scope='full-GPU baseline and optimized JPEG entropy; CPU DHT design and original scheduler gaps'))
 record('I5','原始 nvJPEG 多实例编码器16产品/7 CLI、baseline84+优化39 GPU kernel及真实多stream通过；CPU DHT 表设计与调度缺口逐例登记。',[q['evidence'],'migration/reports/image-jpeg-encoder-instances-publication.json'])
 print('Published original encoder PARTIAL')
if __name__=='__main__':main()
