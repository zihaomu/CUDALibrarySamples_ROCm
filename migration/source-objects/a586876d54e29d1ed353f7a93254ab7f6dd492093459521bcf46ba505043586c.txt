#!/usr/bin/env python3
"""Trace all full RGB inputs and check actual project dispatches and physical GPU."""
import argparse,collections,csv,json,sys
from experiment import ROOT,Experiment,write,digest
from image_flood_build import dependencies
from image_progress import record
def execute():
 from snapshot import capture
 b=json.loads((ROOT/'migration/reports/image-flood-build.json').read_text());assert b['status']=='BUILT' and digest(ROOT/b['library'])==b['library_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());e=Experiment('I3','FloodFill-all29-real-device-dispatch-trace','rocm-trace',sources=[__file__,ROOT/'tools/moat/image_flood_worker.py',ROOT/'tools/moat/image_flood_inputs.py',*dependencies()],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';rc=e.command(['rocprofv3','--kernel-trace','--output-format','csv','--output-directory',str(e.path/'trace'),'--',sys.executable,str(ROOT/'tools/moat/image_flood_worker.py'),'--library',str(ROOT/b['library']),'--sha',b['library_sha256'],'--output',str(out)],'actual-all29-RGB-predicate-union-output-and-metadata-kernels',timeout=900);r=dict(return_code=rc,build=b,experiment_id=e.id,outputs=str(out.relative_to(ROOT)));write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'PROFILER_FAILED');write(ROOT/'migration/reports/image-flood-trace.json',r);record('I3','flood29完整RGB输入真实GPU trace执行rc='+str(rc)+'；全像素与实际kernel/PCI/grid/时间另验。',[r['evidence']]);print(rc,r['evidence']);return rc
def validate(run):
 from image_flood_reference import validate as pixels
 results=pixels(run);meta=json.loads((ROOT/run['evidence']/'manifest.json').read_text());raw=ROOT/meta['raw_artifact_dir'];traces=list((raw/'trace').rglob('*kernel_trace.csv'));agents=list((raw/'trace').rglob('*agent_info.csv'))
 if len(traces)!=1 or len(agents)!=1:raise ValueError('one actual kernel trace and agent inventory')
 counter=collections.Counter();lookup={r['Node_Id']:r for r in csv.DictReader(agents[0].open())};allowed={d['pci_bdf'] for d in json.loads((raw/'backend.observed.json').read_text())['devices'] if d['physical_id']==1};project=[]
 for row in csv.DictReader(traces[0].open()):
  name=row['Kernel_Name'];matches=[k for k in ['prepare','output','finish'] if 'image_flood::'+k+'(' in name]+[k for k in ['hook','compress'] if 'rocm_image::' in name and '::'+k+'(' in name]
  if not matches:continue
  project.append(row)
  for k in matches:counter[k]+=1
  agent=lookup[row['Agent_Id'].split()[-1]];loc=int(agent['Location_Id']);pci=f"{int(agent['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}"
  if pci not in allowed or int(row['End_Timestamp'])<=int(row['Start_Timestamp']) or int(row['Grid_Size_X'])<=0:raise ValueError('nonempty real kernel on allowed physical1 with positive duration')
 checks=[dict(check='actual-dispatch/'+k,passed=counter[k]==29,actual=counter[k]) for k in ['prepare','output','finish']]+[dict(check='actual-dispatch/'+k,passed=counter[k]>=29,actual=counter[k]) for k in ['hook','compress']];rows=json.loads((ROOT/run['outputs']/'runs.json').read_text());checks.append(dict(check='full-changing-inputs-and-actual-output-inventory',passed=bool(project) and len({r['files']['output.bin']['sha256'] for r in rows})>15));results.append(dict(case='all29-actual-device-dispatches',status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks));return dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=30,results=results)
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 if not a.check:return execute()
 run=json.loads((ROOT/'migration/reports/image-flood-trace.json').read_text());e=Experiment('I3','FloodFill-real-dispatch-and-full-pixels-independent-CPU','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_flood_reference.py',ROOT/'tools/moat/image_flood_inputs.py',ROOT/'migration/rewrite/image-flood-profile.json'],parent=run['experiment_id'])
 try:v=validate(run)
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='all29-full-RGB-and-real-physical1-kernel-dispatches',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-flood-trace-validation.json',v);record('I3','flood29完整RGB/metadata/padding与prepare/output/finish/union真实GPU分发独立CPU：'+v['status'],[v['evidence']]);print(v['status'],v.get('error'),[r for r in v['results'] if r['status']=='FAILED']);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
