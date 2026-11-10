#!/usr/bin/env python3
import json,csv,shutil
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
b=json.loads((ROOT/'migration/reports/rewrite-extension-builds.json').read_text())['crc32'];fixture=ROOT/'tests/fixtures/rewrite-extensions/crc32/original';mh=digest(fixture/'manifest.json');e=Experiment('R4','nvCOMP/examples::nvcomp_crc32.cu/backend-trace','rocm-profile',case='original',sources=[__file__,ROOT/'rocm/backends/codec/crc32.hpp'],parent=b['experiment_id'],comparison_id='crc32/original/'+mh);write(e.path/'backend.observed.json',capture());shutil.copytree(fixture,e.path/'inputs');out=e.path/'outputs';out.mkdir();trace=e.path/'trace';trace.mkdir();argv=json.loads((fixture/'manifest.json').read_text())['argv']
rc=e.command(['rocprofv3','--kernel-trace','--output-format','csv','json','--output-directory',str(trace),'--output-file','crc','--',str(ROOT/b['binary'])]+argv,'profile',cwd=e.path/'inputs',env=dict(REWRITE_OUTPUT=str(out)))
rows=[]
for p in trace.rglob('*kernel_trace.csv'):
 with p.open() as f:rows+=list(csv.DictReader(f))
names=[r.get('Kernel_Name') or r.get('Name') or str(r) for r in rows];crc=[name for name in names if 'crc32_ieee' in name];r=dict(binary=b['binary'],binary_sha256=b['binary_sha256'],build_experiment_id=b['experiment_id'],input_manifest_sha256=mh,return_code=rc,crc_kernel_dispatches=len(crc),kernel_names=names);write(e.path/'kernel-summary.json',r);r['evidence']=e.finish('PROFILE_OBSERVED' if rc==0 else 'PROFILER_FAILED');write(ROOT/'migration/reports/rewrite-crc32-trace.json',r);print(rc,len(crc))
