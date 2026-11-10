#!/usr/bin/env python3
import argparse,hashlib,json,os,pathlib,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--binary',required=True);p.add_argument('--kind',required=True);a=p.parse_args()
src=pathlib.Path(a.input);out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=False)
manifest=json.loads((src/'manifest.json').read_text())
checks={n:hashlib.sha256((src/n).read_bytes()).hexdigest()==r['sha256'] for n,r in manifest['files'].items()}
(out/'input-integrity.json').write_text(json.dumps(checks,indent=2)+'\n')
if not all(checks.values()):raise SystemExit(65)
command=[a.binary,a.kind];env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',REWRITE_INPUT=str(src),REWRITE_OUTPUT=str(out))
(out/'command.json').write_text(json.dumps(dict(argv=command,environment={k:env[k] for k in ['CUDA_VISIBLE_DEVICES','REWRITE_INPUT','REWRITE_OUTPUT']}),indent=2)+'\n')
r=subprocess.run(command,env=env,capture_output=True,text=True);sys.stdout.write(r.stdout);sys.stderr.write(r.stderr)
loaded=[]
for line in r.stdout.splitlines():
 if line.startswith('loaded-library '):
  name=line.removeprefix('loaded-library ');path=pathlib.Path(name)
  if path.is_file():loaded.append(dict(path=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(out/'libraries.loaded.json').write_text(json.dumps(loaded,indent=2)+'\n')
raise SystemExit(r.returncode)
