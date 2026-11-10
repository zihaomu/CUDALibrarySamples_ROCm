#!/usr/bin/env python3
"""Seal an explicitly identified, abandoned initialization; do not infer GPU results."""
import argparse,json,shutil
from pathlib import Path
from experiment import ROOT,digest,write,now,append,INDEX
p=argparse.ArgumentParser();p.add_argument('--target',type=Path,required=True);p.add_argument('--reason',required=True);a=p.parse_args();d=a.target.resolve()
if not d.is_relative_to(ROOT/'artifacts/rewrite') or (d/'sealed.json').exists():raise SystemExit('Only unsealed project attempts can be recovered')
m=json.loads((d/'manifest.json').read_text())
if m.get('experiment_outcome')!='RUNNING':raise SystemExit('Attempt is already terminal')
if m.get('recorder_pid'):raise SystemExit('Explicit process verification required for attempts with a recorder PID')
shutil.copyfile(d/'manifest.json',d/'manifest.before-recovery.json')
m.update(experiment_outcome='INITIALIZATION_ERROR',finished_at_utc=now(),reason=a.reason,raw_artifact_dir=str(d.relative_to(ROOT)),eligible_for_sample_pass=False)
write(d/'manifest.json',m);write(d/'recovery.json',dict(observed_reason=a.reason,numerical_result='NOT_RUN',note='Recovered an abandoned constructor before any subprocess; no reconstructed stdout/stderr.'))
append(INDEX,dict(event='recovered-initialization',timestamp_utc=now(),experiment_id=m['experiment_id'],evidence=str(d.relative_to(ROOT)),reason=a.reason))
write(d/'sealed.json',dict(schema_version=1,files={str(q.relative_to(d)):dict(sha256=digest(q),bytes=q.stat().st_size) for q in d.rglob('*') if q.is_file()}))
archive=ROOT/'migration/reports/evidence'/d.relative_to(ROOT/'artifacts');shutil.copytree(d,archive);print(archive.relative_to(ROOT))
