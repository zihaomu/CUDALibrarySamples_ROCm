#!/usr/bin/env python3
"""Pin primary-source candidate declarations; no capability claim from a README alone."""
import argparse,json,hashlib,re,sys,urllib.request,urllib.parse,subprocess
from pathlib import Path
from experiment import ROOT,Experiment,write
REPOS={'libintx':'ValeevGroup/libintx','gauxc':'wavefunction91/GauXC','quick':'merzlab/QUICK','hipcim':'AMD-Ecosystem/hipCIM'}
def inspect(repo):
 def fetch(url):
  request=urllib.request.Request(url,headers={'User-Agent':'CUDALibrarySamples-ROCm-evidence','Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(request,timeout=30) as response:return response.read()
 url='https://api.github.com/repos/'+repo;pin_command=None;api_error=None
 try:
  metadata=json.loads(fetch(url));branch=metadata['default_branch'];head=json.loads(fetch(url+'/commits/'+urllib.parse.quote(branch,safe='')));sha=head['sha'];tree=head['commit']['tree']['sha']
 except Exception as error:
  api_error=str(error);pin_command=['git','ls-remote','--symref','https://github.com/'+repo+'.git','HEAD'];result=subprocess.check_output(pin_command,text=True,timeout=45);branch=next(line.split('refs/heads/',1)[1].split()[0] for line in result.splitlines() if line.startswith('ref:'));sha=next(line.split()[0] for line in result.splitlines() if re.match('[0-9a-f]{40}\\s',line));metadata={};tree=None
 if not re.fullmatch('[0-9a-f]{40}',sha):raise ValueError('invalid upstream commit')
 files={};markers={};packages=[]
 for name in ['README.md','CMakeLists.txt','pyproject.toml','LICENSE','LICENSE.txt','COPYING','license']:
  try:body=fetch('https://raw.githubusercontent.com/'+repo+'/'+sha+'/'+name)
  except Exception:continue
  files[name]=dict(sha256=hashlib.sha256(body).hexdigest(),bytes=len(body));text=body.decode(errors='replace');markers[name]=sorted(set(re.findall(r'\b[A-Z][A-Z0-9_]*(?:HIP|CUDA)[A-Z0-9_]*\b',text)))
  if name=='CMakeLists.txt':packages=sorted(set(re.findall(r'find_package\(\s*([A-Za-z0-9_]+)',text,re.I)))
 return dict(repository='https://github.com/'+repo,commit=sha,git_tree=tree,source_url='https://github.com/'+repo+'/tree/'+sha,default_branch=branch,license_spdx=(metadata.get('license') or {}).get('spdx_id','SEE_PINNED_LICENSE'),files=files,backend_markers=markers,cmake_find_packages=packages,pin_command=pin_command,api_error=api_error,scope='Primary source declarations and prerequisites only; not built GPU functionality or a qualified sample')
p=argparse.ArgumentParser();p.add_argument('--single',nargs=2);args=p.parse_args()
if args.single:
 try:r=inspect(args.single[0]);write(args.single[1],r);print(r['repository'],r['commit']);raise SystemExit(0)
 except Exception as error:write(args.single[1],dict(repository=args.single[0],error=str(error)));raise SystemExit(1)
rows=[]
for name,repo in REPOS.items():
 e=Experiment('R6','candidate-source/'+name,'host-source-probe',sources=[__file__]);out=e.path/'candidate.json';rc=e.command([sys.executable,__file__,'--single',repo,str(out)],'pin-primary-upstream-source',timeout=240);r=json.loads(out.read_text());r.update(name=name,return_code=rc);r['evidence']=e.finish('OBSERVED' if rc==0 else 'SDK_UNAVAILABLE');rows.append(r);write(ROOT/'migration/reports/rewrite-R6-candidate-sources.json',dict(candidates=rows));print(name,rc,flush=True)
