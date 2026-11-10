#!/usr/bin/env python3
"""Execute invalid descriptors and verify rejection before allocating device buffers."""
import json,shutil
from pathlib import Path
from experiment import Experiment,ROOT,write
from snapshot import capture
builds=json.loads((ROOT/'migration/reports/rewrite-first-builds.json').read_text());observed=capture();results=[]
for kind in ['lu','posv','trsm']:
    fixture=ROOT/'tests/fixtures/rewrite-first'/kind/'original';base=json.loads((fixture/'config.json').read_text())
    tests=[('zero-m',dict(m=0)),('negative-n',dict(n=-1)),('short-lda',dict(lda=1)),('zero-batch',dict(batch=0)),('negative-rhs',dict(nrhs=-1)),('zero-repeat',dict(repeat=0)),('zero-threads',dict(threads=0)),('huge-threads',dict(threads=1025)),('fractional-lda',dict(lda=3.5)),('oversize-shape',dict(n=65))]
    tests += [('nonsquare',dict(m=31)),('short-ldb',dict(ldb=1))] if kind=='posv' else [('extra-batch',dict(batch=2))]
    for name,change in tests:
        e=Experiment('R2',kind+'/'+name,'rocm-invalid-descriptor',sources=[__file__,ROOT/'rocm/device/solver/block_solvers.hpp'],parent=builds[kind]['experiment_id'])
        src=e.path/'inputs';shutil.copytree(fixture,src);cfg=dict(base,**change)
        (src/'config.txt').write_text(''.join(f'{k} {v}\n' for k,v in cfg.items()));write(src/'config.json',cfg);out=e.path/'outputs';out.mkdir();write(e.path/'backend.observed.json',observed)
        rc=e.command([str(ROOT/builds[kind]['binary'])],'reject-descriptor',env=dict(REWRITE_INPUT=str(src),REWRITE_OUTPUT=str(out)))
        err=(e.path/e.commands[-1]['stderr']).read_text();passed=rc==1 and ('invalid' in err or 'unsupported' in err) and not list(out.iterdir())
        # An expected failing process is evidence of rejection, not a passing numerical run.
        evidence=e.finish('EXPECTED_REJECTION' if passed else 'GUARD_FAILED',dict(checks=[dict(check=name,passed=passed)]))
        results.append(dict(kind=kind,test=name,passed=passed,evidence=evidence));print(kind,name,passed,flush=True)
write(ROOT/'migration/reports/rewrite-first-runtime-checks.json',dict(status='PASSED' if all(r['passed'] for r in results) else 'FAILED',tests=results))
