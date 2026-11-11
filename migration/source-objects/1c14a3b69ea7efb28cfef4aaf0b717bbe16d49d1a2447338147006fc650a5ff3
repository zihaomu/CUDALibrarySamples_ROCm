#!/usr/bin/env python3
"""Trace every full distance input and independently check real device dispatches."""
import argparse,collections,csv,json,sys
from experiment import ROOT,Experiment,write,digest
from image_distance_build import dependencies
from image_progress import record

def execute():
 from snapshot import capture
 b=json.loads((ROOT/'migration/reports/image-distance-build.json').read_text());assert b['status']=='BUILT' and digest(ROOT/b['library'])==b['library_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());e=Experiment('I2','Distance-full-thirty-real-device-kernels','rocm-trace',sources=[__file__,ROOT/'tools/moat/image_distance_worker.py',ROOT/'tools/moat/image_distance_inputs.py',*dependencies()],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';rc=e.command(['rocprofv3','--kernel-trace','--output-format','csv','--output-directory',str(e.path/'trace'),'--',sys.executable,str(ROOT/'tools/moat/image_distance_worker.py'),'--library',str(ROOT/b['library']),'--sha',b['library_sha256'],'--output',str(out)],'actual-all-thirty-unsigned-and-compact-signed-site-kernels',timeout=900);r=dict(return_code=rc,build=b,experiment_id=e.id,outputs=str(out.relative_to(ROOT)));write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'PROFILER_FAILED');write(ROOT/'migration/reports/image-distance-trace.json',r);record('I2','EDT完整30组原始/独立输入实际GPU trace执行rc='+str(rc)+'；独立CPU与原始dispatch/PCI/时间/grid随后核对。',[r['evidence']]);print(rc,r['evidence']);return rc

def validate(run):
 from image_distance_reference import validate as pixels
 results=pixels(run);meta=json.loads((ROOT/run['evidence']/'manifest.json').read_text());raw=ROOT/meta['raw_artifact_dir'];traces=list((raw/'trace').rglob('*kernel_trace.csv'));agents=list((raw/'trace').rglob('*agent_info.csv'))
 if len(traces)!=1 or len(agents)!=1:raise ValueError('one actual kernel trace and agent inventory')
 rows=list(csv.DictReader(traces[0].open()));names=['prepare','unsigned_rows','unsigned_columns','compact_sites','nearest_sites'];expected=dict(prepare=30,unsigned_rows=9,unsigned_columns=9,compact_sites=21,nearest_sites=21);counts=collections.Counter();project=[];lookup={r['Node_Id']:r for r in csv.DictReader(agents[0].open())};allowed={d['pci_bdf'] for d in json.loads((raw/'backend.observed.json').read_text())['devices'] if d['physical_id']!=3}
 for r in rows:
  matches=[n for n in names if 'image_distance::'+n+'(' in r['Kernel_Name']]
  if not matches:continue
  project.append(r)
  for name in matches:counts[name]+=1
  agent=lookup[r['Agent_Id'].split()[-1]];loc=int(agent['Location_Id']);bdf=f"{int(agent['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}"
  if bdf not in allowed or int(r['End_Timestamp'])<=int(r['Start_Timestamp']) or int(r['Grid_Size_X'])<=0:raise ValueError('actual allowed PCI device/time/nonempty grid')
 checks=[dict(check='real-dispatch/'+name,passed=counts[name]==count,actual=counts[name],expected=count) for name,count in expected.items()];outputs=json.loads((ROOT/run['outputs']/'runs.json').read_text());checks.append(dict(check='changed-full-inputs-and-actual-device-outputs',passed=bool(project) and len({r['files']['distance.bin']['sha256'] for r in outputs})>10));results.append(dict(case='actual-all-input-GPU-kernel-dispatches',status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks));return dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=31,results=results)

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 if not a.check:return execute()
 r=json.loads((ROOT/'migration/reports/image-distance-trace.json').read_text());e=Experiment('I2','Distance-full-trace-independent-CPU','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_distance_reference.py',ROOT/'tools/moat/image_distance_inputs.py',ROOT/'tools/moat/image_distance_model.py',ROOT/'migration/rewrite/image-distance-profile.json'],parent=r['experiment_id'])
 try:v=validate(r)
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='all-thirty-pixels-and-actual-kernel-device-dispatches',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-distance-trace-validation.json',v);record('I2','EDT30组全结果及30prepare/9unsigned×2/21signed×2真实GPU kernel独立CPU验收：'+v['status'],[v['evidence']]);print(v['status'],v.get('error'),[r for r in v['results'] if r['status']=='FAILED']);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
