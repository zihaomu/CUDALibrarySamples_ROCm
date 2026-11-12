#!/usr/bin/env python3
"""Run frozen multi-instance JPEG encoder CLI cases and independent cross-decode."""
import io,json,math,shutil
from PIL import Image,JpegImagePlugin
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_progress import record
from snapshot import capture

PROFILE=ROOT/'migration/rewrite/image-jpeg-encoder-instances-profile.json'
BUILD=ROOT/'migration/reports/image-jpeg-encoder-instances-build.json'
REPORT=ROOT/'migration/reports/image-jpeg-encoder-instances-runs.json'
CASES=[('natural-three',['-j','2','-s','2','-b','gpu','-q','75'],3,75,2,False),
 ('repeat-seven',['-n','7','-j','2','-s','4','-b','gpu','-q','75'],7,75,2,False),
 ('optimized-444',['-j','2','-s','2','-b','gpu','-q','90','-p','-f'],3,90,0,True),
 ('default-backend',['-j','2','-s','2','-q','80','-r','2'],3,80,2,False),
 ('hardware-unavailable',['-j','2','-b','hardware'],0,75,2,False),
 ('missing-input',['-j','2'],0,75,2,False),
 ('invalid-quality',['-j','2','-q','0'],0,75,2,False)]

def huffman_segments(path):
 data=path.read_bytes();offset=2;segments=[]
 while offset+4<len(data) and data[offset]==255:
  marker=data[offset+1]
  if marker==0xda:break
  length=(data[offset+2]<<8)|data[offset+3]
  if length<2 or offset+2+length>len(data):raise ValueError('invalid JPEG marker length')
  if marker==0xc4:segments.append(data[offset:offset+2+length])
  offset+=length+2
 return segments

def main():
 profile=json.loads(PROFILE.read_text());build=json.loads(BUILD.read_text())
 if build['status']!='BUILT' or any(digest(ROOT/n)!=h for n,h in build['dependencies'].items()) or digest(ROOT/build['binary'])!=build['binary_sha256']:
  raise ValueError('current encoder build required')
 inputs=sorted((ROOT/x['path'] for x in profile['inputs']),key=lambda p:int(p.stem[3:]))
 if any(digest(ROOT/x['path'])!=x['sha256'] for x in profile['inputs']):raise ValueError('BMP identity drift')
 rows=[]
 for name,args,count,quality,sampling,optimize in CASES:
  e=Experiment('I5','nvJPEG-Encoder-MultipleInstances-original-CLI','rocm-original-entry',case=name,
   sources=[__file__,PROFILE,BUILD,*inputs,ROOT/'rocm/common/image/jpeg_encoder_instances.hpp',
            ROOT/'rocm/common/image/jpeg_encoder_gpu.hpp',ROOT/'rocm/common/image/jpeg_full_gpu.hpp',
            ROOT/'rocm/common/image/jpeg_entropy_gpu.hpp'],parent=build['experiment_id'])
  write(e.path/'backend.observed.json',capture());out=e.path/'outputs';out.mkdir()
  directory=e.path/'missing' if name=='missing-input' else inputs[0].parent
  argv=[str(ROOT/build['binary']),'-i',str(directory),'-o',str(out),*args]
  rc=e.command(argv,'original-multi-instance-'+name,timeout=300)
  products=sorted(out.glob('*.jpg'),key=lambda p:int(p.stem))
  checks=[dict(check='expected-CLI-return-code',passed=(rc==0)==(count>0)),
          dict(check='exact-number-of-numbered-JPEG-products',passed=len(products)==count and
               {p.name for p in products}=={str(i)+'.jpg' for i in range(count)})]
  metrics=[]
  if count and rc==0:
   log=(e.path/f'logs/0001-original-multi-instance-{name}.stdout.log').read_text()
   checks.append(dict(check='baseline-GPU-entropy-or-explicit-optimized-CPU-path',passed=
      ('cpu_entropy=1 gpu_full_encode=0' if optimize else 'cpu_entropy=0 gpu_full_encode=1') in log))
   for i,path in enumerate(products):
    source=inputs[i%len(inputs)]
    with Image.open(source) as src:rgb=np.asarray(src.convert('RGB'))
    with Image.open(path) as jpg:
     jpg.load();pixels=np.asarray(jpg.convert('RGB'));actual_sampling=JpegImagePlugin.get_sampling(jpg);quant=jpg.quantization
    ref=io.BytesIO();Image.fromarray(rgb,'RGB').save(ref,format='JPEG',quality=quality,subsampling=sampling,optimize=optimize)
    ref.seek(0)
    with Image.open(ref) as cpu:expected_quant=cpu.quantization
    delta=pixels.astype(np.float64)-rgb.astype(np.float64)
    mse=float(np.mean(delta*delta));psnr=float('inf') if mse==0 else 10*math.log10(255*255/mse)
    good=pixels.shape==rgb.shape and actual_sampling==sampling and quant==expected_quant
    checks.append(dict(check='independent-decode-geometry-sampling-quant-'+str(i),passed=good,
                       width=pixels.shape[1],height=pixels.shape[0],sampling=actual_sampling,psnr_db=psnr))
    metrics.append(dict(product=path.name,source=source.name,sha256=digest(path),bytes=path.stat().st_size,
                        psnr_db=psnr,sampling=actual_sampling,quantization_matches=quant==expected_quant))
   if name=='repeat-seven':
    checks.append(dict(check='repeated-input-gives-deterministic-bitstream',
                       passed=all(metrics[i]['sha256']==metrics[i+3]['sha256'] for i in range(4))))
   if name=='default-backend':
    log=(e.path/'logs/0001-original-multi-instance-default-backend.stdout.log').read_text()
    checks.append(dict(check='hardware-capability-not-fabricated',passed=
                       'Num hardware encode engines: 0' in log and
                       'hardware_encoder=0' in log and 'Enabled backends: gpu' in log))
   if name=='optimized-444':
    plain=e.path/'plain-output';plain.mkdir()
    plain_rc=e.command([str(ROOT/build['binary']),'-i',str(directory),'-o',str(plain),
      '-j','2','-s','2','-b','gpu','-q','90','-p'],
      'same-quality-without-optimized-Huffman',timeout=300)
    changed=plain_rc==0 and all(huffman_segments(out/(str(i)+'.jpg'))!=
      huffman_segments(plain/(str(i)+'.jpg')) for i in range(3))
    checks.append(dict(check='optimized-Huffman-actually-changes-DHT-tables',passed=changed))
  else:
   stderr=(e.path/f'logs/0001-original-multi-instance-{name}.stderr.log').read_text()
   checks.append(dict(check='failure-reported-without-false-PASS',passed=
                      'RESULT status=FAIL' in stderr and 'RESULT status=PASS' not in stderr))
  status='PASSED' if all(x['passed'] for x in checks) else 'FAILED'
  row=dict(case=name,status=status,return_code=rc,checks=checks,products=metrics,
           experiment_id=e.id)
  write(e.path/'result.json',row)
  row['evidence']=e.finish('PASSED' if status=='PASSED' and rc==0 else
                          'EXPECTED_REJECTION' if status=='PASSED' else 'NUMERIC_MISMATCH',
                          dict(status=status,checks=checks))
  rows.append(row);write(REPORT,rows)
  record('I5','原始多实例编码器 '+name+'：'+status+'，产品 '+str(len(products))+' 件；'+
         ('优化 Huffman 使用 CPU entropy。' if optimize else 'baseline 全 GPU entropy。'),[row['evidence']])
  print(name,status,len(products),flush=True)
 return int(any(x['status']!='PASSED' for x in rows))
if __name__=='__main__':raise SystemExit(main())
