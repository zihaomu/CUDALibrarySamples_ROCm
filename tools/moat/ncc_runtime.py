#!/usr/bin/env python3
import json
from experiment import ROOT,Experiment,write
from snapshot import capture
b=json.loads((ROOT/'migration/reports/rewrite-extension-builds.json').read_text())['ncc'];observed=capture();results=[]
for name,argv,expected in [('negative-x',['-x','-1'],1),('short-template',['-tw','7'],1),('huge-template',['-tw','2147483647'],1),('bad-noise',['-noise','256'],1),('negative-timing',['-n','-1'],1),('missing-file',['-i','/nonexistent/ncc.raw'],1),('help',['--help'],0)]:
 e=Experiment('R3','NCC/CLI/'+name,'rocm-invalid-cli',sources=[__file__,ROOT/'rocm/ported/NPP/templateMatching/templateMatching.cpp'],parent=b['experiment_id']);write(e.path/'backend.observed.json',observed)
 rc=e.command([str(ROOT/b['binary'])]+argv,'CLI-contract',cwd=e.path);out=(e.path/e.commands[-1]['stdout']).read_text();err=(e.path/e.commands[-1]['stderr']).read_text();passed=rc==expected and not (e.path/'match_result.pgm').exists() and bool(out or err)
 if name=='help':passed &= 'Usage:' in out and '-noise' in out
 evidence=e.finish('EXPECTED_REJECTION' if passed else 'CLI_GAP',dict(checks=[dict(check=name,passed=passed)]));results.append(dict(test=name,passed=passed,evidence=evidence));print(name,passed,flush=True)
write(ROOT/'migration/reports/rewrite-ncc-runtime.json',dict(status='PASSED' if all(r['passed'] for r in results) else 'FAILED',tests=results))
