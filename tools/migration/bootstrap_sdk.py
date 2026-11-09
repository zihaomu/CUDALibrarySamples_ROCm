#!/usr/bin/env python3
"""Project-only development overlay for the split, immutable ROCm SDK wheels."""
import hashlib,json,pathlib
from catalog import ROOT
site=pathlib.Path('/opt/venv/lib/python3.13/site-packages');core=site/'_rocm_sdk_core';libs=site/'_rocm_sdk_libraries';overlay=ROOT/'build/rocm-sdk-overlay';(overlay/'lib').mkdir(parents=True,exist_ok=True)
def link(dest,source):
 if dest.is_symlink():
  if str(dest.readlink())==str(source):return
  dest.unlink()
 if not dest.exists():dest.symlink_to(source,target_is_directory=source.is_dir())
link(overlay/'include',core/'include');link(overlay/'lib/llvm',core/'lib/llvm');link(overlay/'amdgcn',core/'lib/llvm/amdgcn')
identities={}
for directory in [libs/'lib',core/'lib']:
 for src in sorted(directory.glob('lib*.so*')):
  if not src.is_file():continue
  name=src.name.split('.so')[0]+'.so';dest=overlay/'lib'/name
  if dest.exists():continue
  link(dest,src);identities[name]={'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
(ROOT/'migration/environments/sdk-overlay.json').write_text(json.dumps({'rocm_release':'10.1.0','overlay':str(overlay),'identities':identities},indent=2)+'\n');print('SDK overlay:',overlay)
