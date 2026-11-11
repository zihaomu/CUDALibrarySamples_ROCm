#!/usr/bin/env python3
"""Targeted accepted/rejected mutations of the actual contour validators."""
import copy,json,shutil,tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
from experiment import ROOT,Experiment,write,digest
import image_contour_reference as masks
import image_contour_original_reference as originals
import image_contour_data_reference as data_reader
import image_contour_arguments_reference as arg_reader
import image_contour_states_reference as states_reader
from image_progress import record
import image_contour_cli as cli_reader
from qualify_image_contour import cold_inventory,native_result
NAMES=['actual-small-diagnostic-subset-passes','full-cannot-downgrade-to-small','full-missing-big-case-rejected','duplicate-case-rejected','producer-nonzero-rejected','case-nonzero-rejected','wrong-raw-pixel','wrong-label-pixel','wrong-mask-pixel','wrong-mask-padding','missing-geometry-edge','duplicate-geometry-edge','wrong-geometry-order','wrong-geometry-loop','wrong-geometry-owner','wrong-info-count','wrong-info-bbox','wrong-device-totals','input-padding-changed','missing-manifest-file','unexpected-output-file','range-file-alias-cannot-hide-wrong-output','range-case-dropped','range-role-redefined','data-role-redefined','data-error-falsely-successful','data-paired-hashes-forged','data-extra-output-byte','data-missing-case','argument-API-redefined','argument-query-result-forged','argument-descriptor-forged','state-role-redefined','concurrent-streams-not-independent','changed-input-identity-removed','changed-input-unused-tail-scrubbed','actual-C++-relocated-evidence-passes','C++-process-nonzero','C++-input-changed','C++-output-changed','C++-geometry-changed','C++-range-metadata-changed','C++-stdout-point-missing','C++-stdout-bbox-wrong','C++-stdout-truncated','default-input-redirected','default-input-redirected-and-corrupt','CLI-actual-argv-cannot-change-case','CLI-input-path-cannot-redirect','CLI-malformed-input-bytes-required','CLI-log-paths-bound','cold-real-complete-matrix-passes','cold-duplicate-workflow-rejected','cold-duplicate-child-path-rejected','cold-duplicate-child-index-rejected','native-complete-outputs-and-receipts-pass','native-empty-output-inventory-rejected','native-input-identity-rejected']

def run_checks():
 run=json.loads((ROOT/'migration/reports/image-contour-all.json').read_text());out=ROOT/run['outputs'];all_rows=json.loads((out/'runs.json').read_text());profile=json.loads((ROOT/'migration/rewrite/image-contour-profile.json').read_text());small_ids={c['case'] for c in profile['cases'] if c['width']*c['height']<=5000};small=[r for r in all_rows if r['case'] in small_ids];checks=[]
 def check(name,fn,wanted=True):
  try:actual=bool(fn())
  except (ValueError,TypeError,KeyError,IndexError,OSError,StopIteration):actual=False
  checks.append(dict(check=name,passed=actual==wanted))
 with tempfile.TemporaryDirectory(prefix='contour-checks-') as temp:
  base=Path(temp)
  def subset(name,mutate=None,target=None,file_change=None,small_mode=True,expected_small=True,rc=0,rows_override=None,unknown=False):
   d=base/name;d.mkdir();rows=copy.deepcopy(small if rows_override is None else rows_override)
   if mutate:mutate(rows)
   for r in small:
    p=d/r['case']
    if r['case']==target:shutil.copytree(out/r['case'],p)
    else:p.symlink_to(out/r['case'],target_is_directory=True)
   if file_change:
    filename,fn=file_change;p=d/target/filename;fn(p);r=next(r for r in rows if r['case']==target);r['files'][filename]=dict(bytes=p.stat().st_size,sha256=digest(p))
   if unknown:(d/target/'unknown.file').write_bytes(b'bad')
   (d/'runs.json').write_text(json.dumps(rows));return all(r['status']=='PASSED' for r in masks.validate(dict(run,outputs=str(d),small=small_mode,return_code=rc),expected_small=expected_small))
  check(NAMES[0],lambda:subset('positive'))
  check(NAMES[1],lambda:subset('downgrade',expected_small=False),False)
  check(NAMES[2],lambda:subset('missing-big',small_mode=False,expected_small=False,rows_override=all_rows[:-1]),False)
  check(NAMES[3],lambda:subset('duplicate',lambda rs:rs.append(copy.deepcopy(rs[0]))),False)
  check(NAMES[4],lambda:subset('process',rc=1),False)
  check(NAMES[5],lambda:subset('case-error',lambda rs:rs[0].update(return_code=1)),False)
  def flip(p,index):b=bytearray(p.read_bytes());b[index]^=1;p.write_bytes(b)
  target='one-pixel'
  mutations=[('wrong-raw-pixel','raw.bin',0),('wrong-label-pixel','labels.bin',0),('wrong-mask-pixel','mask.bin',0),('wrong-mask-padding','mask.bin',1)]
  for name,f,i in mutations:check(name,lambda name=name,f=f,i=i:subset(name,target=target,file_change=(f,lambda p:flip(p,i))),False)
  check('missing-geometry-edge',lambda:subset('drop-edge',target=target,file_change=('geometry.bin',lambda p:p.write_bytes(p.read_bytes()[:-36]))),False)
  def geometry_change(p,kind):
   a=np.fromfile(p,'<u4').reshape(-1,9)
   if kind=='duplicate':a[1]=a[0]
   elif kind=='order':a[0,2]+=1
   elif kind=='loop':a[0,1]+=1
   else:a[0,7]+=1
   a.tofile(p)
  for name,kind in [('duplicate-geometry-edge','duplicate'),('wrong-geometry-order','order'),('wrong-geometry-loop','loop'),('wrong-geometry-owner','owner')]:check(name,lambda name=name,kind=kind:subset(name,target=target,file_change=('geometry.bin',lambda p:geometry_change(p,kind))),False)
  for name,offset in [('wrong-info-count',0),('wrong-info-bbox',3*4)]:check(name,lambda name=name,offset=offset:subset(name,target=target,file_change=('info.bin',lambda p:flip(p,offset))),False)
  check('wrong-device-totals',lambda:subset('totals',target=target,file_change=('totals.bin',lambda p:flip(p,4))),False)
  check('input-padding-changed',lambda:subset('input-pad',target=target,file_change=('input-after.bin',lambda p:flip(p,1))),False)
  check('missing-manifest-file',lambda:subset('manifest',lambda rs:rs[0]['files'].pop('geometry.bin')),False)
  check('unexpected-output-file',lambda:subset('unexpected',target=target,unknown=True),False)
  def alias(rs):next(r for r in rs if r['case']=='constant-0')['ranges'][0]['file']='reconstruction-default.bin'
  check('range-file-alias-cannot-hide-wrong-output',lambda:subset('alias',alias,target='constant-0',file_change=('reconstruction-all.bin',lambda p:flip(p,0))),False)
  check('range-case-dropped',lambda:subset('range-drop',lambda rs:rs[0]['ranges'].pop()),False)
  check('range-role-redefined',lambda:subset('range-role',lambda rs:rs[0]['ranges'][0].update(start=1)),False)
  def generic(report,reader,name,mutate,file_change=None):
   real=ROOT/report['outputs'];d=base/name;d.mkdir();rows=json.loads((real/'runs.json').read_text());mutate(rows)
   for p in real.iterdir():
    if p.name=='runs.json':continue
    if file_change and p.name==file_change[0]:shutil.copyfile(p,d/p.name);file_change[1](d/p.name)
    else:(d/p.name).symlink_to(p,target_is_directory=p.is_dir())
   (d/'runs.json').write_text(json.dumps(rows));return reader(dict(report,outputs=str(d)))['status']=='PASSED'
  data=json.loads((ROOT/'migration/reports/image-contour-data-errors.json').read_text())
  check('data-role-redefined',lambda:generic(data,data_reader.validate,'data-role',lambda rs:rs[0].update(kind='pixels')),False)
  check('data-error-falsely-successful',lambda:generic(data,data_reader.validate,'data-rc',lambda rs:rs[0].update(return_code=0)),False)
  def forged(rs):rs[0]['before']['geometry']='0'*64;rs[0]['after']['geometry']='0'*64
  check('data-paired-hashes-forged',lambda:generic(data,data_reader.validate,'data-hash',forged),False)
  check('data-extra-output-byte',lambda:generic(data,data_reader.validate,'data-length',lambda rs:None,('zero-edge-count.bin',lambda p:p.write_bytes(p.read_bytes()+b'x'))),False)
  check('data-missing-case',lambda:generic(data,data_reader.validate,'data-drop',lambda rs:rs.pop()),False)
  args=json.loads((ROOT/'migration/reports/image-contour-arguments.json').read_text())
  check('argument-API-redefined',lambda:generic(args,arg_reader.validate,'arg-api',lambda rs:rs[0].update(api='positive')),False)
  check('argument-query-result-forged',lambda:generic(args,arg_reader.validate,'arg-query',lambda rs:next(r for r in rs if r['case']=='render-query-two').update(query_bytes=0)),False)
  check('argument-descriptor-forged',lambda:generic(args,arg_reader.validate,'arg-d',lambda rs:next(r for r in rs if r['case']=='zero-width')['actual_arguments'].update(width=1)),False)
  states=json.loads((ROOT/'migration/reports/image-contour-states.json').read_text())
  check('state-role-redefined',lambda:generic(states,states_reader.validate,'state-role',lambda rs:rs[0].update(kind='error-run')),False)
  def same_stream(rs):next(r for r in rs if r['case']=='concurrent-B')['stream_id']=next(r for r in rs if r['case']=='concurrent-A')['stream_id']
  check('concurrent-streams-not-independent',lambda:generic(states,states_reader.validate,'state-stream',same_stream),False)
  check('changed-input-identity-removed',lambda:generic(states,states_reader.validate,'state-input',lambda rs:next(r for r in rs if r['case']=='changed-core').update(all_input_bytes_zero=False)),False)
  def state_tail():
   real=ROOT/states['outputs'];d=base/'state-tail';d.mkdir()
   for p in real.iterdir():
    if p.name=='changed-core':shutil.copytree(p,d/p.name)
    else:(d/p.name).symlink_to(p,target_is_directory=p.is_dir())
   path=d/'changed-core/geometry.bin';b=bytearray(path.read_bytes());b[96*36]^=1;path.write_bytes(b);return states_reader.validate(dict(states,outputs=str(d)))['status']=='PASSED'
  check('changed-input-unused-tail-scrubbed',state_tail,False)
  runs=json.loads((ROOT/'migration/reports/image-contour-originals.json').read_text());rules=json.loads((ROOT/'migration/rewrite/image-contour-original-contract.json').read_text())['cases'];sample=next(r for r in runs if (r['family'],r['case'],r['mode'])==('NPP+','annulus','default'));rule=next(r for r in rules if (r['family'],r['case'],r['mode'])==('NPP+','annulus','default'));meta=json.loads((ROOT/sample['evidence']/'manifest.json').read_text());real=ROOT/meta['raw_artifact_dir']
  def cpp(name,change=None,edit=None):
   d=base/name;shutil.copytree(real,d);row=copy.deepcopy(sample)
   for key in ['input','outputs','audit']:row[key]=str(d/(ROOT/row[key]).relative_to(real))
   if change:change(row)
   if edit:edit(d,row)
   return originals.validate_one(row,rule,raw_override=d)['status']=='PASSED'
  check('actual-C++-relocated-evidence-passes',lambda:cpp('cpp-positive'))
  check('C++-process-nonzero',lambda:cpp('cpp-rc',lambda r:r.update(return_code=1)),False)
  check('C++-input-changed',lambda:cpp('cpp-input',edit=lambda d,r:flip(Path(r['input']),0)),False)
  check('C++-output-changed',lambda:cpp('cpp-output',edit=lambda d,r:flip(next(Path(r['outputs']).glob('*Contours_*.raw')),0)),False)
  check('C++-geometry-changed',lambda:cpp('cpp-geometry',edit=lambda d,r:flip(Path(r['audit'])/'geometry.bin',0)),False)
  def bad_range(d,r):p=Path(r['audit'])/'workflow.json';v=json.loads(p.read_text());v['start']=0;p.write_text(json.dumps(v))
  check('C++-range-metadata-changed',lambda:cpp('cpp-range',edit=bad_range),False)
  def stdout_edit(d,r,kind):
   p=d/r['stdout'];lines=p.read_text().splitlines()
   if kind=='point':lines.pop(next(i for i,x in enumerate(lines) if x.startswith('ID ')))
   elif kind=='bbox':i=next(i for i,x in enumerate(lines) if x.startswith('nID '));t=lines[i].split();t[-1]=str(int(t[-1])+1);lines[i]=' '.join(t)
   else:lines=[lines[-1]]
   p.write_text('\n'.join(lines)+'\n')
  for name,kind in [('C++-stdout-point-missing','point'),('C++-stdout-bbox-wrong','bbox'),('C++-stdout-truncated','truncated')]:check(name,lambda name=name,kind=kind:cpp(name,edit=lambda d,r:stdout_edit(d,r,kind)),False)
  original=next(r for r in runs if (r['family'],r['case'])==('NPP','original'));rule0=next(r for r in rules if (r['family'],r['case'])==('NPP','original'));redirect=copy.deepcopy(original);redirect['input']='NPP/findContour/images/CircuitBoard_2048x1024_8u.raw';check('default-input-redirected',lambda:originals.validate_one(redirect,rule0)['status']=='PASSED',False)
  target_default=(ROOT/original['outputs']/'CircuitBoard_2048x1024_8u.raw').resolve();actual_bytes_file=originals.bytes_file
  def corrupted(path,n,sha=None):return bytes(n) if Path(path).resolve()==target_default else actual_bytes_file(path,n,sha)
  with patch.object(originals,'bytes_file',corrupted):check('default-input-redirected-and-corrupt',lambda:originals.validate_one(redirect,rule0)['status']=='PASSED',False)
 cli_rows=json.loads((ROOT/'migration/reports/image-contour-cli.json').read_text());zero=next(r for r in cli_rows if (r['family'],r['case'])==('NPP','zero-width'));zmeta=json.loads((ROOT/zero['evidence']/'manifest.json').read_text());zraw=ROOT/zmeta['raw_artifact_dir'];target_commands=(zraw/'commands.json').read_text();base_loads=json.loads
 def changed_command(blob,*args,**kwargs):
  value=base_loads(blob,*args,**kwargs)
  if blob==target_commands:value[0]['argv'][-2:]=['--height','-1']
  return value
 with patch.object(cli_reader.json,'loads',changed_command):check('CLI-actual-argv-cannot-change-case',lambda:cli_reader.validate(cli_rows)['status']=='PASSED',False)
 redirected=copy.deepcopy(cli_rows);next(r for r in redirected if r['case']=='trailing-input')['input']='build/absent-contour-CLI-input.raw';check('CLI-input-path-cannot-redirect',lambda:cli_reader.validate(redirected)['status']=='PASSED',False)
 trailing=next(r for r in cli_rows if r['case']=='trailing-input');path=(ROOT/trailing['input']).resolve();read_bytes=Path.read_bytes
 def wrong_bytes(p):return b'bad' if p.resolve()==path else read_bytes(p)
 with patch.object(Path,'read_bytes',wrong_bytes):check('CLI-malformed-input-bytes-required',lambda:cli_reader.validate(cli_rows)['status']=='PASSED',False)
 bad_logs=copy.deepcopy(cli_rows);bad_logs[0]['stdout']=bad_logs[0]['stderr'];check('CLI-log-paths-bound',lambda:cli_reader.validate(bad_logs)['status']=='PASSED',False)
 children=json.loads((ROOT/'migration/reports/image-contour-cold.json').read_text())['children'];check('cold-real-complete-matrix-passes',lambda:cold_inventory(children))
 duplicate=copy.deepcopy(children);originals_children=[c for c in duplicate if c['name']=='originals'];originals_children[-1]['report']=copy.deepcopy(originals_children[0]['report']);check('cold-duplicate-workflow-rejected',lambda:cold_inventory(duplicate),False)
 duplicate=copy.deepcopy(children);duplicate[-1]['relative']=duplicate[0]['relative'];check('cold-duplicate-child-path-rejected',lambda:cold_inventory(duplicate),False)
 duplicate=copy.deepcopy(children);originals_children=[c for c in duplicate if c['name']=='originals'];originals_children[-1]['index']=originals_children[0]['index'];check('cold-duplicate-child-index-rejected',lambda:cold_inventory(duplicate),False)
 natives=json.loads((ROOT/'migration/reports/image-I2-contour-native-originals.json').read_text());spec=json.loads((ROOT/'migration/rewrite/image-contour-profile.json').read_text())
 def native_ok(row):
  commands=json.loads((ROOT/row['evidence']/'commands.json').read_text());return native_result(row,spec,commands)['expected_components']==262
 check('native-complete-outputs-and-receipts-pass',lambda:all(native_ok(r) for r in natives))
 broken=copy.deepcopy(natives[0]);broken['files']={};check('native-empty-output-inventory-rejected',lambda:native_ok(broken),False)
 broken=copy.deepcopy(natives[0]);broken['input_sha256']='0'*64;check('native-input-identity-rejected',lambda:native_ok(broken),False)
 if len(checks)!=len(NAMES) or {c['check'] for c in checks}!=set(NAMES):raise ValueError('all fixed validator mutation obligations')
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',case_count=len(checks),checks=checks)

def main():
 fixed=ROOT/'migration/rewrite/image-contour-validator-cases.json'
 if json.loads(fixed.read_text())!=NAMES:raise ValueError('fixed negative-case inventory')
 sources=[__file__,fixed,*[ROOT/'tools/moat'/n for n in ['image_contour_reference.py','image_contour_original_reference.py','image_contour_model.py','image_ccl_reference.py','image_contour_data_reference.py','image_contour_arguments_reference.py','image_contour_states_reference.py','image_contour_state_reference.py','image_contour_cli.py','qualify_image_contour.py']],*[ROOT/'migration/rewrite'/n for n in ['image-contour-profile.json','image-contour-original-contract.json','image-contour-data-error-contract.json','image-contour-argument-contract.json','image-contour-state-contract.json']]];e=Experiment('I2','Contour-actual-validator-mutations','CPU-validator-test',sources=sources)
 try:v=run_checks()
 except Exception as error:v=dict(status='FAILED',checks=[dict(check='all-mutants-execute',passed=False,error=repr(error))])
 write(e.path/'checks.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'SELF_TEST_FAILED',dict(status=v['status'],checks=v['checks']));write(ROOT/'migration/reports/image-contour-checks.json',v);record('I2','Contour验收器固定'+str(len(NAMES))+'项真实输出/metadata/模式/默认路径/geometry/状态/原例stdout正反向检查：'+v['status'],[v['evidence']]);print(v['status'],v.get('case_count'),[c for c in v['checks'] if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
