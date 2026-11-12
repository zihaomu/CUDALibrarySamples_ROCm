#!/usr/bin/env python3
"""Publish Git-anchored full GPU baseline JPEG re-encode subsets."""
import json
from experiment import ROOT,digest,write
from image_progress import record
from selected_proofs import anchored_seal,publication
QUAL=ROOT/'migration/reports/image-jpeg-encoder-full-gpu-resize-qualifications.json'
CATALOG=ROOT/'migration/samples.yaml'
def main():
 qualifiers=json.loads(QUAL.read_text());catalog=json.loads(CATALOG.read_text())
 integration={x['source']:x for x in json.loads((ROOT/'migration/reports/image-jpeg-encoder-full-gpu-integration.json').read_text())}
 products=json.loads((ROOT/'migration/reports/image-jpeg-encoder-full-gpu-products-comparison.json').read_text())
 if len(qualifiers)!=2 or products['status']!='PASSED' or products['compared']!=68:raise ValueError('two complete GPU resize subset proofs and 68 products required')
 for q in qualifiers:
  proof=ROOT/q['evidence'];sealed=json.loads((proof/'qualification.json').read_text())
  sample=next(s for s in catalog['samples'] if s['id']==q['sample_id'])
  if (not anchored_seal(proof,publication(proof),qualification=True) or
   q['kind']!='image-JPEG-full-GPU-baseline-reencode-subset' or q['status']!='PASSED' or
   q['contract_status']!='PARTIAL' or q['case_count']!=10 or len(q['case_ids'])!=10 or
   any(not c['passed'] for c in q['checks']) or
   {k:v for k,v in q.items() if k not in {'qualification_id','evidence'}}!=sealed or
   q['implementation']!=sample['implementation'] or
   q['implementation_sha256']!=digest(ROOT/q['implementation']) or
   any(digest(ROOT/n)!=h for n,h in q['dependencies'].items()) or
   any(not anchored_seal(ROOT/ref,publication(ROOT/ref)) for ref in q['evidence_references'])):
   raise ValueError('unanchored or stale full GPU JPEG subset '+q['sample_id'])
  count=sum(x['encoded_products'] for x in integration[sample['source']]['cases'])
  missing=['I5/source-progressive-output-mode-and-scan-contract',
   'I5/source-quantization-tables-and-APP-COM-metadata-preservation',
   'I5/GPU-prefix-throughput-and-optimized-Huffman',
   'I9/fixed-commit-cold-replay-and-independent-review']
  sample.update(status='PARTIAL',level='L4',reason_code='VALIDATED_I5_FULL_GPU_JPEG_BASELINE_SUBSET',
   actual_library='rocJPEG baseline hardware + project HIP progressive decode + project HIP full baseline JPEG encode (GPU color/FDCT/MCU/Huffman/pack/stuff; CPU marker orchestration)',
   backend_library='rocJPEG + project HIP JPEG decoder/encoder + libjpeg-turbo progressive entropy only',
   equivalence='HYBRID_CPU_GPU',selected_validation=q,
   required_cases=q['case_ids']+missing,passed_cases=q['case_ids'],
   reason=f'七组原登记 CLI/独立 CPU 与同输入 CUDA 数学流程均通过；{count} 件重编码 JPEG 由 AMD GPU 完成色彩/FDCT/MCU/Huffman/scan/pack/stuff，CPU 仅组装标准 baseline marker，禁 CPU 熵编码。两个入口68产品共8,191,374个 RGB 字节与旧独立数值路径完全一致，采样/量化表一致；实际 C++ 入口各12个 GPU JPEG 内核及重放 SHA 已验。源 progressive 输出模式、表及 APP/COM metadata 继承和 GPU prefix 性能尚缺，故 PARTIAL。',
   cuda_comparison='PASSED',cuda_comparison_mode='GPU_BASELINE_PROJECT_JPEG_ENCODE',
   cuda_comparison_reason='七组既有同输入 CUDA 数学对照通过；全 GPU 编码输出还与已冻结旧 HIP FDCT+CPU entropy 参考68产品逐像素一致，不要求合法 JPEG 字节流一致。',
   active_batch='I5',
   retry_condition='完成 progressive 输出/量化表和 APP/COM metadata 继承、并行 GPU prefix 与优化 Huffman/吞吐检查，固定提交冷检出后重新验收。',
   next_step='I5 源编码模式和 metadata 继承、多实例全 GPU 编码；I6–I8 JPEG2000；I9 全局验收。',
   reproduce='HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 python3 tools/moat/image_encoder_full_gpu_integration.py\n'
             'build/image-cpu-venv/bin/python tools/moat/image_encoder_full_gpu_products_compare.py\n'
             'HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 python3 tools/moat/image_encoder_full_gpu_frontend_trace.py')
  if not any(a.get('qualification_id')==q['qualification_id'] for a in sample['attempts']):sample['attempts'].append(q)
  for ref in [q['evidence'],q['rocm_evidence'],'migration/reports/image-jpeg-encoder.md',
              'migration/reports/image-jpeg-encoder-full-gpu-integration.json',
              'migration/reports/image-jpeg-encoder-full-gpu-frontend-trace.json',
              'migration/reports/image-jpeg-encoder-full-gpu-products-comparison.json']:
   if ref not in sample['evidence']:sample['evidence'].append(ref)
  record('I5',sample['source']+f' {count}件全 GPU baseline JPEG 产品/七组原入口/独立CPU与CUDA/实际GPU trace 已绑定主表；源模式metadata缺口仍 PARTIAL。',[q['evidence'],products['evidence']])
 write(CATALOG,catalog)
 write(ROOT/'migration/reports/image-jpeg-encoder-full-gpu-publication.json',
  dict(status='PUBLISHED_PARTIAL',sample_count=2,qualification=QUAL.relative_to(ROOT).as_posix(),
       scope='GPU baseline re-encode subset only; source mode/tables/metadata still incomplete'))
 print('Published two full-GPU baseline JPEG PARTIAL adapters')
if __name__=='__main__':main()
