#!/usr/bin/env python3
"""Download private NVIDIA image SDKs strictly from recorded vendor manifests."""
import json,shutil,tarfile
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def main():
 manifests=json.loads((ROOT/'migration/reports/image-I0-SDK-manifests.json').read_text())['results'];rows=[]
 for name,key,variant in [('nvjpeg2000','libnvjpeg_2k','cuda13'),('nppplus','libnpp_plus','cuda12')]:
  package=manifests[name]['manifest'][key];item=package['linux-x86_64'][variant];url='https://developer.download.nvidia.com/compute/'+name+'/redist/'+item['relative_path'];e=Experiment('I0','image-private-'+name+'-SDK','host-download',sources=[__file__,ROOT/'migration/reports/image-I0-SDK-manifests.json']);archive=e.path/'sdk.tar.xz';rc=e.command(['curl','--fail','--location','--connect-timeout','15','--max-time','600','--retry','1','--output',str(archive),url],'official-archive-download',timeout=650);valid=rc==0 and archive.stat().st_size==int(item['size']) and digest(archive)==item['sha256'];prefix=ROOT/'build/image-cuda-sdk'/name
  if valid:
   unpack=e.path/'unpack';unpack.mkdir()
   with tarfile.open(archive,'r:xz') as tar:tar.extractall(unpack,filter='data')
   children=list(unpack.iterdir());sdk=children[0] if len(children)==1 else unpack
   if prefix.exists():raise RuntimeError('Existing SDK prefix must be checked explicitly before replacement '+str(prefix))
   prefix.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(sdk,prefix)
  row=dict(status='VERIFIED_DOWNLOAD' if valid else 'DOWNLOAD_FAILED',SDK=name,version=package['version'],variant=variant,url=url,vendor_sha256=item['sha256'],actual_sha256=digest(archive) if archive.exists() else None,prefix=str(prefix.relative_to(ROOT)),files={str(p.relative_to(prefix)):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in prefix.rglob('*') if p.is_file() and (p.suffix in ['.h','.txt'] or '.so' in p.name)} if valid else {})
  write(e.path/'sdk-identity.json',row);ref=e.finish('OBSERVED' if valid else 'SDK_UNAVAILABLE');row['evidence']=ref;rows.append(row);write(ROOT/'migration/reports/image-I0-private-SDKs.json',rows);record('I0',name+' SDK '+package['version']+' / '+variant+' 官方下载与SHA核验：'+row['status']+'；仅项目私有前缀，编译/运行资格另验。',[ref]);print(name,row['status'],flush=True)
if __name__=='__main__':main()
