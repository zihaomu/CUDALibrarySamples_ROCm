#!/usr/bin/env python3
"""Seal measured I5 original multi-instance encoder GPU subset as PARTIAL."""
import json
from audit import check as audit_check
from experiment import ROOT,Experiment,digest,git,write
from image_progress import record

REPORT=ROOT/'migration/reports/image-jpeg-encoder-instances-subset-qualification.json'
SAMPLE='nvJPEG/nvJPEG-Encoder-MultipleInstances::nvJPEGEncMultipleInstances.cpp'
def main():
 build=json.loads((ROOT/'migration/reports/image-jpeg-encoder-instances-build.json').read_text())
 runs=json.loads((ROOT/'migration/reports/image-jpeg-encoder-instances-runs.json').read_text())
 trace=json.loads((ROOT/'migration/reports/image-jpeg-encoder-instances-trace.json').read_text())
 profile=json.loads((ROOT/'migration/rewrite/image-jpeg-encoder-instances-profile.json').read_text())
 comparison=json.loads((ROOT/'migration/reports/image-jpeg-encoder-instances-full-comparison.json').read_text())
 full_profile=ROOT/'migration/rewrite/image-jpeg-encoder-instances-full-gpu-profile.json'
 opt_profile=ROOT/'migration/rewrite/image-jpeg-encoder-instances-opt-profile.json'
 optimized=json.loads(opt_profile.read_text())
 refs=[build['evidence'],trace['evidence'],comparison['evidence'],optimized['evidence'],*[x['evidence'] for x in runs]]
 if any(audit_check(ROOT/r) for r in refs):raise ValueError('unsealed I5 instance evidence')
 if build['status']!='BUILT' or len(runs)!=7 or trace['status']!='PASSED' or comparison['status']!='PASSED' or any(x['status']!='PASSED' for x in runs):raise ValueError('incomplete original CLI/trace/comparison')
 source=ROOT/'rocm/ported/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp'
 deps=dict(build['dependencies']);deps[str(source.relative_to(ROOT))]=digest(source)
 checks=[dict(check='seven-predeclared-original-CLI-groups',passed=len(runs)==7 and all(x['status']=='PASSED' for x in runs)),
  dict(check='recursive-natural-BMP-and-seven-numbered-repeat-products',passed=
   next(x for x in runs if x['case']=='natural-three')['products'][0]['source']=='img1.bmp' and
   next(x for x in runs if x['case']=='repeat-seven')['products'][6]['source']=='img1.bmp'),
  dict(check='independent-JPEG-cross-decode-and-quant-sampling-for-all-16-products',passed=
   sum(len(x['products']) for x in runs)==16 and all(c['passed'] for x in runs for c in x['checks'])),
  dict(check='actual-full-JPEG-84-kernels-on-at-least-two-HIP-streams',passed=len(trace['stream_ids'])>=2 and
   trace['kernel_counts']=={'rgb_to_plane':21,'forward_dct_quantize':21,**{x:7 for x in
    ('gather_mcu_coefficients','encode_blocks','prefix_bits','pack_bytes','prefix_stuff','scatter_stuff')}}),
  dict(check='actual-optimized-JPEG-39-kernels-on-at-least-two-HIP-streams',passed=
   len(trace.get('optimized_stream_ids',[]))>=2 and
   trace.get('optimized_kernel_counts')=={'rgb_to_plane':9,'forward_dct_quantize':9,**{x:3 for x in
    ('gather_mcu_coefficients','histogram','encode_blocks','prefix_bits','pack_bytes','prefix_stuff','scatter_stuff')}}),
  dict(check='baseline-and-optimized-full-GPU-entropy-with-CPU-DHT-design',passed=all(
   any(c['check']=='full-GPU-entropy-with-CPU-DHT-only-if-optimized' and c['passed'] for c in row['checks'])
   for row in runs if row['products'])),
  dict(check='thirteen-prior-baseline-products-exact-and-three-optimized-same-GPU-FDCT',passed=
   len(comparison['products'])==16 and all(x['header_sampling_quant_match'] for x in comparison['products']) and
   all(x['exact_decoded_rgb'] for x in comparison['products'] if x['case']!='optimized-444') and
   all(any(c['check']=='optimized-RGB-exact-vs-same-GPU-FDCT-plain-'+str(i) and c['passed']
       for c in next(r for r in runs if r['case']=='optimized-444')['checks']) for i in range(3))),
  dict(check='changed-input-produces-changed-output-and-stable-other-outputs',passed=
   any(c['check']=='changed-source-changes-JPEG-while-others-stable' and c['passed'] for c in trace['checks'])),
  dict(check='optimized-Huffman-DHT-actually-changed',passed=
   any(c['check']=='optimized-Huffman-actually-changes-DHT-tables' and c['passed'] for c in
       next(x for x in runs if x['case']=='optimized-444')['checks'])),
  dict(check='current-source-closure-and-GPU1',passed=
   all(digest(ROOT/n)==h for n,h in deps.items()) and
   all(d['physical_id']==1 for d in json.loads((ROOT/trace['evidence']/'backend.observed.json').read_text())['devices']))]
 if not all(x['passed'] for x in checks):raise ValueError('multi-instance subset check failed')
 e=Experiment('I5',SAMPLE,'composite-subset-qualification',sources=[__file__,source,
  ROOT/'migration/reports/image-jpeg-encoder-instances-runs.json',
  ROOT/'migration/reports/image-jpeg-encoder-instances-trace.json',
  ROOT/'migration/reports/image-jpeg-encoder-instances-full-comparison.json',
  ROOT/'migration/rewrite/image-jpeg-encoder-instances-profile.json',full_profile,opt_profile])
 devices=json.loads((ROOT/trace['evidence']/'backend.observed.json').read_text())['devices']
 q=dict(kind='image-JPEG-multiple-instances-optimized-GPU-subset',status='PASSED',contract_status='PARTIAL',
  sample_id=SAMPLE,implementation=str(source.relative_to(ROOT)),implementation_sha256=digest(source),
  source_commit=git('rev-parse','HEAD').strip(),case_count=10,
  case_ids=['I5/'+x['case'] for x in runs]+['I5/multi-stream-changed-input-replay',
   'I5/sixteen-JPEG-independent-decoded-RGB','I5/optimized-GPU-Huffman-39-kernel-trace'],
  checks=checks,devices=devices,dependencies=deps,evidence_references=refs,
  rocm_evidence=trace['evidence'],cuda_evidence=None,
  comparison_mode='FULL_GPU_BASELINE_AND_OPTIMIZED_JPEG_INDEPENDENT_CPU_DECODE_AND_TRACE',
  remaining='optimized DHT table design on CPU; pinned host/device workspace and event overlap; original auto calibration; parallel prefix throughput and hardware backend unavailable on AMD')
 q['qualification_id']=e.id
 write(e.path/'qualification.json',{k:v for k,v in q.items() if k not in {'qualification_id','evidence'}})
 q['evidence']=e.finish('PASSED',dict(status='PASSED',checks=checks));write(REPORT,q)
 record('I5','原始 nvJPEG 多实例编码器7 CLI、16产品与 baseline 84/优化39 GPU kernel、双stream封存；CPU仅设计优化DHT表，其余调度缺口保留PARTIAL。',[q['evidence']])
 print('MULTI_INSTANCE_SUBSET_PASSED',q['evidence'])
if __name__=='__main__':main()
