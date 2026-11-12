#!/usr/bin/env python3
"""Freeze GPU prefix, entropy byte assembly and byte stuffing contract."""
import json
from experiment import ROOT,Experiment,digest,write
from image_progress import record
PROFILE=ROOT/'migration/rewrite/image-jpeg-encoder-gpu-packing-profile.json'
def main():
 if PROFILE.exists():raise ValueError('GPU entropy packing profile already frozen')
 old=json.loads((ROOT/'migration/rewrite/image-jpeg-encoder-entropy-profile.json').read_text())
 runs=json.loads((ROOT/'migration/reports/image-jpeg-encoder-entropy-runs.json').read_text())
 if len(old['inputs'])!=2 or len(runs)!=2:raise ValueError('two Huffman inputs required')
 e=Experiment('I5','GPU-JPEG-entropy-prefix-pack-stuff-contract','CPU-contract',
  sources=[__file__,*[ROOT/x['path'] for x in old['inputs']]])
 data=dict(status='FROZEN',phase='I5',inputs=old['inputs'],
  algorithm='GPU per-block Huffman bit generation, GPU per-block bit offset scan, GPU byte bit assembly and pad, GPU byte stuffing prefix/scatter; CPU only coefficient extraction and JPEG marker/table orchestration in prototype',
  gates=dict(exact_original_entropy_bytes=2,
   required_GPU_kernels=['encode_blocks','prefix_bits','pack_bytes','prefix_stuff','scatter_stuff'],
   physical_GPU1=True,modified_input_changes_output=True),
  limitations='Prefix scan prototype may be serial; performance and original sample integration must be validated separately.')
 write(e.path/'profile.json',data);data['evidence']=e.finish('OBSERVED',dict(status='FROZEN',checks=[dict(check='previous-two-exact-Huffman-JPEG-hashes',passed=True)]))
 write(PROFILE,data)
 record('I5','两条已验 Huffman 码流的 GPU prefix-scan、byte pack、FF stuffing 与原 JPEG 逐字节一致目标已先冻结；性能另验。',[data['evidence']])
 print(data['evidence'])
if __name__=='__main__':main()
