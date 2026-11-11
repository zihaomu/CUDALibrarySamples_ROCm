#!/usr/bin/env python3
"""Independent original grid/CSV model and standard-library zlib full CRC oracle."""
import argparse,csv,json,math,mmap,struct,zlib,hashlib
from pathlib import Path

def human(value,byte=False):
 suffix=''
 for threshold,name in [(1<<30,'Gi'),(1<<20,'Mi'),(1<<10,'Ki')]:
  if value>=threshold:value//=threshold;suffix=name;break
 return str(value)+suffix+('B' if byte else '')
def validate(out,case,backend='rocm'):
 out=Path(out);grid=json.loads((out/'grid.json').read_text());memory=json.loads((out/'memory.json').read_text());checks=[]
 def check(name,value,**kw):checks.append(dict(check=name,passed=bool(value),**kw))
 complete=case['complete'];minimum=1024 if complete else 32768;maximum=32*(1<<30) if complete else 1<<30;maxcount=1<<20 if complete else 1<<16;shift=1 if complete else 3
 limit=1<<(int(memory['total']*.9).bit_length()-1);storage=case['storage'] or min(limit,maxcount*maximum)
 sizes=[];counts=[];n=minimum
 while n<=maximum and n<=storage:sizes.append(n);n<<=shift
 n=1
 while n<=maxcount and n*minimum<=storage:counts.append(n);n<<=shift
 expected=dict(storage=storage,min_size=minimum,max_size=maximum,min_count=1,max_count=maxcount,step_shift=shift,sizes=sizes,counts=counts)
 check('exact-original-grid-and-memory-policy',grid==expected)
 check('exact-generated-input-length',(out/'input.bin').stat().st_size==storage)
 if case.get('input_sha256'):check('same-frozen-input-bytes',hashlib.file_digest(open(out/'input.bin','rb'),'sha256').hexdigest()==case['input_sha256'])
 csvpath=out/case['csv'];rows=list(csv.reader(csvpath.open()));check('CSV-exact-axes-and-rectangular-shape',len(rows)==len(sizes)+1 and rows[0]==['Size \\ Count']+[human(n) for n in counts] and all(len(row)==len(counts)+1 and row[0]==human(size,True) for row,size in zip(rows[1:],sizes)))
 search=[json.loads(s) for s in (out/'search.jsonl').read_text().splitlines()] if backend=='rocm' and (out/'search.jsonl').exists() else []
 cells=[];valid_count=0;skipped=0
 with (out/'input.bin').open('rb') as file,mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as mapped:
  for i,size in enumerate(sizes):
   for j,count in enumerate(counts):
    value=float(rows[i+1][j+1]);prefix='cell_'+str(size)+'_'+str(count)
    if size*count>storage:
     skipped+=1;check(prefix+'-skipped-only-for-capacity',value==-1 and not (out/(prefix+'_final.bin')).exists());continue
    valid_count+=1;timing=json.loads((out/(prefix+'_timing.json')).read_text());ms=timing['elapsed_ms'];check(prefix+'-finite-positive-event-and-throughput',math.isfinite(ms) and ms>0 and math.isfinite(value) and value>0 and timing['size']==size and timing['count']==count)
    if ms>0 and math.isfinite(ms):check(prefix+'-decimal-GB-per-second',math.isclose(value,(size*count/1e9)/(ms/1000),rel_tol=2e-5))
    expected_crc=[zlib.crc32(memoryview(mapped)[h*size:(h+1)*size]) for h in range(count)];gold=struct.pack('<'+str(count)+'I',*expected_crc)
    check(prefix+'-independent-zlib-all-chunks',(out/(prefix+'_final.bin')).read_bytes()==gold)
    if backend=='rocm':
     candidates=[r for r in search if r['size']==size and r['count']==count];check(prefix+'-three-real-search-configurations',len(candidates)==3 and {r['segment'] for r in candidates}=={256,1024,4096} and all(math.isfinite(r['elapsed_ms']) and r['elapsed_ms']>0 for r in candidates))
     for segment in [256,1024,4096]:check(prefix+'-candidate-'+str(segment)+'-zlib',(out/(prefix+'_segment'+str(segment)+'.bin')).read_bytes()==gold)
     selected=json.loads((out/(prefix+'_selected.json')).read_text());chosen=[r for r in candidates if r['segment']==selected['segment'] and r['threads']==selected['threads']];check(prefix+'-selected-measured-minimum',len(chosen)==1 and chosen[0]['elapsed_ms']==min(r['elapsed_ms'] for r in candidates))
    cells.append(dict(size=size,count=count,crcs=expected_crc))
 check('complete-search-cell-set',backend!='rocm' or len(search)==valid_count*3)
 return dict(status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED',checks=checks,valid_cells=valid_count,skipped_cells=skipped,rows=len(sizes),columns=len(counts),storage=storage,cells=cells,oracle='Independent original CLI/grid model and zlib IEEE CRC32; all final chunks plus all AMD search candidates, full CSV/timing semantics; no cross-device speed claim')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--case',required=True);p.add_argument('--report',required=True);p.add_argument('--backend',default='rocm');a=p.parse_args();case=json.loads(Path(a.case).read_text());r=validate(a.output,case,a.backend);Path(a.report).write_text(json.dumps(r,indent=2)+'\n');print(r['status'],r['valid_cells'],r['skipped_cells']);raise SystemExit(r['status']!='PASSED')
