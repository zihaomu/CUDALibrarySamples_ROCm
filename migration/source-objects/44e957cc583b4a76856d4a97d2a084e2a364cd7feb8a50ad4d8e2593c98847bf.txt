#!/usr/bin/env python3
"""Shared immutable file-fixture and evidence identity gates for later batches."""
import json
from pathlib import Path
from experiment import ROOT,digest
from audit import check

def read(path):return json.loads(Path(path).read_text())
def fixture(path,expected=None,kind=None,case=None):
 path=Path(path)
 if expected is not None and digest(path/'manifest.json')!=expected:raise ValueError('fixture manifest identity')
 data=read(path/'manifest.json')
 if kind is not None and data['kind']!=kind:raise ValueError('fixture kind')
 if case is not None and data['case']!=case:raise ValueError('fixture case')
 for name,meta in data['files'].items():
  file=path/name
  if Path(name).name!=name or not file.is_file() or file.stat().st_size!=meta['bytes'] or digest(file)!=meta['sha256']:raise ValueError('fixture file identity: '+name)
 return data

def evidence(path,sources=(),parent=None,case=None,backend=None,sample=None,comparison=None,outcome=None,check_names=None):
 directory=ROOT/path
 if check(directory):raise ValueError('evidence seal')
 meta=read(directory/'manifest.json');source=read(directory/'source.json')['dependencies']
 if meta['experiment_id']!=directory.name:raise ValueError('evidence ID')
 for field,value in [('parent_experiment_id',parent),('case_id',case),('backend',backend),('sample_id',sample),('comparison_id',comparison),('experiment_outcome',outcome)]:
  if value is not None and meta.get(field)!=value:raise ValueError('evidence '+field)
 for name in sources:
  if source.get(name)!=digest(ROOT/name):raise ValueError('evidence current source '+name)
 if check_names is not None or outcome=='PASSED':
  validation=read(directory/'validation.json');names=[c['check'] for c in validation['checks']]
  if not names or not all(c.get('passed') is True for c in validation['checks']):raise ValueError('evidence checks did not pass')
  if check_names is not None and (set(names)!=set(check_names) or len(names)!=len(check_names)):raise ValueError('evidence check contract')
 return directory,ROOT/meta['raw_artifact_dir'],meta

def guarded(function,*args,**kwargs):
 try:return bool(function(*args,**kwargs))
 except (OSError,KeyError,ValueError,TypeError,StopIteration):return False

def file_run(row,profile,case,backend):
 expected=digest(ROOT/profile['fixture_root']/case/'manifest.json');comparison=profile['kind']+'/'+case+'/'+expected
 directory,raw,meta=evidence(row['evidence'],parent=row['build']['experiment_id'],case=case,backend=backend,sample=profile['sample_id'],comparison=comparison)
 if row['kind']!=profile['kind'] or row['case']!=case or row['experiment_id']!=meta['experiment_id'] or row['input_manifest_sha256']!=expected or row['comparison_id']!=comparison or (ROOT/row['output']).resolve()!=(raw/'outputs').resolve() or (ROOT/row['input_snapshot']).resolve()!=(raw/'inputs').resolve():return False
 fixture(raw/'inputs',expected,profile['kind'],case)
 return True
