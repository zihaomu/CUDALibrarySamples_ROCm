#!/usr/bin/env python3
"""Freeze full GPU baseline path for the original multi-instance encoder."""
import json
from experiment import ROOT,Experiment,digest,write
from image_progress import record
PROFILE=ROOT/'migration/rewrite/image-jpeg-encoder-instances-full-gpu-profile.json'
def main():
 if PROFILE.exists():raise ValueError('full GPU multi-instance contract already frozen')
 base=json.loads((ROOT/'migration/rewrite/image-jpeg-encoder-instances-profile.json').read_text())
 runs=json.loads((ROOT/'migration/reports/image-jpeg-encoder-instances-runs.json').read_text())
 trace=json.loads((ROOT/'migration/reports/image-jpeg-encoder-instances-trace.json').read_text())
 if len(runs)!=7 or trace['status']!='PASSED':raise ValueError('previous multi-instance reference incomplete')
 refs=[]
 for row in runs:
  if not row['products']:continue
  evidence=ROOT/row['evidence']
  refs.extend(dict(case=row['case'],file=x['product'],path=str((evidence/'outputs'/x['product']).relative_to(ROOT)),
                   sha256=x['sha256']) for x in row['products'])
 if len(refs)!=16:raise ValueError('16 previous products required')
 e=Experiment('I5','full-GPU-multiple-instance-baseline-contract','CPU-contract',
  sources=[__file__,*[ROOT/x['path'] for x in base['inputs']]])
 profile=dict(status='FROZEN',phase='I5',inputs=base['inputs'],prior_products=refs,
  required_cases=base['required_cases'],
  gates=dict(seven_original_CLI_groups=True,full_GPU_entropy_for_nonoptimized_baseline=True,
             optimized_Huffman_CPU_table_path_explicit=True,
             independent_decode_and_exact_RGB_vs_prior_16_products=True,
             real_multiple_HIP_streams=True,changed_input_replay=True),
  limitations='GPU prefix scan remains serial; optimized Huffman and pinned memory/event overlap remain separate acceptance work.')
 write(e.path/'profile.json',profile);profile['evidence']=e.finish('OBSERVED',dict(status='FROZEN',checks=[dict(check='16-prior-JPEG-product-hashes-and-seven-CLI-groups',passed=True)]))
 write(PROFILE,profile)
 record('I5','原始多实例 encoder 全 GPU baseline 接入合同先冻结：16旧产品、七CLI、多stream与改输入重放；-f 优化表 CPU 路线显式标注。',[profile['evidence']])
 print(profile['evidence'])
if __name__=='__main__':main()
