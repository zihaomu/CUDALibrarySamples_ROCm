#!/usr/bin/env python3
"""Exercise actual Flood Fill publication gates against altered archived records."""
import copy,json,shutil,tempfile
from pathlib import Path
from unittest.mock import patch
from experiment import ROOT,Experiment,write,digest
from image_progress import record
import qualify_image_flood as q
import image_flood_native_reference as native

NAMES=['actual-cold-inventory-pass','actual-cold-full-archive-and-CPU-pass',
       'duplicate-CLI-child','duplicate-original-child','duplicate-relative-path',
       'duplicate-evidence-reference','wrong-original-case','wrong-CLI-case',
       'runtime-report-return-code-changed','CPU-result-status-changed',
       'cold-build-dependency-changed','compiler-output-option-changed',
       'native-execution-recipe-changed','historical-padding-result-changed',
       'cold-output-pixel-with-coupled-hashes-changed']

def run_checks():
 r=q.load('cold');b=q.load('build');checks=[]
 def check(name,fn,wanted=True):
  try:actual=bool(fn())
  except (OSError,ValueError,KeyError,TypeError,IndexError,StopIteration):actual=False
  checks.append(dict(check=name,passed=actual==wanted))
 def mutate(name,edit,inventory=False):
  v=copy.deepcopy(r);edit(v['children'])
  return q.cold_inventory(v['children']) if inventory else q.cold_verify(v,b,set())
 def replace_group(rows,group):
  ix=[i for i,c in enumerate(rows) if c['name']==group];rows[ix[1]]=copy.deepcopy(rows[ix[0]])
 check(NAMES[0],lambda:q.cold_inventory(r['children']))
 check(NAMES[1],lambda:q.cold_verify(r,b,set()))
 check(NAMES[2],lambda:mutate('duplicate-CLI',lambda rows:replace_group(rows,'cli'),True),False)
 check(NAMES[3],lambda:mutate('duplicate-original',lambda rows:replace_group(rows,'originals'),True),False)
 check(NAMES[4],lambda:mutate('duplicate-relative',lambda rows:rows[-1].update(relative=rows[0]['relative']),True),False)
 check(NAMES[5],lambda:mutate('duplicate-evidence',lambda rows:rows[-1]['report'].update(evidence=rows[0]['report']['evidence']),True),False)
 check(NAMES[6],lambda:mutate('original-case',lambda rows:next(c for c in rows if c['name']=='originals')['report'].update(case='never-ran'),True),False)
 check(NAMES[7],lambda:mutate('CLI-case',lambda rows:next(c for c in rows if c['name']=='cli')['report'].update(case='never-ran'),True),False)
 check(NAMES[8],lambda:mutate('runtime-rc',lambda rows:next(c for c in rows if c['name']=='runtime')['report'].update(return_code=1)),False)
 check(NAMES[9],lambda:mutate('CPU-status',lambda rows:next(c for c in rows if c['name']=='all-validation')['report'].update(status='FAILED')),False)
 check(NAMES[10],lambda:mutate('build-deps',lambda rows:next(c for c in rows if c['name']=='build')['report']['dependencies'].update({'rocm/common/image/flood.hip':'0'*64})),False)
 cmd=json.loads((ROOT/b['evidence']/'commands.json').read_text())[0]
 bad=copy.deepcopy(cmd);bad['argv'][-1]='/tmp/other-library.so'
 check(NAMES[11],lambda:q.build_command(b,bad),False)
 with patch.object(native,'receipt_code',lambda:'pass'):
  check(NAMES[12],lambda:native.validate(q.native_run())['status']=='PASSED',False)
 original_load=q.load
 def altered(name):
  v=original_load(name)
  if name=='legacy-padding-failure':
   v=copy.deepcopy(v);v['status']='PASSED';v['observed']['padding_after']=197;v['checks']=[dict(check=c['check'],passed=True) for c in v['checks']]
  return v
 with patch.object(q,'load',altered):
  check(NAMES[13],lambda:next(c for c in q.collect(None)[0] if c['check']=='same-one-pixel-padding-counterexample-now-rejected')['passed'],False)
 meta=json.loads((ROOT/r['evidence']/'manifest.json').read_text());source=ROOT/meta['raw_artifact_dir'];one=next(c for c in r['children'] if c['name']=='all')
 with tempfile.TemporaryDirectory(prefix='flood-cold-validator-') as temporary:
  root=Path(temporary);target=root/one['relative'];target.parent.mkdir(parents=True)
  for group in {c['name'] for c in r['children']}:
   if group!='all':(root/'child-evidence'/group).symlink_to(source/'child-evidence'/group,target_is_directory=True)
  shutil.copytree(source/one['relative'],target)
  output=target/'outputs/exact-original/output.bin';data=bytearray(output.read_bytes());data[0]^=1;output.write_bytes(data)
  runs=target/'outputs/runs.json';rows=json.loads(runs.read_text());next(x for x in rows if x['case']=='exact-original')['files']['output.bin']['sha256']=digest(output);write(runs,rows)
  seal=target/'child-seal.json';members=json.loads(seal.read_text());
  for file in ['outputs/exact-original/output.bin','outputs/runs.json']:
   members['files'][file]=dict(bytes=(target/file).stat().st_size,sha256=digest(target/file))
  write(seal,members)
  check(NAMES[14],lambda:q.cold_verify(r,b,set(),raw_override=root),False)
 if len(checks)!=len(NAMES) or [c['check'] for c in checks]!=NAMES:raise ValueError('all fixed Flood Fill qualification checks')
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',case_count=len(checks),checks=checks)

def main():
 path=ROOT/'migration/rewrite/image-flood-qualification-validator-cases.json'
 if not path.exists():
  e=Experiment('I3','FloodFill-qualification-check-contract','CPU-contract',sources=[__file__,ROOT/'migration/rewrite/image-flood-profile.json']);write(path,NAMES);write(e.path/'cases.json',NAMES);v=dict(status='FROZEN',case_count=len(NAMES));write(e.path/'contracts.json',v);v['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-flood-qualification-check-contracts.json',v);record('I3','Flood资格发布门'+str(len(NAMES))+'项归档/编译/旧反例/原生执行负向检查合同固定。',[v['evidence']])
 if json.loads(path.read_text())!=NAMES:raise ValueError('fixed qualification check list')
 e=Experiment('I3','FloodFill-qualification-and-cold-archive-validator-checks','CPU-validator-test',sources=[__file__,path,ROOT/'tools/moat/qualify_image_flood.py',ROOT/'tools/moat/image_flood_native_reference.py',ROOT/'migration/rewrite/image-flood-profile.json'])
 try:v=run_checks()
 except Exception as error:v=dict(status='FAILED',checks=[dict(check='all-actual-qualification-mutations',passed=False,error=repr(error))])
 write(e.path/'checks.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'SELF_TEST_FAILED',dict(status=v['status'],checks=v['checks']));write(ROOT/'migration/reports/image-flood-qualification-checks.json',v);record('I3','Flood资格门'+str(len(NAMES))+'项真实历史padding/源命令/重复子记录/摘要/像素和配对hash反例：'+v['status'],[v['evidence']]);print(v['status'],v.get('case_count'),[c for c in v['checks'] if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
