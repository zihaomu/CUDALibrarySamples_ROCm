#!/usr/bin/env python3
"""Install the pinned CUDA reference SDK only under this project's build/."""
import hashlib,json,pathlib,urllib.request,zipfile
from catalog import ROOT
url='https://files.pythonhosted.org/packages/6e/64/a9a8d9a5e36fb944deab0e2f1118598076cdf829f2e0df030d5b46215478/cutensor_cu13-2.8.1-py3-none-manylinux2014_x86_64.whl';sha='49a6e319c956c2b80e4322d43a9442d595deea176413cd2fa2d45967edea09c5';wheel=ROOT/'build'/url.split('/')[-1];wheel.parent.mkdir(parents=True,exist_ok=True)
if not wheel.exists():urllib.request.urlretrieve(url,wheel)
assert hashlib.sha256(wheel.read_bytes()).hexdigest()==sha
unpacked=ROOT/'build/cutensor-cu13-2.8.1'
with zipfile.ZipFile(wheel) as z:z.extractall(unpacked)
headers=next(unpacked.rglob('cutensor.h')).parent;library=next(unpacked.rglob('libcutensor.so.2'));sdk=ROOT/'build/cuda-sdk';sdk.mkdir(exist_ok=True)
for name,target in [('include',headers),('lib',library.parent)]:
 d=sdk/name
 if not d.exists():d.symlink_to(target.resolve(),target_is_directory=True)
link=library.parent/'libcutensor.so'
if not link.exists():link.symlink_to(library.name)
r={'package':'cutensor-cu13','version':'2.8.1','wheel_url':url,'wheel_sha256':sha,'library':str(library.relative_to(ROOT)),'library_sha256':hashlib.sha256(library.read_bytes()).hexdigest(),'scope':'Project-local CUDA reference SDK only; no global Toolkit changes'};(ROOT/'migration/environments/cuda-cutensor.lock.json').write_text(json.dumps(r,indent=2)+'\n');print(r)
