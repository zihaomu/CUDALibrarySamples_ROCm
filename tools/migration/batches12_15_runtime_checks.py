#!/usr/bin/env python3
"""Real MPI/device-count and image descriptor failures must stop before unsafe compute."""
import datetime,json,os,pathlib,subprocess,signal
from catalog import ROOT
from device_guard import allowed_devices
from run import digest,evidence_directory
from batches12_15_spec import kind
out=ROOT/'artifacts'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')/'batches12_15-runtime';out.mkdir(parents=True);devices=allowed_devices();rows=json.loads((ROOT/'migration/reports/batches12_15-rocm.json').read_text());tests=[]
def execute(label,source,args,env,cwd,message):
 d=out/label;d.mkdir();(d/'commands.json').write_text(json.dumps(dict(command=args,cwd=str(cwd),visible_devices=env.get('HIP_VISIBLE_DEVICES')),indent=2)+'\n')
 with (d/'run.log').open('w') as f:
  p=subprocess.Popen(args,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:rc=p.wait(timeout=30)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();rc=124
 log=(d/'run.log').read_text();passed=rc not in [0,124] and message in log;assert passed,(label,rc,log[-1000:]);tests.append(dict(source=source,guard=label,passed=True,return_code=rc,evidence=str(d.relative_to(ROOT))))
geadd=next(r for r in rows if kind(r['source'])=='geadd');mg=next(r for r in rows if kind(r['source'])=='mg_lu');binary=lambda r:str(evidence_directory(r['evidence'])/'sample');mpi=str(ROOT/'build/mpi/bin/mpiexec');env=dict(os.environ,FI_PROVIDER='tcp',MPIR_CVAR_CH4_NETMOD='ofi')
for n in [1,3]:execute('MPI-ranks-'+str(n),geadd['source'],[mpi,'-n',str(n),binary(geadd)],env,ROOT,'requires two ranks')
execute('MPI-one-visible-GPU',geadd['source'],[mpi,'-n','2',binary(geadd)],dict(env,HIP_VISIBLE_DEVICES='2'),ROOT,'requires two ranks')
execute('Mg-one-visible-GPU',mg['source'],[binary(mg)],dict(env,HIP_VISIBLE_DEVICES='2',MIGRATION_OUTPUT_DIR=str(out)),ROOT,'two visible GPUs')
# Isolated, persistent invalid fixtures; qualified inputs are never modified.
for label,k,change in [('truncated-RAW','canny',None),('bad-ROI','canny',(4,999)),('bad-stride','canny',(3,1)),('bad-thresholds','canny',(9,1)),('bad-seed','flood',(11,999)),('bad-template','ncc',(14,999))]:
 row=next(r for r in rows if kind(r['source'])==k);cwd=out/(label+'-root');f=cwd/'build/batch15-fixtures'/k/'original'/'0';f.mkdir(parents=True);params=[13,11,3 if k in ['canny','flood'] else 1,39 if k in ['canny','flood'] else 13,0,0,13,11,50,100,8,1,1,0,8,8,0,0];(f.parent/'count.txt').write_text('1\n')
 if change:params[change[0]]=change[1]
 (f/'params.txt').write_text(' '.join(map(str,params))+'\n');(f/'input.bin').write_bytes(b'x'*(17 if change is None else params[1]*(39 if params[2]==3 else 13)));message='input length' if change is None else 'invalid';execute(label,row['source'],[binary(row)],dict(env,MIGRATION_CASE='original',MIGRATION_OUTPUT_DIR=str(out)),cwd,message)
(ROOT/'migration/reports/batches12_15-runtime-checks.json').write_text(json.dumps(dict(status='PASSED',tests=tests,environment=dict(devices=devices,image_id=os.environ['DEEPINFER_IMAGE_ID'],rocm_release=os.environ['DEEPINFER_ROCM_RELEASE']),generator_sha256=digest(pathlib.Path(__file__))),indent=2)+'\n');print('Runtime guards passed',len(tests))
