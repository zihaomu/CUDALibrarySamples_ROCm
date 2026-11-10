#!/usr/bin/env python3
import json
from experiment import ROOT,Experiment,write
from snapshot import capture
b=json.loads((ROOT/'migration/reports/rewrite-extension-builds.json').read_text())['crc32'];observed=capture();results=[]
for name,argv in [('no-files',[]),('flag-without-file',['-f']),('unknown-flag',['--unknown','file']),('missing-file',['-f','/nonexistent/crc32.raw']),('zero-chunks',['-f','empty.raw'])]:
 e=Experiment('R4','nvCOMP/examples::nvcomp_crc32.cu/CLI/'+name,'rocm-invalid-cli',sources=[__file__,ROOT/'rocm/backends/codec/crc32.hpp'],parent=b['experiment_id']);write(e.path/'backend.observed.json',observed);(e.path/'empty.raw').write_bytes(b'');out=e.path/'outputs';out.mkdir();rc=e.command([str(ROOT/b['binary'])]+argv,'CLI-rejection',cwd=e.path,env=dict(REWRITE_OUTPUT=str(out)));err=(e.path/e.commands[-1]['stderr']).read_text();passed=rc==1 and bool(err) and not list(out.iterdir());ev=e.finish('EXPECTED_REJECTION' if passed else 'CLI_GAP',dict(checks=[dict(check=name,passed=passed)]));results.append(dict(test=name,passed=passed,evidence=ev));print(name,passed,flush=True)
write(ROOT/'migration/reports/rewrite-crc32-runtime.json',dict(status='PASSED' if all(r['passed'] for r in results) else 'FAILED',tests=results))
