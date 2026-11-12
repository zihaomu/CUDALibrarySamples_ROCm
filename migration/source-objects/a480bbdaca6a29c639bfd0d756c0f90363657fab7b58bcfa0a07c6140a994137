#!/usr/bin/env python3
"""Freeze I5 full-GPU baseline re-encode integration for two resize entrypoints."""
import json
from experiment import ROOT,Experiment,digest,write
from image_progress import record
from pathlib import Path
PROFILE=ROOT/'migration/rewrite/image-jpeg-encoder-resize-full-gpu-profile.json'
SOURCES=('nvJPEG/Image-Resize/imageResize.cpp','nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp')
def main():
 if PROFILE.exists():raise ValueError('resize GPU encode integration profile already frozen')
 prototype=json.loads((ROOT/'migration/reports/image-jpeg-encoder-full-gpu-runs.json').read_text())
 trace=json.loads((ROOT/'migration/reports/image-jpeg-encoder-full-gpu-trace.json').read_text())
 if len(prototype)!=4 or any(x['status']!='PASSED' for x in prototype) or trace['status']!='PASSED':raise ValueError('full GPU prototype gate incomplete')
 import sys
 sys.path.insert(0,str(ROOT/'tools/migration'))
 from batches9_11_spec import GROUPS
 corpus=ROOT/'nvJPEG/nvJPEG-Decoder/input_images'
 inputs=[dict(path=str(p.relative_to(ROOT)),sha256=digest(p)) for p in sorted(corpus.glob('*.jpg'))]
 if len(inputs)!=12:raise ValueError('original 12-image corpus required')
 e=Experiment('I5','resize-two-original-full-GPU-reencode-contract','CPU-contract',
  sources=[__file__,*[ROOT/s for s in SOURCES],*[ROOT/x['path'] for x in inputs]])
 profile=dict(status='FROZEN',phase='I5',sources=[dict(source=s,cases=GROUPS['b10'][s]) for s in SOURCES],
  original_inputs=inputs,gates=dict(two_original_entries=2,seven_B10_case_groups_each=True,
   all_reencoded_products_use_GPU_FDCT_Huffman_pack_stuff=True,
   no_CPU_entropy_encode=True,independent_CPU_full_pixel_and_file_decode=True,
   same_input_CUDA_math_comparison=True),
  remaining='progressive output mode/APP-COM and quantization-table inheritance; fixed-commit cold review')
 write(e.path/'profile.json',profile);profile['evidence']=e.finish('OBSERVED',dict(status='FROZEN',checks=[dict(check='12-original-images-and-two-seven-case-entries',passed=True)]))
 write(PROFILE,profile)
 record('I5','两个 resize 原始入口的全 GPU baseline JPEG 重编码接入合同先冻结：各七组 B10、12 原图、所有重编码产品无 CPU entropy，独立 CPU/CUDA 数学验收。',[profile['evidence']])
 print(profile['evidence'])
if __name__=='__main__':main()
