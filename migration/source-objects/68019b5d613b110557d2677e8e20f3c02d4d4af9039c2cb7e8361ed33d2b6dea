#!/usr/bin/env python3
"""Collect native allocation evidence separately from unprofiled timings."""
import json,shlex
from experiment import ROOT,Experiment,write
from image_completion_progress import record
from image_encoder_math_binding import sealed

REMOTE='''import hashlib,json,os,pathlib,sqlite3,subprocess,sys
c=json.loads(sys.argv[1]);sha=lambda p:hashlib.file_digest(pathlib.Path(p).open('rb'),'sha256').hexdigest()
for p,h in c['identities'].items():assert sha(p)==h
root=pathlib.Path(c['root']);root.mkdir(parents=True);args=list(c['args'])
if '-o' in args:
 output=root/'products';output.mkdir();args[args.index('-o')+1]=str(output)
print('MEMORY_IDENTITY '+json.dumps(dict(config=c,CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),gpu=subprocess.check_output(['nvidia-smi','--id=1','--query-gpu=name,uuid,pci.bus_id,driver_version','--format=csv,noheader'],text=True).strip(),nsys=subprocess.check_output(['nsys','--version'],text=True))),flush=True)
command=['nsys','profile','--trace=cuda,nvtx','--sample=none','--cpuctxsw=none','--cuda-memory-usage=true','--force-overwrite=true','-o',str(root/'trace'),*args]
print('PROFILE_COMMAND '+json.dumps(command),flush=True);subprocess.run(command,check=True)
subprocess.run(['nsys','export','--type=sqlite','--force-overwrite=true','--output',str(root/'trace.sqlite'),str(root/'trace.nsys-rep')],check=True)
db=sqlite3.connect(root/'trace.sqlite');db.row_factory=sqlite3.Row;tables={}
for row in db.execute("select name,sql from sqlite_master where type='table' and (name like '%MEMORY%' or name like '%MEM_KIND%' or name like '%MEMORY_KIND%' or name like 'ENUM_CUDA%MEM%' or name='TARGET_INFO_CUDA_GPU')"):
 name=row['name'];tables[name]=dict(schema=row['sql'],rows=[dict(r) for r in db.execute('select * from "'+name.replace('"','""')+'"')])
result=dict(tables=tables,files={p.name:dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in root.iterdir() if p.is_file()})
(root/'memory.json').write_text(json.dumps(result,indent=2));print('MEMORY_RESULT '+json.dumps(dict(json_path=str(root/'memory.json'),json_sha256=sha(root/'memory.json'),tables={k:dict(rows=len(v['rows']),schema=v['schema']) for k,v in tables.items()})),flush=True)
'''

def main():
    profile=ROOT/'migration/rewrite/image-encoder-performance-profile.json';p=json.loads(profile.read_text())
    report=ROOT/'migration/reports/image-encoder-performance-native.json';timings=json.loads(report.read_text())
    if [r['case'] for r in timings]!=[c['id'] for c in p['cases']]:raise ValueError('complete native timing set required')
    rows=[]
    for case,timing in zip(p['cases'],timings):
        proof=sealed(timing);commands=json.loads((proof/'commands.json').read_text());log=(proof/commands[0]['stdout']).read_text().splitlines()
        identity=json.loads(next(x.removeprefix('TIMED_IDENTITY ') for x in log if x.startswith('TIMED_IDENTITY ')))
        e=Experiment('I5','encoder-native-peak-allocation-trace','cuda-profiler',case=case['id'],sources=[__file__,profile,report,proof/'result.json',proof/'commands.json',proof/commands[0]['stdout']])
        config=dict(identity['config'],root='/tmp/image-memory-'+e.id)
        rc=e.command(['ssh','nvidia-5090x2',shlex.join(['env','CUDA_VISIBLE_DEVICES=1','python3','-c',REMOTE,json.dumps(config,separators=(',',':'))])],'native-original-allocation-profile',timeout=600)
        checks=[dict(check='profile-and-export',passed=rc==0)];tables={}
        try:
            output=(e.path/e.commands[-1]['stdout']).read_text().splitlines();observed=json.loads(next(x.removeprefix('MEMORY_IDENTITY ') for x in output if x.startswith('MEMORY_IDENTITY ')));receipt=json.loads(next(x.removeprefix('MEMORY_RESULT ') for x in output if x.startswith('MEMORY_RESULT ')))
            cr=e.command(['scp','nvidia-5090x2:'+receipt['json_path'],str(e.path/'memory.json')],'collect-full-memory-events')
            from experiment import digest
            checks.append(dict(check='actual-GPU1-and-event-file',passed=cr==0 and observed['CUDA_VISIBLE_DEVICES']=='1' and '5090' in observed['gpu'] and observed['config']==config and digest(e.path/'memory.json')==receipt['json_sha256']))
            value=json.loads((e.path/'memory.json').read_text());tables={k:dict(rows=len(v['rows']),schema=v['schema']) for k,v in value['tables'].items()}
            checks.append(dict(check='allocation-events-present',passed=any('MEMORY_USAGE' in k and v['rows'] for k,v in value['tables'].items())))
        except Exception as error:checks.append(dict(check='profile-exception',passed=False,error=repr(error)))
        status='OBSERVED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(case=case['id'],status=status,checks=checks,tables=tables,evidence_references=[timing['evidence']],scope='Raw Nsight allocation evidence. Peak reconstruction and coverage validation separate; no profiled throughput used.')
        write(e.path/'result.json',row);row['evidence']=e.finish('OBSERVED' if status=='OBSERVED' else 'PROBE_FAILED',dict(status=status,checks=checks));rows.append(row);write(ROOT/'migration/reports/image-encoder-memory-native.json',rows)
        record('IMG-01','native独立分配trace '+case['id']+'：'+status+'；完整内存事件/原始nsys与SQLite身份保留，峰值另行重建。',[row['evidence']]);print(case['id'],status,{k:v['rows'] for k,v in tables.items()},flush=True)
        if status!='OBSERVED':return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
