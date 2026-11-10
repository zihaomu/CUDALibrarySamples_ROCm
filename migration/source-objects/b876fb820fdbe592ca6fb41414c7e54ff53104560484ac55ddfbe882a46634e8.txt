#!/usr/bin/env python3
"""Independent zlib IEEE CRC32 and exact file/chunk reconstruction."""
import argparse,json,struct,zlib,sys
from pathlib import Path
from experiment import ROOT,write,digest

def validate(inputs,out):
 m=json.loads((inputs/'manifest.json').read_text());checks=[]
 def gate(name,value,**fields):checks.append(dict(check=name,passed=bool(value),**fields))
 data=b'';offsets=[];sizes=[];expected=[]
 for name in m['argv'][1:]:
  raw=(inputs/name).read_bytes();gate('frozen-file-'+name,digest(inputs/name)==m['files'][name]['sha256'])
  for start in range(0,len(raw),65536):
   chunk=raw[start:start+65536];offsets.append(len(data)+start);sizes.append(len(chunk));expected.append(zlib.crc32(chunk))
  data+=raw
 expected_bytes={'input.bin':len(data),'offsets.bin':len(offsets)*8,'sizes.bin':len(sizes)*8,'crc32.bin':len(expected)*4,'trace.bin':4*8,'timing_ms.bin':4}
 for name,size in expected_bytes.items():gate(name+'-exact-bytes',(out/name).is_file() and (out/name).stat().st_size==size,expected_bytes=size)
 if not all(c['passed'] for c in checks):return dict(status='FAILED',checks=checks)
 def integers(name,code,count):return list(struct.unpack('<'+str(count)+code,(out/name).read_bytes()))
 gate('all-original-file-bytes',(out/'input.bin').read_bytes()==data);gate('per-file-chunk-offsets-exact',integers('offsets.bin','Q',len(offsets))==offsets);gate('per-file-chunk-lengths-exact',integers('sizes.bin','Q',len(sizes))==sizes);gate('zlib-IEEE-CRC32-all-chunks-exact',integers('crc32.bin','I',len(expected))==expected,checksums=expected)
 if data==b'123456789':gate('canonical-IEEE-check-value',expected==[0xcbf43926])
 trace=integers('trace.bin','q',4);gate('two-warmups-five-total-GPU-passes',trace==[2,5,len(sizes),5*int(bool(sizes))]);ms=struct.unpack('<f',(out/'timing_ms.bin').read_bytes())[0];gate('GPU-event-time-finite-nonnegative',ms>=0 and ms<float('inf'),observed_ms=ms)
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,oracle='Python standard-library zlib.crc32, independent native IEEE implementation; per-file chunk boundaries exact')

def validate_rejection(inputs,out,record):
 m=json.loads((inputs/'manifest.json').read_text());checks=[dict(check='frozen-zero-chunk-input',passed=m['expected_run_outcome']=='ZERO_CHUNKS_REJECTED' and all((inputs/name).stat().st_size==0 and digest(inputs/name)==info['sha256'] for name,info in m['files'].items())),dict(check='nonzero-real-process-result',passed=isinstance(record['return_code'],int) and record['return_code']!=0),dict(check='no-checksum-output-on-precondition-error',passed=not (out/'crc32.bin').exists())]
 directory=ROOT/record['evidence'];commands=json.loads((directory/'commands.json').read_text());text='\n'.join((directory/c['stderr']).read_text() for c in commands)
 checks.append(dict(check='documented-zero-chunk-rejection',passed='chunk_count=0' in text or 'nvcompBatchedCRC32GetHeuristicConf() not successful' in text))
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,validation_kind='SEMANTIC_REJECTION',note='Original nvCOMP terminates on its thrown configuration exception; project CLI reports a nonzero error without reproducing the abort signal. No CRC numeric pass is claimed for zero chunks.')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--run-record',type=Path);a=p.parse_args();r=validate_rejection(a.input,a.output,json.loads(a.run_record.read_text())) if a.run_record else validate(a.input,a.output);write(a.report,r);print(json.dumps(r));raise SystemExit(r['status']!='PASSED')
