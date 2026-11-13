#!/usr/bin/env python3
"""Bind each cold result to that checkout's sealed build, command and output tree."""
import json
from pathlib import Path
from experiment import digest

MODES=('padded','compact','inplace','no-labels')
NEGATIVES=('missing-first','missing-last','truncated-first','blocked-output')
COUNTS={'image-watershed-completion-entries-build.json':1,'image-watershed-v2-build.json':1,'image-watershed-v2-controls.json':1,'image-watershed-completion-entries-runs.json':2,'image-watershed-completion-entry-trace.json':2,'image-watershed-completion-entry-replay.json':2,'image-watershed-completion-entry-negative.json':8,**{f'image-watershed-completion-AMD-{m}.json':1 for m in MODES}}

def need(ok,message):
    if not ok:raise ValueError(message)

def inside(root,name):
    p=Path(name);need(not p.is_absolute() and '..' not in p.parts,'cold paths must be relative without traversal')
    result=(root/p).resolve();need(result.is_relative_to(root.resolve()),'cold path escapes checkout');return result

def bound(root,row,member,commit):
    proof=inside(root,row['evidence']);need(proof.is_relative_to(root/'migration/reports/evidence/rewrite'),'cold evidence archive location')
    manifest=json.loads((proof/'manifest.json').read_text());raw=inside(root,manifest['raw_artifact_dir']);need(raw.is_relative_to(root/'artifacts/rewrite'),'cold raw location')
    need(proof==root/'migration/reports/evidence'/raw.relative_to(root/'artifacts'),'cold archive/raw correspondence')
    seal=json.loads((proof/'sealed.json').read_text());need((proof/'sealed.json').read_bytes()==(raw/'sealed.json').read_bytes(),'cold raw and archive seals match')
    for name,identity in seal['files'].items():
        path=inside(raw,name);need(path.is_file() and path.stat().st_size==identity['bytes'] and digest(path)==identity['sha256'],'cold raw sealed file '+name)
        archived=inside(proof,name)
        if archived.exists():need(archived.is_file() and digest(archived)==identity['sha256'],'cold archive sealed file '+name)
    need(json.loads((raw/member).read_text())=={k:v for k,v in row.items() if k!='evidence'},'fresh row must equal actual sealed child record')
    source=json.loads((raw/'source.json').read_text());need(source['commit']==commit,'actual cold child source commit')
    need(set(source['source_objects'])==set(source['dependencies']),'cold source snapshot completeness')
    for name,sha in source['dependencies'].items():
        path=inside(root,name);obj=inside(root,source['source_objects'][name]);need(path.is_file() and digest(path)==sha and obj.is_relative_to(root/'migration/source-objects') and obj.name==sha and digest(obj)==sha,'cold current dependency '+name)
    commands=json.loads((raw/'commands.json').read_text());need(bool(commands),'cold actual commands required')
    if 'output_dir' in row:
        folder=inside(root,row['output_dir']);need(folder==raw/('outputs' if 'products' in row else 'images'),'cold output belongs to selected child')
    return raw,manifest,source,commands

def inventory(selected,actual):
    need(len(selected)==21 and len(set(selected))==21,'twenty-one unique selected cold children')
    need(set(selected)==set(actual) and len(actual)==21,'selected reports exactly cover actual cold children')

def validate(root,commit,reports=None):
    root=Path(root).resolve()
    reports=reports if reports is not None else {n:json.loads((root/'migration/reports'/n).read_text()) for n in COUNTS}
    need(set(reports)==set(COUNTS),'complete cold report inventory');verified={};selected=[]
    for name,count in COUNTS.items():
        group=reports[name];rows=group if isinstance(group,list) else [group];need(len(rows)==count,'exact cold report row count '+name)
        member='build.json' if name.endswith('-build.json') else 'run.json' if name=='image-watershed-completion-entries-runs.json' else 'result.json'
        verified[name]=[]
        for row in rows:
            info=bound(root,row,member,commit);selected.append(info[1]['experiment_id']);verified[name].append((row,*info))
    entry=reports['image-watershed-completion-entries-build.json'];probe=reports['image-watershed-v2-build.json']
    for name,build in [('image-watershed-completion-entries-build.json',entry),('image-watershed-v2-build.json',probe)]:
        _,raw,manifest,source,commands=verified[name][0];binaries=build['binaries'] if 'binaries' in build else {'probe':build['binary']}
        need(build['status']=='BUILT' and build['return_code']==0 and len(commands)==len(binaries),'successful exact cold build')
        need(manifest['backend']=='rocm-build' and manifest['experiment_outcome']=='EXECUTED','actual cold build backend')
        for family,item in binaries.items():
            binary=inside(root,item['path']);need(binary.parent==raw and digest(binary)==item['sha256'],'binary produced by selected cold build')
            command=next((c for c in commands if c['argv'][-2:]==['-o',str(binary)]),None)
            need(command is not None and command['return_code']==0 and command['argv'][0]=='hipcc' and '--offload-arch=gfx1201' in command['argv'],'actual cold compiler output')
            expected=[str(root/'rocm/probes/image/watershed_v2_probe.cpp')] if family=='probe' else [str(root/('rocm/ported/NPP/watershedSegmentation/watershedSegmentation.cpp' if family=='NPP' else 'rocm/ported/NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp')),str(root/'rocm/common/image/watershed.hip')]
            need(all(p in command['argv'] for p in expected),'actual cold compiler sources')
    samples=json.loads((root/'migration/rewrite/image-watershed-profile.json').read_text())['samples'];ids={s['sample_id'] for s in samples}
    for name,records in verified.items():
        if name.endswith('-build.json'):continue
        if name=='image-watershed-v2-controls.json':
            row,raw,manifest,source,commands=records[0];need(manifest['sample_id']=='watershed-view-and-allocation-controls' and manifest['backend']=='rocm' and manifest['experiment_outcome']=='PASSED','cold controls identity')
            need(len(commands)==2 and all(c['return_code']==0 for c in commands) and commands[0]['argv'][-2:]==['-o',str(raw/'controls')] and commands[1]['argv']==[str(raw/'controls')] and digest(raw/'controls')==row['binary_sha256'],'cold controls compiler and executable');continue
        if 'completion-AMD-' in name:
            mode=name.removesuffix('.json').rsplit('-',1)[1]
            if name.endswith('no-labels.json'):mode='no-labels'
            row,raw,manifest,source,commands=records[0];binary=inside(root,probe['binary']['path'])
            need(row['key']=='AMD-'+mode and row['build_evidence']==probe['evidence'] and row['binary_sha256']==probe['binary']['sha256'],'cold probe mode/build binding')
            need(manifest['sample_id']=='watershed-complete-AMD-'+mode and manifest['backend']=='rocm' and manifest['experiment_outcome']=='EXECUTED','cold corpus child identity')
            need(len(commands)==1 and commands[0]['return_code']==0 and commands[0]['argv']==[str(binary),str(root/'migration/fixtures/image-watershed-completion'),str(raw/'outputs'),mode],'cold corpus actual command')
            need(source['dependencies'].get('migration/reports/image-watershed-v2-build.json')==digest(root/'migration/reports/image-watershed-v2-build.json'),'cold actual probe build snapshot');continue
        action='run' if name.endswith('-runs.json') else name.removesuffix('.json').rsplit('-',1)[1]
        need({r[0]['sample_id'] for r in records}==ids,'cold both actual entry identities')
        need(len({(r[0]['sample_id'],r[0].get('case','original')) for r in records})==len(records),'no duplicate cold entry cases')
        if action=='negative':need({(r[0]['sample_id'],r[0]['case']) for r in records}=={(s,c) for s in ids for c in NEGATIVES},'all cold IO cases')
        for row,raw,manifest,source,commands in records:
            family=row['sample_id'].split('/')[0];binary=inside(root,entry['binaries'][family]['path'])
            need(row['family']==family and row['build_evidence']==entry['evidence'] and row['binary_sha256']==entry['binaries'][family]['sha256'],'cold original entry build identity')
            need(manifest['sample_id']==row['sample_id'] and manifest['backend']==('rocm-complete-original-entry' if action=='run' else 'rocm-complete-entry-'+action),'cold original child backend')
            expected=[str(binary)] if action!='trace' else ['rocprofv3','--kernel-trace','--output-format','csv','--output-directory',str(raw/'trace'),'--',str(binary)]
            need(len(commands)==1 and commands[0]['argv']==expected and commands[0]['cwd']==str(raw/'work') and commands[0]['return_code']==(1 if action=='negative' else 0),'cold actual entry executable/cwd/return')
            need(source['dependencies'].get('migration/reports/image-watershed-completion-entries-build.json')==digest(root/'migration/reports/image-watershed-completion-entries-build.json'),'cold actual entry build snapshot')
    actual=[json.loads(p.read_text())['experiment_id'] for p in (root/'artifacts/rewrite').rglob('manifest.json')];inventory(selected,actual)
    return dict(status='PASSED',selected_child_ids=selected,children=21)
