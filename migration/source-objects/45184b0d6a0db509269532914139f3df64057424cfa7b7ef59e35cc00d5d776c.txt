#!/usr/bin/env python3
"""Run GPU Huffman prefix/packing/stuffing against sealed baseline entropy bytes."""
import json
from experiment import ROOT,Experiment,digest,write
from image_progress import record
from snapshot import capture
PROFILE=ROOT/'migration/rewrite/image-jpeg-encoder-gpu-packing-profile.json'
BUILD=ROOT/'migration/reports/image-jpeg-encoder-gpu-packing-build.json'
REPORT=ROOT/'migration/reports/image-jpeg-encoder-gpu-packing-runs.json'
def main():
 profile=json.loads(PROFILE.read_text());build=json.loads(BUILD.read_text());rows=[]
 if build['status']!='BUILT' or any(digest(ROOT/n)!=h for n,h in build['dependencies'].items()) or digest(ROOT/build['binary'])!=build['binary_sha256']:raise ValueError('stale Huffman build')
 for item in profile['inputs']:
  source=ROOT/item['path'];assert digest(source)==item['sha256']
  e=Experiment('I5','GPU-JPEG-Huffman-prefix-pack-stuff-byte-parity','rocm-prototype',case=item['case'],
   sources=[__file__,PROFILE,BUILD,source,ROOT/'rocm/probes/image/jpeg_huffman_pack_gpu.hip'],parent=build['experiment_id'])
  write(e.path/'backend.observed.json',capture());gpu=e.path/'gpu.entropy';ref=e.path/'original.entropy'
  rc=e.command([str(ROOT/build['binary']),str(source),str(gpu),str(ref)],'GPU-Huffman-prefix-pack-stuff',timeout=300)
  output=(e.path/'logs/0001-GPU-Huffman-prefix-pack-stuff.stdout.log').read_text()
  metadata=json.loads(output.splitlines()[-1]) if output.strip() else {}
  actual=gpu.read_bytes() if gpu.is_file() else b'';expected=ref.read_bytes() if ref.is_file() else b''
  mismatch=next((i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b),None)
  checks=[dict(check='GPU-command-exit-zero',passed=rc==0),
   dict(check='nonempty-entropy',passed=bool(actual) and bool(expected)),
   dict(check='exact-GPU-Huffman-entropy-byte-parity',passed=actual==expected,
        first_mismatch=mismatch,gpu_bytes=len(actual),original_bytes=len(expected)),
   dict(check='declared-GPU-Huffman-and-CPU-packing-boundary',passed=
        metadata.get('gpu_huffman') is True and metadata.get('cpu_bit_packing') is False and
        metadata.get('gpu_prefix_pack_stuff') is True and
        metadata.get('cpu_coefficient_extract') is True)]
  status='PASSED' if all(c['passed'] for c in checks) else 'NUMERIC_MISMATCH'
  row=dict(case=item['case'],status=status,return_code=rc,checks=checks,metadata=metadata,
   gpu_sha256=digest(gpu) if gpu.is_file() else None,original_sha256=digest(ref) if ref.is_file() else None,
   experiment_id=e.id)
  write(e.path/'run.json',row);row['evidence']=e.finish(status,dict(status=status,checks=checks));rows.append(row);write(REPORT,rows)
  record('I5',item['case']+' GPU Huffman+prefix/pack/stuff 码流与原 JPEG entropy 逐字节比对：'+status+
   '，GPU '+str(len(actual))+' B / 原 '+str(len(expected))+' B。',[row['evidence']]);print(item['case'],status,len(actual),len(expected),mismatch,flush=True)
 return int(any(r['status']!='PASSED' for r in rows))
if __name__=='__main__':raise SystemExit(main())
