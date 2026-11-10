#!/usr/bin/env python3
import json,shutil
from experiment import ROOT,Experiment,write
from snapshot import capture
b=json.loads((ROOT/'migration/reports/rewrite-extension-builds.json').read_text())['svd'];observed=capture();results=[]
tests=[('zero-m',dict(m=0)),('wide-shape',dict(n=4)),('short-lda',dict(lda=1)),('short-U',dict(ldu=1)),('short-V',dict(ldv=1)),('zero-rank',dict(rank=0)),('oversize-rank',dict(rank=3)),('short-stride',dict(strideA=1)),('bad-batch',dict(batch=0)),('fractional-rank',dict(rank=1.5)),('huge-stride',dict(strideU=1e20))]
for name,change in tests:
 e=Experiment('R3','SVD/'+name,'rocm-invalid-descriptor',sources=[__file__,ROOT/'rocm/backends/solver/rank_svd.hpp'],parent=b['experiment_id']);write(e.path/'backend.observed.json',observed);src=e.path/'inputs';shutil.copytree(ROOT/'tests/fixtures/rewrite-extensions/svd/original',src);cfg=json.loads((src/'config.json').read_text());cfg.update(change);(src/'config.txt').write_text(''.join(f'{k} {v}\n' for k,v in cfg.items()));write(src/'config.json',cfg);out=e.path/'outputs';out.mkdir()
 rc=e.command([str(ROOT/b['binary'])],'reject-descriptor',env=dict(REWRITE_INPUT=str(src),REWRITE_OUTPUT=str(out)));err=(e.path/e.commands[-1]['stderr']).read_text();passed=rc==1 and 'invalid' in err and not list(out.iterdir());ev=e.finish('EXPECTED_REJECTION' if passed else 'GUARD_FAILED',dict(checks=[dict(check=name,passed=passed)]));results.append(dict(test=name,passed=passed,evidence=ev));print(name,passed,flush=True)
write(ROOT/'migration/reports/rewrite-svd-runtime.json',dict(status='PASSED' if all(r['passed'] for r in results) else 'FAILED',tests=results))
