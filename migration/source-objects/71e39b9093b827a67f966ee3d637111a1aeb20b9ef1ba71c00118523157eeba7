#!/usr/bin/env python3
import hashlib,json
from experiment import ROOT,write,digest
cases=[('original-auto',0,False,0,'crc32_perf.csv'),('storage-small',1<<20,False,0,'crc32_perf.csv'),('complete-small',1<<20,True,0,'complete.csv'),('changed-input',1<<20,False,7,'changed.csv'),('repeat',1<<16,False,0,'output with spaces.csv')]
rows=[]
for name,storage,complete,seed,csv in cases:
 path=ROOT/'tests/fixtures/rewrite-crc-benchmark'/name;path.mkdir(parents=True,exist_ok=True);argv=[]
 if complete:argv+=['-c']
 if storage:argv+=['-s',str(storage)]
 if csv!='crc32_perf.csv':argv+=['-o',csv]
 files={};input_hash=None
 if storage:
  raw=bytes(((i*17)^(i>>8)^(seed*31))&255 for i in range(storage));(path/'input.bin').write_bytes(raw);input_hash=hashlib.sha256(raw).hexdigest();files['input.bin']=dict(sha256=input_hash,bytes=len(raw))
 row=dict(case=name,storage=storage,complete=complete,csv=csv,argv=argv,input_sha256=input_hash,kind='crc32-benchmark',files=files)
 write(path/'case.json',row);files['case.json']=dict(sha256=digest(path/'case.json'),bytes=(path/'case.json').stat().st_size)
 write(path/'manifest.json',dict(kind='crc32-benchmark',case=name,files=files));rows.append(row)
write(ROOT/'migration/rewrite/crc-benchmark-cases.json',rows);print('Frozen five benchmark cases, including original auto policy')
