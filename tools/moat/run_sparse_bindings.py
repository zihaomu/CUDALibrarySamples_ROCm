#!/usr/bin/env python3
import json,shutil
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from qualification_common import fixture
profiles=json.loads((ROOT/'migration/rewrite/sparse-bindings.json').read_text())['profiles'];build=json.loads((ROOT/'migration/reports/rewrite-sparse-binding-build.json').read_text());observed=capture();results={}
if build['status']!='BUILT':raise RuntimeError('binding build unavailable')
if any(digest(ROOT/n)!=sha for n,sha in build['dependencies'].items()) or digest(ROOT/build['shared_library'])!=build['shared_library_sha256']:raise RuntimeError('stale HIP core')
for p in profiles:
 binary=next(b for b in build['binaries'] if b['sample_id']==p['sample_id'])
 if digest(ROOT/binary['binary'])!=binary['binary_sha256'] or digest(ROOT/p['implementation'])!=binary['implementation_sha256']:raise RuntimeError('stale Fortran entry')
 for case in p['cases']:
  src=ROOT/p['fixture_root']/case;mf=fixture(src,kind='sparse-binding',case=case);mh=digest(src/'manifest.json');comparison='sparse-binding/'+p['kind']+'/'+case+'/'+mh;e=Experiment('R5',p['sample_id'],'rocm-fortran',case=case,sources=[__file__,ROOT/p['source'],ROOT/p['implementation']]+[ROOT/n for n in build['dependencies']],parent=build['experiment_id'],comparison_id=comparison);shutil.copytree(src,e.path/'inputs');write(e.path/'backend.observed.json',observed);out=e.path/'outputs';out.mkdir()
  rc=e.command([str(ROOT/binary['binary'])],'actual-Fortran-entry',env=dict(REWRITE_INPUT=str(e.path/'inputs'),REWRITE_OUTPUT=str(out)));write(out/'manifest.json',dict(files={f.name:dict(bytes=f.stat().st_size,sha256=digest(f)) for f in out.iterdir()}));r=dict(sample_id=p['sample_id'],kind='sparse-binding',profile=p['kind'],language=p['language'],case=case,return_code=rc,output=str(out.relative_to(ROOT)),input_snapshot=str((e.path/'inputs').relative_to(ROOT)),input_manifest_sha256=mh,comparison_id=comparison,experiment_id=e.id,build=build,binary=binary)
  r['evidence']=e.finish('EXECUTED' if rc==0 else 'EXPECTED_REJECTION' if mf['expected_exit']==rc else 'RUNTIME_ERROR');key=p['sample_id']+'/'+case;results[key]=r;write(ROOT/'migration/reports/rewrite-sparse-binding-rocm.json',results);print(p['language'],p['kind'],case,rc,flush=True)
