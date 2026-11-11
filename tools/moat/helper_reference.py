#!/usr/bin/env python3
"""Independent byte/metadata model; no project descriptor implementation imported."""
import json,struct,argparse
from pathlib import Path
from qualification_common import fixture
from experiment import write

def validate(src,out):
 src=Path(src);out=Path(out);mf=fixture(src,kind='matrix-helpers');cfg=mf['config'];checks=[];kind=cfg['kind'];batch=cfg['batch'];csr=kind!=1;batched=kind==3
 def check(name,ok):checks.append(dict(check=name,passed=bool(ok)))
 def raw(name):return (src/(name+'.bin')).read_bytes()
 def equal(name,expected):
  f=out/(name+'.bin');check(name+'-exact-whole-bytes',f.is_file() and f.read_bytes()==expected)
 def packed(values,code):return struct.pack('<'+str(len(values))+code,*values)
 check('config-JSON-equals-frozen-contract',json.loads((src/'config.json').read_text())==cfg)
 lines=(src/'config.txt').read_text().splitlines();head=lines[0].split()
 check('config-text-equals-frozen-contract',[int(v) for v in head[:4]]==[cfg['kind'],cfg['batch'],cfg['base'],cfg['loops']] and float(head[4])==cfg['inplace'] and int(head[5])==int(cfg['alias_host_shapes']) and len(lines)==cfg['batch']+1 and all([int(v) for v in line.split()]==[o[k] for k in ['nrows','ncols','nnz','new_nnz','ld']] for line,o in zip(lines[1:],cfg['objects'])))
 expected_names=set()
 for iteration in range(cfg['loops']):
  prefix='r'+str(iteration)
  for object_name in ['A']+(['B'] if batched else []):
   dense=object_name=='B' or not csr;format=(1 if dense else 2)+(4 if batched else 0);o=cfg['objects'][0]
   sizes=[batch,o['nrows'],1 if object_name=='B' else o['ncols'],0 if dense else o['nnz'],o['ld'] if dense else 0];codes=[format,10,10,1,0 if dense else 3 if batched else 1,0 if dense else 2,0 if dense else cfg['base'],0];meta=packed(sizes+codes+[1]*8,'q');shapes=[]
   for obj in cfg['objects']:shapes.extend([obj['nrows'],1 if object_name=='B' else obj['ncols'],0 if dense else obj['nnz'],obj['ld'] if dense else 0])
   for stage in ['0','1','2','3','_after_destroy']:
    p=prefix+'_'+object_name+stage;equal(p+'_meta',meta);equal(p+'_shapes',packed(shapes,'i'));expected_names.update([p+'_meta.bin',p+'_shapes.bin'])
    late=stage in ['3','_after_destroy'];rebound=stage in ['2','3','_after_destroy']
    for i,obj in enumerate(cfg['objects']):
     b='b'+str(i);name=p+'_'+b
     values=raw(b+'_B'+('_replacement' if rebound else '')) if object_name=='B' else raw(b+('_final' if late and csr else '_replacement' if rebound else '_values'))
     if object_name=='A' and not batched and stage=='1':values=packed([cfg['inplace']],'d')+values[8:]
     equal(name+'_values',values);expected_names.add(name+'_values.bin')
     if not dense:
      for key in ['rows','columns']:equal(name+'_'+key,raw(b+('_new_' if late else '_')+key));expected_names.add(name+'_'+key+'.bin')
  equal(prefix+'_optional',packed([1]*4,'i'));equal(prefix+'_lifetime',packed([1]*3,'i'));expected_names.update([prefix+'_optional.bin',prefix+'_lifetime.bin'])
  equal(prefix+'_context',packed([1,1,int(batched)],'i'));expected_names.add(prefix+'_context.bin')
  if batched:
   for stage in range(4):
    name=prefix+'_aliases'+str(stage);a=int(cfg['alias_host_shapes']);equal(name,packed([a,1,a,a],'i'));expected_names.add(name+'.bin')
 actual={p.name for p in out.glob('*.bin')};check('complete-output-file-set',actual==expected_names)
 return dict(status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED',checks=checks,oracle='Independent original metadata/mutation protocol and exact complete storage bytes, including padding and post-destroy caller storage')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args();r=validate(a.input,a.output);write(a.report,r);print(r['status'],len(r['checks']));raise SystemExit(r['status']!='PASSED')
