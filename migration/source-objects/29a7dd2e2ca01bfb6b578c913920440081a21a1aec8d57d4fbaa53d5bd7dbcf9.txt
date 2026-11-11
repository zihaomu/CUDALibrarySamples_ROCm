#!/usr/bin/env python3
"""Trace real loop construction/order and both renderer validation phases."""
import argparse,collections,csv,json,sys
from experiment import ROOT,Experiment,write,digest
from image_contour_build import dependencies
from image_progress import record

def execute():
 from snapshot import capture
 b=json.loads((ROOT/'migration/reports/image-contour-build.json').read_text());assert b['status']=='BUILT' and b['abi_version']==2 and all(digest(ROOT/n)==v for n,v in b['dependencies'].items());e=Experiment('I2','Contour-real-loop-and-raster-kernels','rocm-trace',sources=[__file__,ROOT/'tools/moat/image_contour_worker.py',*dependencies()],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';rc=e.command(['rocprofv3','--kernel-trace','--output-format','csv','--output-directory',str(e.path/'trace'),'--',sys.executable,str(ROOT/'tools/moat/image_contour_worker.py'),'--library',str(ROOT/b['library']),'--sha',b['library_sha256'],'--output',str(out),'--small'],'real-contour-graph-order-validation-and-rasterization',timeout=300);r=dict(return_code=rc,small=True,outputs=str(out.relative_to(ROOT)),build=b,experiment_id=e.id);write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'PROFILER_FAILED');write(ROOT/'migration/reports/image-contour-trace.json',r);record('I2','Contour真实17输入GPU trace执行rc='+str(rc)+'；loop/排序/完整geometry校验/顶点光栅化及像素输出由独立CPU/原始dispatch核对。',[r['evidence']]);print(rc,r['evidence']);return rc

def validate(run):
 from image_contour_reference import validate as full_validate
 results=full_validate(run,expected_small=True);meta=json.loads((ROOT/run['evidence']/'manifest.json').read_text());raw=ROOT/meta['raw_artifact_dir'];traces=list((raw/'trace').rglob('*kernel_trace.csv'));agents=list((raw/'trace').rglob('*agent_info.csv'))
 if len(traces)!=1 or len(agents)!=1:raise ValueError('one actual trace and device inventory')
 rows=list(csv.DictReader(traces[0].open()));names=['init_edges','link_edges','predecessors','geometry','validate_render','complete_render_info','validate_render_topology','compare_render_info','rasterize_geometry_vertices','output_reconstruction'];counts=collections.Counter();project=[]
 for r in rows:
  if any('::'+n+'(' in r['Kernel_Name'] for n in names):
   project.append(r)
   for n in names:
    if '::'+n+'(' in r['Kernel_Name']:counts[n]+=1
 checks=[dict(check='real-dispatch/'+n,passed=counts[n]==(17 if n in ['init_edges','link_edges','predecessors','geometry'] else 51)) for n in names];lookup={r['Node_Id']:r for r in csv.DictReader(agents[0].open())};allowed={d['pci_bdf'] for d in json.loads((raw/'backend.observed.json').read_text())['devices'] if d['physical_id']!=3}
 for r in project:
  agent=lookup[r['Agent_Id'].split()[-1]];loc=int(agent['Location_Id']);bdf=f"{int(agent['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}"
  if bdf not in allowed or int(r['End_Timestamp'])<=int(r['Start_Timestamp']) or int(r['Grid_Size_X'])<=0:raise ValueError('actual GPU trace device/time/grid')
 mask_hashes=set();edge_counts=set()
 for row in json.loads((ROOT/run['outputs']/'runs.json').read_text()):mask_hashes.add(row['files']['mask.bin']['sha256']);edge_counts.add(row['totals'][1])
 checks.append(dict(check='nonempty-geometry-and-changed-input-dispatches',passed=bool(project) and len(mask_hashes)>2 and len(edge_counts)>2));results.append(dict(case='actual-GPU-loop-validation-raster-trace',status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,dispatches=dict(counts)));return dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=18,results=results)

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 if not a.check:return execute()
 e=Experiment('I2','Contour-trace-full-CPU-and-dispatch-check','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_contour_reference.py',ROOT/'tools/moat/image_contour_model.py',ROOT/'tools/moat/image_ccl_reference.py',ROOT/'migration/rewrite/image-contour-profile.json']);r=json.loads((ROOT/'migration/reports/image-contour-trace.json').read_text())
 try:v=validate(r)
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='actual-GPU-loops-geometry-validation-and-rasterization',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-contour-trace-validation.json',v);record('I2','Contour真实trace17全结果/完整校验kernel与geometry驱动光栅化GPU dispatch独立验收：'+v['status'],[v['evidence']]);print(v['status'],v.get('error'),[r for r in v['results'] if r['status']=='FAILED']);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
