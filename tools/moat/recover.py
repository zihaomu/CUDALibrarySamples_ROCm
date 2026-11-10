#!/usr/bin/env python3
"""Seal an explicitly identified, abandoned initialization; do not infer GPU results."""
import argparse,json,shutil,os,signal,platform,time
from pathlib import Path
from experiment import ROOT,digest,write,now,append,INDEX,recorder_alive,process_start
p=argparse.ArgumentParser();p.add_argument('--target',type=Path,required=True);p.add_argument('--reason',required=True);a=p.parse_args();d=a.target.resolve()
if not d.is_relative_to(ROOT/'artifacts/rewrite') or (d/'sealed.json').exists():raise SystemExit('Only unsealed project attempts can be recovered')
m=json.loads((d/'manifest.json').read_text())
if m.get('recorder_pid') and recorder_alive(m) is not False:raise SystemExit('Recorder is alive or cannot be verified dead; refusing recovery')
child=d/'subprocess.json'
if child.exists():
    c=json.loads(child.read_text())
    if c.get('hostname')==platform.node() and process_start(c['pid'])==c.get('start_ticks'):
        os.killpg(c['pid'],signal.SIGKILL)
shutil.copyfile(d/'manifest.json',d/'manifest.before-recovery.json')
m.update(experiment_outcome='INTERRUPTED' if m.get('recorder_pid') else 'INITIALIZATION_ERROR',previous_outcome=m.get('experiment_outcome'),finished_at_utc=now(),reason=a.reason,raw_artifact_dir=str(d.relative_to(ROOT)),eligible_for_sample_pass=False)
write(d/'manifest.json',m);write(d/'recovery.json',dict(observed_reason=a.reason,numerical_result='NOT_QUALIFIED',note='Recorder confirmed dead or abandoned before subprocess initialization; preserve existing streams without reconstructing results.'))
append(INDEX,dict(event='recovered-interruption',timestamp_utc=now(),experiment_id=m['experiment_id'],evidence=str(d.relative_to(ROOT)),reason=a.reason))
write(d/'sealed.json',dict(schema_version=1,files={str(q.relative_to(d)):dict(sha256=digest(q),bytes=q.stat().st_size) for q in d.rglob('*') if q.is_file()}))
archive=ROOT/'migration/reports/evidence'/d.relative_to(ROOT/'artifacts');shutil.copytree(d,archive,ignore=lambda directory,names:[n for n in names if (Path(directory)/n).is_file() and ((Path(directory)/n).stat().st_size>4*1024*1024 or Path(n).suffix in {'.bin','.o','.so'})]);print(archive.relative_to(ROOT))
