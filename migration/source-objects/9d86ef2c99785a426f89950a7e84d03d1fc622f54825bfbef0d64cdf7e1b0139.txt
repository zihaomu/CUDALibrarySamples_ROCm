#!/usr/bin/env python3
"""Freeze baseline JPEG GPU Huffman prototype bitstream targets."""
import json
from experiment import ROOT,Experiment,digest,write
from image_progress import record

PROFILE=ROOT/'migration/rewrite/image-jpeg-encoder-entropy-profile.json'
def main():
 if PROFILE.exists():raise ValueError('GPU entropy prototype already frozen')
 rows=json.loads((ROOT/'migration/reports/image-jpeg-encoder-runs.json').read_text())
 sources=[]
 for name in ('odd-420','odd-444'):
  row=next(x for x in rows if x['case']==name)
  path=ROOT/row['evidence']/'output.jpg'
  if digest(path)!=row['jpeg_sha256']:raise ValueError('JPEG evidence identity changed')
  sources.append(dict(case=name,path=str(path.relative_to(ROOT)),sha256=digest(path),
                      source_evidence=row['evidence'],bytes=path.stat().st_size))
 e=Experiment('I5','GPU-baseline-Huffman-two-original-project-JPEGs','CPU-contract',
  sources=[__file__,*[ROOT/x['path'] for x in sources]])
 profile=dict(status='FROZEN',phase='I5',scope='GPU Huffman symbol and bit generation from preexisting JPEG coefficient arrays; CPU coefficient extraction and final bit packing are prototype scaffolding',
  inputs=sources,gates=dict(all_inputs=2,exact_entropy_bytes_match_original=True,
   one_real_GPU_Huffman_kernel_per_input=True,physical_GPU1_required=True,
   altered_coefficient_must_change_entropy=True),
  limitations='Does not yet implement GPU prefix scan, byte stuffing, header/metadata preservation or integration into original sample.')
 write(e.path/'profile.json',profile)
 profile['evidence']=e.finish('OBSERVED',dict(status='FROZEN',checks=[dict(check='two-sealed-baseline-JPEG-input-hashes',passed=True)]))
 write(PROFILE,profile)
 record('I5','GPU Huffman 原型先冻结 odd-420/odd-444 两条有效 baseline 码流与逐字节 entropy 目标；'
        'CPU 系数提取/最终拼接仅作原型脚手架，不计完整 GPU encoder。',[profile['evidence']])
 print(profile['evidence'])
if __name__=='__main__':main()
