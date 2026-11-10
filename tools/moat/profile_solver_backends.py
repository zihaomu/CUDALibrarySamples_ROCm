#!/usr/bin/env python3
"""Observe numeric GPU kernels separately from project extraction/residual kernels."""
import json,csv
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
observed=capture();cat=json.loads((ROOT/'migration/samples.yaml').read_text());svd=json.loads((ROOT/'migration/reports/rewrite-extension-builds.json').read_text())['svd'];jobs=[('rank-svd',ROOT/svd['binary'],['rocm/backends/solver/rank_svd.hpp'])]
for s in cat['samples']:
 if s['source'].startswith('cuSOLVER/Xgeev/') and s['status']=='PARTIAL':
  d=json.loads((ROOT/s['original_port']['evidence']/'commands.json').read_text());binary=Path(d['run'][0]);jobs.append((Path(s['source']).stem,binary,[s['implementation']]))
results=[]
for name,binary,sources in jobs:
 e=Experiment('R3',name+'/backend-trace','rocm-profile',sources=[__file__]+[ROOT/n for n in sources]);write(e.path/'backend.observed.json',observed);out=e.path/'outputs';out.mkdir();trace=e.path/'trace';trace.mkdir();env=dict(REWRITE_OUTPUT=str(out))
 if name=='rank-svd':env['REWRITE_INPUT']=str(ROOT/'tests/fixtures/rewrite-extensions/svd/original')
 rc=e.command(['rocprofv3','--kernel-trace','--hip-trace','--stats','--output-format','csv','json','--output-directory',str(trace),'--output-file','solver','--',str(binary)],'profile',timeout=180,env=env)
 csvs=[q for q in trace.rglob('*.csv') if 'kernel' in q.name.lower()];rows=[]
 for path in csvs:
  with path.open() as f:rows+=list(csv.DictReader(f))
 names=sorted({r.get('Kernel_Name') or r.get('Name') or r.get('KernelName') or str(r) for r in rows});numeric=[n for n in names if 'rocsolver' in n.lower()]
 r=dict(name=name,return_code=rc,binary_sha256=digest(binary),kernel_records=len(rows),kernel_names=names,solver_algorithm_kernel_names=numeric,blas_kernel_names=[n for n in names if 'rocblas' in n.lower() or n.startswith('Cijk_')],memory_kernel_names=[n for n in names if n.startswith('__amd_rocclr_')],note='BLAS kernels in the original Xgeev programs verify residuals after the eigen call; they do not prove GPU eigensolving.',source_sha256={n:digest(ROOT/n) for n in sources});write(e.path/'kernel-summary.json',r);r['evidence']=e.finish('PROFILE_OBSERVED' if rc==0 else 'PROFILER_FAILED');results.append(r);write(ROOT/'migration/reports/rewrite-solver-backend-traces.json',dict(scope='Actual kernel observations; no host-only eigen routine is promoted from a successful process exit',profiles=results));print(name,rc,len(rows),len(numeric),flush=True)
