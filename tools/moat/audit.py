#!/usr/bin/env python3
"""Check immutable attempt records, task coverage and pinned control sources."""
import argparse,json
from pathlib import Path
from experiment import ROOT,digest,write,recorder_alive

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
    source=directory/'source.json'
    if source.exists():
        data=json.loads(source.read_text());objects=data.get('source_objects')
        if data.get('provenance_version',0)>=2 and objects is None:errors.append('source-object mapping absent')
        if objects is not None:
            dependencies=data.get('dependencies',{})
            if set(objects)!=set(dependencies):errors.append('source-object mapping completeness')
            for name,path in objects.items():
                p=ROOT/path;sha=dependencies.get(name)
                if not p.is_relative_to(ROOT/'migration/source-objects') or p.name!=sha or not p.is_file() or digest(p)!=sha:errors.append('source-object:'+name)
    return errors

def unfinished():
    active=[];orphans=[];terminal=[];pending=[]
    manifests={}
    for p in (ROOT/'artifacts/rewrite').glob('*/*/*/manifest.json'):
        m=json.loads(p.read_text());manifests[m['experiment_id']]=(p,m)
        if m.get('experiment_outcome')=='RUNNING':
            (active if recorder_alive(m) is True else orphans).append(str(p.parent.relative_to(ROOT)))
        elif not (p.parent/'sealed.json').exists():terminal.append(str(p.parent.relative_to(ROOT)))
        elif not (ROOT/'migration/reports/evidence'/p.parent.relative_to(ROOT/'artifacts')/'sealed.json').exists():pending.append(str(p.parent.relative_to(ROOT)))
    index=ROOT/'migration/reports/rewrite-experiments.jsonl'
    events=[json.loads(line) for line in index.read_text().splitlines()] if index.exists() else []
    started={e['experiment_id'] for e in events if e['event']=='start'}
    ended={e['experiment_id'] for e in events if e['event'] in ['finish','recovered-initialization','recovered-interruption']}
    unmatched=[]
    for eid in started-ended:
        pair=manifests.get(eid)
        if not pair or recorder_alive(pair[1]) is not True:unmatched.append(eid)
    return dict(check='unfinished-attempt-accounting',passed=not (orphans or terminal or pending or unmatched),active=active,abandoned_or_unverifiable=orphans,terminal_unsealed=terminal,archive_pending=pending,unmatched_starts=unmatched)

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
    checks.append(unfinished())
    result=dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks)
    write(ROOT/'migration/reports/rewrite-evidence-audit.json',result);print(json.dumps(result));raise SystemExit(0 if result['status']=='PASSED' else 1)
