#!/usr/bin/env python3
"""Compare every original resize JPEG product by independent decoded pixels."""
import json
import numpy as np
from PIL import Image,JpegImagePlugin
from experiment import ROOT,Experiment,digest,write
from image_progress import record
PROFILE=ROOT/'migration/rewrite/image-jpeg-encoder-full-gpu-products-profile.json'
REPORT=ROOT/'migration/reports/image-jpeg-encoder-full-gpu-products-comparison.json'
def main():
 profile=json.loads(PROFILE.read_text());integration=json.loads((ROOT/'migration/reports/image-jpeg-encoder-full-gpu-integration.json').read_text())
 e=Experiment('I5','all-68-original-resize-JPEG-independent-pixel-comparison','CPU-reference',
  sources=[__file__,PROFILE,ROOT/'migration/reports/image-jpeg-encoder-full-gpu-integration.json'],
  parent=profile['evidence'].split('/')[-1])
 rows=[]
 for item in profile['products']:
  left=ROOT/item['old'];right=ROOT/item['gpu']
  if digest(left)!=item['old_sha256'] or digest(right)!=item['gpu_sha256']:
   raise ValueError('frozen JPEG product hash changed')
  with Image.open(left) as old:
   old.load();a=np.asarray(old.convert('RGB'));size=old.size;sampling=JpegImagePlugin.get_sampling(old);quant=old.quantization
  with Image.open(right) as new:
   new.load();b=np.asarray(new.convert('RGB'));same_header=new.size==size and JpegImagePlugin.get_sampling(new)==sampling and new.quantization==quant
  exact=a.shape==b.shape and np.array_equal(a,b)
  rows.append(dict(source=item['source'],product=item['product'],old_sha256=item['old_sha256'],
   gpu_sha256=item['gpu_sha256'],pixel_bytes=int(a.size),exact_pixels=exact,header_sampling_quant_match=same_header,
   max_abs=int(np.max(np.abs(a.astype(np.int16)-b.astype(np.int16)))) if a.shape==b.shape else None))
  if not exact or not same_header:break
 claims=sum(x['encoded_products'] for row in integration for x in row['cases'])==68 and all(
  x['encoder_claims'] for row in integration for x in row['cases'])
 checks=[dict(check='all-68-predeclared-products-compared',passed=len(rows)==68),
  dict(check='all-independent-RGB-pixels-exact',passed=all(x['exact_pixels'] for x in rows)),
  dict(check='all-dimensions-sampling-and-quant-tables-match',passed=all(x['header_sampling_quant_match'] for x in rows)),
  dict(check='all-68-products-report-full-GPU-encode-no-CPU-entropy',passed=claims)]
 status='PASSED' if all(c['passed'] for c in checks) else 'NUMERIC_MISMATCH'
 result=dict(status=status,checks=checks,products=rows,compared=len(rows),
  total_pixel_bytes=sum(x['pixel_bytes'] for x in rows),experiment_id=e.id)
 write(e.path/'comparison.json',result)
 result['evidence']=e.finish(status,dict(status=status,checks=checks));write(REPORT,result)
 record('I5','两个 resize 原入口68件全 GPU entropy JPEG 与旧数值路径独立解码逐像素/采样/量化表检查：'+status+
  '，共 '+str(result['total_pixel_bytes'])+' RGB 字节。',[result['evidence']])
 print(status,len(rows),result['total_pixel_bytes']);return int(status!='PASSED')
if __name__=='__main__':raise SystemExit(main())
