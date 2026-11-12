#!/usr/bin/env python3
"""Freeze a combined GPU FDCT-to-Huffman baseline JPEG prototype contract."""
import json
from experiment import ROOT,Experiment,digest,write
from image_progress import record
PROFILE=ROOT/'migration/rewrite/image-jpeg-encoder-full-gpu-profile.json'
def main():
 if PROFILE.exists():raise ValueError('combined GPU encoder profile already frozen')
 pixels=json.loads((ROOT/'migration/rewrite/image-jpeg-encoder-gpu-profile.json').read_text())
 runs=json.loads((ROOT/'migration/reports/image-jpeg-encoder-runs.json').read_text())
 inputs=[]
 for item in pixels['inputs']:
  reference=next(x for x in runs if x['case']==item['case']);jpeg=ROOT/reference['evidence']/'output.jpg'
  if digest(jpeg)!=reference['jpeg_sha256'] or digest(ROOT/item['path'])!=item['sha256']:
   raise ValueError('frozen RGB/reference JPEG identity drift')
  inputs.append(dict(**item,reference_jpeg=str(jpeg.relative_to(ROOT)),
   reference_jpeg_sha256=reference['jpeg_sha256']))
 e=Experiment('I5','combined-GPU-JPEG-encode-contract','CPU-contract',
  sources=[__file__,*[ROOT/x['path'] for x in inputs],*[ROOT/x['reference_jpeg'] for x in inputs]])
 profile=dict(status='FROZEN',phase='I5',inputs=inputs,
  algorithm='HIP RGB-to-YCbCr/chroma, FDCT/quant, MCU gather, DC/AC Huffman, GPU bit scan/pack/stuff; CPU only JPEG baseline marker/table orchestration',
  gates=dict(all_inputs=4,independent_JPEG_decode=True,
   decoded_RGB_exactly_matches_previous_GPU_FDCT_CPU_entropy_baseline=True,
   quantization_and_sampling_exact=True,real_GPU_kernel_trace=True,
   no_CPU_entropy_encode_path=True, malformed_input_rejected=True),
  limitations='Baseline 3-component 420/444 with standard Huffman tables; optimized Huffman, progressive output, APP/COM metadata, restart and throughput validation remain separate.')
 write(e.path/'profile.json',profile)
 profile['evidence']=e.finish('OBSERVED',dict(status='FROZEN',checks=[dict(check='four-source-RGB-and-reference-JPEG-hashes',passed=True)]))
 write(PROFILE,profile)
 record('I5','GPU JPEG 全链原型四输入及已验 GPU FDCT+CPU entropy 参考先冻结；新输出要求独立解码像素精确一致，禁止 CPU entropy encode。',[profile['evidence']])
 print(profile['evidence'])
if __name__=='__main__':main()
