#!/usr/bin/env python3
"""Check immutable attempt records, task coverage and pinned control sources."""
import argparse,json
from pathlib import Path
from experiment import ROOT,digest,write

def check(directory):
    seal=json.loads((directory/'sealed.json').read_text());errors=[]
    manifest=json.loads((directory/'manifest.json').read_text())
    for name,row in seal['files'].items():
        p=directory/name
        if not p.exists():
            raw=manifest.get('raw_artifact_dir')
            if not raw and directory.is_relative_to(ROOT/'migration/reports/evidence'):
                raw=str(Path('artifacts')/directory.relative_to(ROOT/'migration/reports/evidence'))
            p=ROOT/(raw or '')/name
        if not p.is_file() or p.stat().st_size!=row['bytes'] or digest(p)!=row['sha256']:errors.append(name)
    return errors

if __name__=='__main__':
    import jsonschema
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path);a=p.parse_args()
    dirs=[a.directory] if a.directory else [p.parent for p in (ROOT/'migration/reports/evidence/rewrite').rglob('sealed.json')]
    bad={str(d.relative_to(ROOT)):check(d) for d in dirs};bad={k:v for k,v in bad.items() if v}
    tasks=json.loads((ROOT/'migration/moat/tasks.json').read_text())['tasks'];cat=json.loads((ROOT/'migration/samples.yaml').read_text())['samples']
    checks=[dict(check='639-stable-task-IDs',passed=len(tasks)==639 and {t['sample_id'] for t in tasks}=={s['id'] for s in cat}),dict(check='sealed-attempt-integrity',passed=not bad,attempts=len(dirs),errors=bad)]
    schema_errors=[]
    for name,path in [('tasks','migration/moat/tasks.json'),('libraries','migration/libraries.json'),('backend-routes','migration/backend-routes.json')]:
        schema=json.loads((ROOT/'migration/moat/schema'/(name+'.schema.json')).read_text())
        schema_errors += [name+': '+e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(json.loads((ROOT/path).read_text()))]
    schema=json.loads((ROOT/'migration/moat/schema/experiment.schema.json').read_text());validator=jsonschema.Draft202012Validator(schema)
    for d in dirs:schema_errors += [str(d)+': '+e.message for e in validator.iter_errors(json.loads((d/'manifest.json').read_text()))]
    checks.append(dict(check='structured-record-schemas',passed=not schema_errors,errors=schema_errors))
    result=dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks)
    write(ROOT/'migration/reports/rewrite-evidence-audit.json',result);print(json.dumps(result));raise SystemExit(0 if result['status']=='PASSED' else 1)
