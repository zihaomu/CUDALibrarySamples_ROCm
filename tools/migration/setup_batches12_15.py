#!/usr/bin/env python3
"""Restore project-only MPICH/MathDx wheels from official PyPI, pinned by SHA256."""
import argparse,hashlib,json,pathlib,urllib.request,zipfile,platform
from catalog import ROOT
p=argparse.ArgumentParser();p.add_argument('--check',action='store_true',help='Check existing library identities without downloading or writing');a=p.parse_args();lock=json.loads((ROOT/'migration/environments/batches12_15-dependencies.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if not a.check:
 if platform.machine()!='x86_64':raise RuntimeError('Pinned project MPI wheel requires Linux x86_64')
 cache=ROOT/'build/batches12_15-wheels';cache.mkdir(parents=True,exist_ok=True)
 for name,key,target in [('mpich','mpi','build/mpi'),('nvidia-mathdx','native_mathdx','build/mathdx-sdk')]:
  item=lock[key];metadata=json.load(urllib.request.urlopen('https://pypi.org/pypi/'+name+'/'+item['version']+'/json'));wheel=next(x for x in metadata['urls'] if x['digests']['sha256']==item['wheel_sha256']);file=cache/wheel['filename']
  if not file.exists() or sha(file)!=item['wheel_sha256']:urllib.request.urlretrieve(wheel['url'],file)
  assert sha(file)==item['wheel_sha256']
  with zipfile.ZipFile(file) as z:
   for info in z.infolist():
    if info.is_dir():continue
    relative=info.filename
    if name=='mpich':
     if '.data/data/' not in relative:continue
     relative=relative.split('.data/data/',1)[1]
    path=ROOT/target/relative
    if '..' in pathlib.PurePosixPath(relative).parts:raise ValueError('invalid wheel member')
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(info));path.chmod(0o755 if relative.startswith('bin/') else 0o644)
for name,expected in lock['mpi']['libraries'].items():
 file=ROOT/name
 if not file.exists() or sha(file)!=expected:raise RuntimeError('MPI identity mismatch: '+name)
assert (ROOT/'build/mathdx-sdk/nvidia/mathdx/include/cufftdx.hpp').exists()
print('Project MPICH4.3.2 library hashes and MathDx25.6 SDK available; shared foundation unchanged.')
