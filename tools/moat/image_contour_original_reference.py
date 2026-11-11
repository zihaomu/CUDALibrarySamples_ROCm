#!/usr/bin/env python3
"""Verify actual C++ original files, ordered diagnostic fields and GPU audit data."""
import argparse,json
import numpy as np
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_contour_model import model,reconstruct
from image_contour_reference import check_array,bytes_file,geometry_invariants
from image_progress import record

def command_binding(r,rule,raw,meta,w,h,audit,out):
 commands=json.loads((raw/'commands.json').read_text())
 if len(commands)!=1:return dict(check='actual-C++-command-input-output-and-audit-binding',passed=False)
 command=commands[0];stored_raw=Path(command['cwd']).parent;origin=stored_raw
 for part in Path(meta['raw_artifact_dir']).parts:origin=origin.parent
 if origin/Path(meta['raw_artifact_dir'])!=stored_raw:return dict(check='actual-C++-command-input-output-and-audit-binding',passed=False)
 original_input=stored_raw/'work/images/CircuitBoard_2048x1024_8u.raw' if rule['default_paths'] else stored_raw/'inputs/input.raw';original_output=stored_raw/'work/images' if rule['default_paths'] else stored_raw/'outputs';expected=[str(origin/r['binary']['binary'])]
 if not rule['default_paths']:expected+=['--input',str(original_input),'--output-dir',str(original_output),'--width',str(w),'--height',str(h)]
 modes={'single-ID-override':['--start-id','1','--stop-id','2'],'all-markers':['--start-id','0','--stop-id','3'],'empty':['--start-id','2','--stop-id','2']};expected+=modes.get(rule['mode'],[])
 relocated_input=raw/original_input.relative_to(stored_raw);relocated_output=raw/original_output.relative_to(stored_raw)
 return dict(check='actual-C++-command-input-output-and-audit-binding',passed=command['return_code']==0 and command['argv']==expected and command['stdout']==r['stdout'] and command['stderr']==r['stderr'] and command['cwd']==str(stored_raw/'work') and (ROOT/r['input']).resolve()==relocated_input.resolve() and out.resolve()==relocated_output.resolve() and command['environment_changes']['MIGRATION_IMAGE_CONTOUR_AUDIT_DIR']==str(stored_raw/'audit') and audit.resolve()==(raw/'audit').resolve())

def validate_one(r,rule,raw_override=None):
 if (r['family'],r['case'],r['mode'],r['fixture_case'])!=(rule['family'],rule['case'],rule['mode'],rule['source_case']) or r['return_code']!=0:raise ValueError('fixed actual original case/status')
 profile=json.loads((ROOT/'migration/rewrite/image-contour-profile.json').read_text());case=next(c for c in profile['cases'] if c['case']==rule['source_case']);w,h=case['width'],case['height'];source=np.fromfile(ROOT/case['fixture']/'input.bin',np.uint8).reshape(h,case['pitch'])[:,:w].copy();expected=model(source);k,m,loops=map(int,expected['totals']);start=rule['start'];stop=k if rule['stop']=='component_count' else rule['stop'];limit=rule['limit'];out=ROOT/r['outputs'];audit=ROOT/r['audit'];meta=json.loads((ROOT/r['evidence']/'manifest.json').read_text());raw=Path(raw_override) if raw_override is not None else ROOT/meta['raw_artifact_dir'];checks=[dict(check='exact-original-input-bytes-and-receipt',passed=bytes_file(ROOT/r['input'],w*h,r['input_sha256'])==source.tobytes()),dict(check='actual-original-process-zero',passed=r['return_code']==0)];checks.append(command_binding(r,rule,raw,meta,w,h,audit,out));shape=f'{w}x{h}';files={}
 for name,value,kind in [('LabelMarkersUF',expected['raw'],'32u'),('CompressedMarkerLabelsUF',expected['labels'],'32u'),('Contours',expected['mask'],'8u')]:files[f'CircuitBoard_{name}_8Way_{shape}_{kind}.raw']=value
 if rule['plus']:files[f'CircuitBoard_ContoursReconstructed_8Way_{shape}_8u.raw']=reconstruct(expected['geometry'],expected['labels'],expected['info'],start,stop,limit)
 allowed=set(files)
 if rule['default_paths']:
  allowed.add('CircuitBoard_2048x1024_8u.raw');actual_default=out/'CircuitBoard_2048x1024_8u.raw';checks.append(dict(check='actual-default-input-path-and-frozen-bytes',passed=(ROOT/r['input']).resolve()==actual_default.resolve() and bytes_file(actual_default,w*h,case['original']['sha256'])==source.tobytes()))
 checks.append(dict(check='exact-three-or-four-original-files',passed={p.name for p in out.iterdir()}==allowed))
 for name,expect in files.items():a=np.frombuffer(bytes_file(out/name,expect.nbytes),expect.dtype).reshape(expect.shape);checks.append(check_array(name+'/complete-original-pixels',a,expect))
 if {p.name for p in audit.iterdir()}!={'input.bin','info.bin','geometry.bin','totals.bin','workflow.json'}:raise ValueError('complete original audit sidecars')
 checks.append(dict(check='actual-dense-input-read-by-C++',passed=bytes_file(audit/'input.bin',w*h)==source.tobytes()))
 for name,expect in [('info',expected['info']),('geometry',expected['geometry']),('totals',expected['totals'])]:
  actual=np.frombuffer(bytes_file(audit/(name+'.bin'),expect.nbytes),'<u4').reshape(expect.shape);checks.append(check_array('C++/'+name+'/all-fields',actual,expect))
  if name=='geometry':checks.append(geometry_invariants(actual,expected['labels']))
 workflow=dict(width=w,height=h,plus=rule['plus'],start=start,stop=stop,limit=limit,components=k,edges=m,loops=loops);checks.append(dict(check='actual-C++-range-and-format-metadata',passed=json.loads((audit/'workflow.json').read_text())==workflow))
 if (raw/r['stderr']).read_text().strip():raise ValueError('unexpected C++ runtime diagnostics')
 selected=np.zeros(k,bool)
 if rule['plus']:
  selected[start:stop]=True
  if stop-start>1:selected&=expected['info'][:,0]<limit
 wanted_indices=np.flatnonzero(selected[expected['geometry'][:,0]]);index=0;headers=[];bypassed=[];complete=[];diag_ok=True
 with (raw/r['stdout']).open() as f:
  for text in f:
   text=text.rstrip('\n')
   if text.startswith('ID '):
    tokens=text.split()
    if len(tokens)!=13 or index>=len(wanted_indices):diag_ok=False;continue
    values=tuple(int(tokens[j]) for j in [1,3,5,6,7,9,10,11,12]);g=expected['geometry'][wanted_indices[index]];wanted=tuple(int(g[j]) for j in [0,1,2,7,8,3,4,5,6]);diag_ok&=values==wanted;index+=1
   elif text.startswith('nID ') and ' geometry diagnostics bypassed at ' in text:bypassed.append(text)
   elif text.startswith('nID '):
    t=text.split();headers.append(tuple(int(t[j]) for j in [1,3,5,7,9,10,11,12]) if len(t)==13 else ())
   elif text.startswith('Contour GPU workflow complete:'):complete.append(text)
   else:diag_ok=False
 wanted_headers=[tuple([c,*map(int,expected['info'][c])]) for c in range(start,stop)] if rule['plus'] else [];wanted_bypass=[f'nID {c} geometry diagnostics bypassed at {limit} contour pixels' for c in range(start,stop) if stop-start>1 and int(expected['info'][c,0])>=limit] if rule['plus'] else []
 checks.extend([dict(check='all-real-ordered-GPU-geometry-diagnostics',passed=diag_ok and index==len(wanted_indices) and headers==wanted_headers and bypassed==wanted_bypass),dict(check='actual-original-completion-counts',passed=complete==[f'Contour GPU workflow complete: components {k}, edges {m}, loops {loops}'])]);return dict(case=r['family']+'/'+r['case']+'/'+r['mode'],status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,file_count=len(files))

def validate(runs):
 rules=json.loads((ROOT/'migration/rewrite/image-contour-original-contract.json').read_text())['cases'];expected={(r['family'],r['case'],r['mode']):r for r in rules}
 if len(runs)!=len(expected) or {(r['family'],r['case'],r['mode']) for r in runs}!=set(expected):raise ValueError('all fifteen independently fixed original workflows')
 results=[]
 for r in runs:
  v=validate_one(r,expected[(r['family'],r['case'],r['mode'])]);results.append(v);print(v['case'],v['status'],flush=True)
 return results

def main():
 e=Experiment('I2','Contour-real-C++-originals-CPU','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_contour_model.py',ROOT/'tools/moat/image_contour_reference.py',ROOT/'tools/moat/image_ccl_reference.py',ROOT/'migration/rewrite/image-contour-profile.json',ROOT/'migration/rewrite/image-contour-original-contract.json']);runs=json.loads((ROOT/'migration/reports/image-contour-originals.json').read_text())
 try:results=validate(runs);v=dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=len(results),file_count=sum(r['file_count'] for r in results),results=results)
 except Exception as error:v=dict(status='FAILED',error=repr(error),results=[])
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='independent-complete-original-C++-files-ranges-and-ordered-diagnostics',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-contour-originals-validation.json',v);record('I2','Contour两个真实C++入口15流程/55原始文件、完整geometry与实际排序诊断/范围/bypass独立CPU验收：'+v['status']+'；尚待运行/CLI/trace/反例/冷检出/复审。',[v['evidence']]);print(v['status'],v.get('error'),[(r['case'],[c for c in r['checks'] if not c['passed']]) for r in v['results'] if r['status']=='FAILED'][:3]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
