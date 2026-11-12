#!/usr/bin/env python3
"""Attach I5 codec prototype logs to three PARTIAL entries without promotion."""
import json
from audit import check as audit_check
from experiment import ROOT,write
from image_progress import record

def main():
 build=json.loads((ROOT/'migration/reports/image-jpeg-encoder-gpu-packing-build.json').read_text())
 runs=json.loads((ROOT/'migration/reports/image-jpeg-encoder-gpu-packing-runs.json').read_text())
 trace=json.loads((ROOT/'migration/reports/image-jpeg-encoder-gpu-packing-trace.json').read_text())
 refs=[build['evidence'],trace['evidence'],*[x['evidence'] for x in runs]]
 if build['status']!='BUILT' or len(runs)!=2 or any(x['status']!='PASSED' for x in runs) or trace['status']!='PASSED' or any(audit_check(ROOT/r) for r in refs):
  raise ValueError('complete sealed GPU Huffman pack/stuff prototype required')
 catalog=json.loads((ROOT/'migration/samples.yaml').read_text())
 names={'nvJPEG/Image-Resize/imageResize.cpp','nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp',
        'nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp'}
 rows=[s for s in catalog['samples'] if s['source'] in names]
 if len(rows)!=3 or any(s['status']!='PARTIAL' for s in rows):raise ValueError('three expected PARTIAL entries required')
 for s in rows:
  for ref in ['migration/reports/image-jpeg-entropy-prototype.md',
              'migration/reports/image-jpeg-encoder-gpu-packing-runs.json',
              'migration/reports/image-jpeg-encoder-gpu-packing-trace.json',*refs]:
   if ref not in s['evidence']:s['evidence'].append(ref)
  s['next_step']='I5 将已验 GPU Huffman/pack/stuff 接入原始编码入口，补并行 prefix/优化表/metadata；I6–I8 JPEG2000。'
 write(ROOT/'migration/samples.yaml',catalog)
 record('I5','三项 PARTIAL JPEG 重编码入口已在逐例证据表链接 GPU Huffman/pack/stuff 原型报告；状态不变，待直接接入生产编码路径。',
        ['migration/reports/image-jpeg-entropy-prototype.md',trace['evidence']])
 print('Attached codec prototype to three PARTIAL entries; no promotion')
if __name__=='__main__':main()
