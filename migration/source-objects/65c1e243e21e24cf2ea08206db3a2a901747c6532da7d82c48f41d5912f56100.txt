#!/usr/bin/env python3
import csv,json,shutil
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
b=json.loads((ROOT/'migration/reports/rewrite-sparse-binding-build.json').read_text());records=[];observed=capture()
for kind in ['batch','uniform_batch','reordering_phase','residual']:
 binary=next(row for row in b['binaries'] if row['sample_id']==f'cuDSS/fortran/{kind}::{kind}.f90');src=ROOT/'tests/fixtures/rewrite-bindings'/kind/'original';mh=digest(src/'manifest.json');e=Experiment('R5',binary['sample_id']+'/backend-trace','rocm-profile',case='original',sources=[__file__,ROOT/'rocm/adapters/fortran/sparse_bridge.cpp',ROOT/'rocm/common/batch11_sparse.hpp'],parent=b['experiment_id'],comparison_id='sparse-binding/'+kind+'/original/'+mh);shutil.copytree(src,e.path/'inputs');write(e.path/'backend.observed.json',observed);out=e.path/'outputs';out.mkdir();trace=e.path/'trace';trace.mkdir();rc=e.command(['rocprofv3','--kernel-trace','--output-format','csv','json','--output-directory',str(trace),'--output-file','sparse','--',str(ROOT/binary['binary'])],'actual-Fortran-GPU-trace',env=dict(REWRITE_INPUT=str(e.path/'inputs'),REWRITE_OUTPUT=str(out)));rows=[]
 for path in trace.rglob('*kernel_trace.csv'):
  with path.open() as f:rows+=list(csv.DictReader(f))
 names=[r.get('Kernel_Name') or r.get('Name') or str(r) for r in rows];summary=dict(profile=kind,binary=binary,shared_library_sha256=b['shared_library_sha256'],build_experiment_id=b['experiment_id'],input_manifest_sha256=mh,return_code=rc,kernel_names=names,factor_dispatches=sum('lu11(' in n for n in names),solve_dispatches=sum('solve11(' in n for n in names));write(e.path/'kernel-summary.json',summary);summary['evidence']=e.finish('PROFILE_OBSERVED' if rc==0 else 'PROFILER_FAILED');records.append(summary);write(ROOT/'migration/reports/rewrite-sparse-binding-traces.json',dict(profiles=records));print(kind,summary['factor_dispatches'],summary['solve_dispatches'],flush=True)
