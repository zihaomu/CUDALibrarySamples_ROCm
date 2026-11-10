#!/usr/bin/env python3
"""Real file CLI boundary checks and explicit unsupported JPEG backend rejection."""
import datetime,json,os,pathlib
from catalog import ROOT
from device_guard import allowed_devices
from run import digest,command,evidence_directory
def observed(p):return {x['observe']:x['values'] for line in p.read_text().splitlines() if line.startswith('{"observe":') for x in [json.loads(line)]}
out=ROOT/'artifacts'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')/'batches9_11-runtime';out.mkdir(parents=True);devices=allowed_devices();tests=[];rows=json.loads((ROOT/'migration/reports/batches9_11-rocm.json').read_text())
files=[];expected=[]
for n in [0,1,65536,65537]:
 p=out/('file-'+str(n)+'.dat');data=bytes((i*17+3)%256 for i in range(n));p.write_bytes(data);files.append(str(p));expected.extend([data[i:i+65536] for i in range(0,n,65536)] or [b''])
for row in [r for r in rows if r['batch']=='b9' and '_cpu_' in r['source']]:
 binary=str(evidence_directory(row['evidence'])/'sample')
 for label,args,success,inputs in [('mixed-files',['-f']+files+['-i','3','-w','1'],True,expected),('empty-file',['-f',files[0]],True,[b'']),('missing-file',['-f',str(out/'missing')],False,[]),('unknown-flag',['--csv'],False,[]),('iteration-boundary',['-i','2','-w','2'],False,[])]:
  d=out/(row['source'].replace('/','_')+'-'+label);d.mkdir();cmd=[binary]+args;rc=command(cmd,ROOT,d/'run.log',dict(os.environ,MIGRATION_CASE='original',MIGRATION_OUTPUT_DIR=str(d)),120);log=(d/'run.log').read_text();passed=rc==0 if success else rc!=0
  if success:
   o=observed(d/'run.log');passed=passed and o['input_lengths']==[len(x) for x in inputs] and all((d/('gpu_decoded_'+str(i)+'.bin')).read_bytes()==x for i,x in enumerate(inputs))
  assert passed,(row['source'],label,rc,log[-500:]);(d/'commands.json').write_text(json.dumps(cmd,indent=2)+'\n');tests.append(dict(source=row['source'],case=label,passed=bool(passed),expected_success=success,return_code=rc,evidence=str(d.relative_to(ROOT))))
row=next(r for r in rows if 'nvJPEGROIDecode.cpp' in r['source']);binary=str(evidence_directory(row['evidence'])/'sample');image=str(ROOT/'tests/fixtures/batch10/420.jpg')
for label,args in [('hybrid-backend',['-backend','1']),('decoupled-pipeline',['-pipelined']),('non-RGB-ROI',['-fmt','nv12','-roi','1,2,3,4'])]:
 d=out/label;d.mkdir();cmd=[binary,'-i',image]+args;rc=command(cmd,ROOT,d/'run.log',dict(os.environ),60);log=(d/'run.log').read_text();passed=rc==3 and 'RESULT status=PASS' not in log;assert passed,(label,rc,log);(d/'commands.json').write_text(json.dumps(cmd,indent=2)+'\n');tests.append(dict(source=row['source'],case=label,passed=passed,expected_success=False,return_code=rc,evidence=str(d.relative_to(ROOT))))
(ROOT/'migration/reports/batches9_11-runtime-checks.json').write_text(json.dumps(dict(status='PASSED',tests=tests,environment=dict(devices=devices,image_id=os.environ['DEEPINFER_IMAGE_ID'],rocm_release=os.environ['DEEPINFER_ROCM_RELEASE']),generator_sha256=digest(pathlib.Path(__file__))),indent=2)+'\n');print('Passed runtime checks',len(tests))
