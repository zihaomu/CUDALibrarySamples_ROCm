#!/usr/bin/env python3
"""Exercise real C++ command-line and input/output failure branches."""
import argparse,json,os
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_contour_build import dependencies
from image_progress import record

def execute():
 from snapshot import capture
 spec=json.loads((ROOT/'migration/rewrite/image-contour-profile.json').read_text());contract=json.loads((ROOT/'migration/rewrite/image-contour-cli-contract.json').read_text());b=json.loads((ROOT/'migration/reports/image-contour-frontends-build.json').read_text());assert b['status']=='BUILT' and all(digest(ROOT/n)==v for n,v in b['dependencies'].items());case=next(c for c in spec['cases'] if c['case']=='independent-noise-875231');data=np.fromfile(ROOT/case['fixture']/'input.bin',np.uint8).reshape(case['height'],case['pitch'])[:,:case['width']].copy();rows=[]
 for rule in contract['cases']:
  family,name=rule['family'],rule['case'];binary=next(r for r in b['binaries'] if r['family']==family);assert digest(ROOT/binary['binary'])==binary['binary_sha256'];e=Experiment('I2',family+'/findContour-CLI','rocm-CLI',case=name,sources=[__file__,ROOT/'migration/rewrite/image-contour-cli-contract.json',*[ROOT/n for n in b['dependencies']]],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';out.mkdir();inp=e.path/'input.raw';data.tofile(inp);command=[str(ROOT/binary['binary']),'--input',str(inp),'--output-dir',str(out),'--width',str(case['width']),'--height',str(case['height']),*rule['args']];env={}
  if name=='help':command=[str(ROOT/binary['binary']),'--help']
  elif name=='missing-input':inp.unlink()
  elif name=='truncated-input':inp.write_bytes(inp.read_bytes()[:-1])
  elif name=='trailing-input':inp.write_bytes(inp.read_bytes()+b'\x00')
  elif name=='unwritable-output':out.rmdir();out.write_text('file blocks output directory')
  elif name=='no-GPU':env['HIP_VISIBLE_DEVICES']=''
  rc=e.command(command,'actual-C++-CLI-'+name,env=env,timeout=180);r=dict(family=family,case=name,return_code=rc,output=str(out.relative_to(ROOT)),input=str(inp.relative_to(ROOT)),binary=binary,build=b,experiment_id=e.id,stdout=e.commands[-1]['stdout'],stderr=e.commands[-1]['stderr']);write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if rc==rule['return_code'] else 'CLI_GAP');rows.append(r);write(ROOT/'migration/reports/image-contour-cli.json',rows);record('I2',family+' contour CLI/'+name+'实际返回'+str(rc)+'；固定诊断和输出集合由独立CPU验收。',[r['evidence']]);print(family,name,rc,flush=True)
 return 0

def validate(rows):
 rules=json.loads((ROOT/'migration/rewrite/image-contour-cli-contract.json').read_text())['cases'];expected={(r['family'],r['case']):r for r in rules}
 if len(rows)!=32 or {(r['family'],r['case']) for r in rows}!=set(expected):raise ValueError('all unique fixed CLI obligations')
 results=[]
 for r in rows:
  rule=expected[(r['family'],r['case'])];meta=json.loads((ROOT/r['evidence']/'manifest.json').read_text());raw=ROOT/meta['raw_artifact_dir'];cs=json.loads((raw/'commands.json').read_text());stdout=(raw/r['stdout']).read_text();stderr=(raw/r['stderr']).read_text();output=ROOT/r['output'];checks=[dict(check='actual-return-code',passed=r['return_code']==rule['return_code']==cs[0]['return_code']),dict(check='actual-current-binary',passed=len(cs)==1 and cs[0]['argv'][0]==str(ROOT/r['binary']['binary']))]
  if r['case']=='help':checks.extend([dict(check='actual-help',passed='Usage:' in stdout and '--input RAW' in stdout and '--width W --height H' in stdout and (('--start-id ID' in stdout)==(r['family']=='NPP+'))),dict(check='no-error-diagnostic',passed=not stderr.strip())])
  else:checks.append(dict(check='actual-specific-error-diagnostic',passed='Contour error:' in stderr and rule['diagnostic'] in stderr))
  if r['case']=='unwritable-output':checks.append(dict(check='actual-output-directory-conflict',passed=output.is_file() and output.read_text()=='file blocks output directory'))
  else:checks.append(dict(check='no-output-files-from-help-or-failed-workflow',passed=output.is_dir() and not list(output.iterdir())))
  if r['case']=='no-GPU':checks.append(dict(check='actual-empty-device-mask',passed=cs[0]['environment_changes']['HIP_VISIBLE_DEVICES']==''))
  results.append(dict(case=r['family']+'/'+r['case'],status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks))
 return dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=len(results),results=results)

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 if not a.check:return execute()
 e=Experiment('I2','Contour-CLI-independent-CPU','CPU-reference',sources=[__file__,ROOT/'migration/rewrite/image-contour-cli-contract.json',ROOT/'migration/rewrite/image-contour-profile.json'])
 try:v=validate(json.loads((ROOT/'migration/reports/image-contour-cli.json').read_text()))
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='complete-actual-CLI-contract',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-contour-cli-validation.json',v);record('I2','Contour32项CLI实际返回码/具体诊断/空输出/无设备mask独立验收：'+v['status'],[v['evidence']]);print(v['status'],v.get('error'),[r for r in v['results'] if r['status']=='FAILED']);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
