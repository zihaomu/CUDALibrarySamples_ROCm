#!/usr/bin/env python3
import argparse,json,shutil,struct,sys
from pathlib import Path
from experiment import ROOT,Experiment,write
from crc32_reference import validate
p=argparse.ArgumentParser();p.add_argument('--single',nargs=3);a=p.parse_args()
if a.single:
 inputs,out,report=a.single;v=validate(Path(inputs),Path(out));write(report,v);raise SystemExit(0 if v['status']=='FAILED' else 1)
records=json.loads((ROOT/'migration/reports/rewrite-crc32-rocm.json').read_text());modes=['checksum','CRC32C-polynomial','chunk-offset','trailing-checksum-byte','iteration-count','timing-NaN','input-byte','truncate-checksum'];results=[]
for mode in modes:
 case='chunk-boundary' if mode=='chunk-offset' else 'original';r=records[case];e=Experiment('R4','nvCOMP/examples::nvcomp_crc32.cu/negative/'+mode,'cpu-negative',case=case,sources=[__file__,ROOT/'tools/moat/crc32_reference.py'],parent=r['experiment_id'],comparison_id=r['comparison_id']);inputs=e.path/'inputs';shutil.copytree(ROOT/r['input_snapshot'],inputs);out=e.path/'outputs';shutil.copytree(ROOT/r['output'],out)
 if validate(inputs,out)['status']!='PASSED':raise RuntimeError('CRC injection requires valid original output')
 name='offsets.bin' if mode=='chunk-offset' else 'trace.bin' if mode=='iteration-count' else 'timing_ms.bin' if mode=='timing-NaN' else 'input.bin' if mode=='input-byte' else 'crc32.bin';path=out/name;data=bytearray(path.read_bytes())
 if mode=='CRC32C-polynomial':struct.pack_into('<I',data,0,0xe3069283)
 elif mode=='chunk-offset':struct.pack_into('<Q',data,8,struct.unpack_from('<Q',data,8)[0]+1)
 elif mode=='iteration-count':struct.pack_into('<q',data,8,4)
 elif mode=='timing-NaN':struct.pack_into('<f',data,0,float('nan'))
 elif mode=='trailing-checksum-byte':data+=b'\0'
 elif mode=='truncate-checksum':data=data[:-1]
 else:data[0]^=1
 path.write_bytes(data);report=e.path/'rejection.json';rc=e.command([sys.executable,__file__,'--single',str(inputs),str(out),str(report)],'reject-'+mode);ev=e.finish('PASSED' if rc==0 else 'VALIDATOR_GAP',dict(checks=[dict(check=mode,passed=rc==0)]));results.append(dict(mode=mode,case=case,passed=rc==0,evidence=ev));print(mode,rc,flush=True)
write(ROOT/'migration/reports/rewrite-crc32-negative.json',dict(status='PASSED' if all(r['passed'] for r in results) else 'FAILED',tests=results))
