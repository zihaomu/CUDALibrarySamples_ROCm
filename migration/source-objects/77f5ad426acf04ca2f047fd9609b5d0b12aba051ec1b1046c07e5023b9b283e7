"""Verify and materialize the exact per-attempt inputs, including legacy bundles."""
import json,shutil,tarfile
from pathlib import Path
from experiment import ROOT,digest

def verify(path,expected_hash=None):
    path=Path(path);manifest=path/'manifest.json'
    if expected_hash and digest(manifest)!=expected_hash:raise ValueError('input manifest identity mismatch')
    data=json.loads(manifest.read_text())
    for name,r in data['files'].items():
        p=path/name
        if Path(name).name!=name or not p.is_file() or p.stat().st_size!=r['bytes'] or digest(p)!=r['sha256']:raise ValueError('input file identity mismatch: '+name)
    cfg=json.loads((path/'config.json').read_text());tokens=(path/'config.txt').read_text().split();text={tokens[i]:float(tokens[i+1]) for i in range(0,len(tokens),2)}
    if cfg!=data['config'] or cfg!=text:raise ValueError('binary and reference configuration contracts differ')
    return data

def copy_run_inputs(record,destination):
    destination=Path(destination);source=ROOT/record['input_snapshot'] if record.get('input_snapshot') else (ROOT/record['output']).parent/'inputs'
    if source.is_dir():shutil.copytree(source,destination)
    else:
        parent=json.loads((ROOT/record['evidence']/'manifest.json').read_text())['parent_experiment_id']
        bundle=ROOT/'artifacts/rewrite/R1-R2/first-eight-native-and-compatible'/parent/'inputs.tar.gz'
        seal=json.loads((bundle.parent/'sealed.json').read_text())['files']['inputs.tar.gz']
        if digest(bundle)!=seal['sha256']:raise ValueError('CUDA input bundle identity mismatch')
        prefix='tests/fixtures/rewrite-first/'+record['kind']+'/'+record['case']+'/'
        destination.mkdir()
        with tarfile.open(bundle,'r:gz') as f:
            for m in f.getmembers():
                if m.isfile() and m.name.startswith(prefix):
                    name=m.name[len(prefix):]
                    if Path(name).name!=name:raise ValueError('unexpected fixture archive entry')
                    (destination/name).write_bytes(f.extractfile(m).read())
    verify(destination,record['input_manifest_sha256'])
    if record['comparison_id']!=record['kind']+'/'+record['case']+'/'+record['input_manifest_sha256']:raise ValueError('comparison identity mismatch')
    return destination
