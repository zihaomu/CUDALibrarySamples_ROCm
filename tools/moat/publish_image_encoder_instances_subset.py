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
  q['kind']!='image-JPEG-multiple-instances-full-GPU-baseline-subset' or q['status']!='PASSED' or
  q['contract_status']!='PARTIAL' or q['case_count']!=9 or len(q['case_ids'])!=9 or
  any(not c['passed'] for c in q['checks']) or
  {k:v for k,v in q.items() if k not in {'qualification_id','evidence'}}!=sealed or
  q['implementation']!=sample['implementation'] or
  q['implementation_sha256']!=digest(ROOT/q['implementation']) or
  any(digest(ROOT/n)!=h for n,h in q['dependencies'].items()) or
  any(not anchored_seal(ROOT/ref,publication(ROOT/ref)) for ref in q['evidence_references'])):
  raise ValueError('unanchored or stale I5 multi-instance subset')
 missing=['I5/GPU-optimized-Huffman-table-generation',
          'I5/pinned-host-device-workspace-and-event-overlap',
          'I5/parallel-GPU-prefix-and-throughput',
          'I5/original-auto-calibration-and-backend-selection-semantics',
          'I9/fixed-commit-cold-replay-and-independent-review']
 sample.update(status='PARTIAL',level='L4',reason_code='VALIDATED_I5_FULL_GPU_JPEG_INSTANCES_SUBSET',
  actual_library='Project HIP multi-stream baseline JPEG color/downsample/FDCT/quant/Huffman/pack/stuff; libjpeg-turbo standard markers and optimized -f fallback',
  backend_library='project HIP full baseline JPEG encoder + libjpeg-turbo optimized Huffman fallback',
  equivalence='GPU_BASELINE_WITH_EXPLICIT_OPTIMIZED_CPU_FALLBACK',selected_validation=q,
  required_cases=q['case_ids']+missing,passed_cases=q['case_ids'],
  reason='原始 C++ 七组 CLI 通过：3张 BMP 自然排序、7次重复、2线程/4状态、Q75/90、420/444、优化 Huffman、硬件不可用/错误输入拒绝；16件JPEG产品独立跨解码与旧路径逐 RGB 字节、采样和量化表一致。非优化 baseline 用 GPU 完成色彩/FDCT/MCU/Huffman/pack/stuff，真实 GPU trace 有7图/84内核、2个独立HIP stream，改输入重放通过。-f 优化 Huffman 仍调用 CPU libjpeg；pinned buffer/事件重叠/自动标定与 GPU prefix 性能尚未完整验收，因此 PARTIAL。',
  cuda_comparison='BLOCKED',cuda_comparison_mode='NATIVE_CUDA_BASELINE_UNAVAILABLE',
  cuda_comparison_reason='历史原生 nvJPEG 编码器 CUDA baseline 未成功构建；本阶段使用独立 libjpeg/Pillow 跨解码与量化表参考，不把它冒充同输入原始 CUDA 入口对照。',
  active_batch='I5',
  retry_condition='完成 GPU 优化 Huffman 表、pinned host/device workspace/事件重叠、并行 prefix 吞吐和原自动标定/后端选择后，补原生CUDA对照与固定提交冷检出。',
  next_step='I5 优化 Huffman 与多实例剩余语义；I6–I8 JPEG2000；I9 全局验收。',
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
       scope='full-GPU baseline JPEG and actual multi-stream subset; optimized -f CPU entropy and original scheduler gaps'))
 record('I5','原始 nvJPEG 多实例编码器 16产品/7 CLI/84 GPU kernel+真实多stream通过；优化 Huffman CPU fallback 与调度缺口逐例登记。',[q['evidence'],'migration/reports/image-jpeg-encoder-instances-publication.json'])
 print('Published original encoder PARTIAL')
if __name__=='__main__':main()
