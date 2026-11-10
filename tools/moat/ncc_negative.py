#!/usr/bin/env python3
import argparse,json,shutil,struct,sys
from pathlib import Path
from experiment import ROOT,Experiment,write
p=argparse.ArgumentParser();p.add_argument('--single',nargs=3);args=p.parse_args()
if args.single:
 from ncc_reference import validate
 out,log,report=args.single;v=validate(Path(out),Path(log));write(report,v);raise SystemExit(0 if v['status']=='FAILED' else 1)
r=json.loads((ROOT/'migration/reports/rewrite-ncc-rocm.json').read_text())['original'];log=ROOT/r['evidence']/'logs/0001-original-harness.stdout.log';results=[]
for mode in ['scores','annotation','argmax']:
 e=Experiment('R3','NCC/'+mode,'cpu-negative',sources=[__file__,ROOT/'tools/moat/ncc_reference.py'],parent=r['experiment_id']);out=e.path/'outputs';shutil.copytree(ROOT/r['output'],out);config=list(struct.unpack('9i',(out/'config.bin').read_bytes()))
 if mode=='annotation':
  path=out/'match_result.pgm';data=bytearray(path.read_bytes());data[-1]^=1;path.write_bytes(data)
 elif mode=='argmax':config[-2:]=[0,0];(out/'config.bin').write_bytes(struct.pack('9i',*config))
 else:
  path=out/'scores.bin';data=bytearray(path.read_bytes());index=(config[-1]*(config[0]-config[4]+1)+config[-2])*4;value=struct.unpack_from('f',data,index)[0];struct.pack_into('f',data,index,value+.1);path.write_bytes(data)
 report=e.path/'rejected.json';rc=e.command([sys.executable,__file__,'--single',str(out),str(log),str(report)],'reject-'+mode,timeout=120);v=dict(checks=[dict(check='reject-'+mode,passed=rc==0)]);evidence=e.finish('PASSED' if rc==0 else 'VALIDATOR_GAP',v);results.append(dict(mode=mode,passed=rc==0,evidence=evidence));print(mode,rc,flush=True)
write(ROOT/'migration/reports/rewrite-ncc-negative.json',dict(status='PASSED' if all(r['passed'] for r in results) else 'FAILED',tests=results))
