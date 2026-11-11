#!/usr/bin/env python3
"""Transfer verified private SDK archives and inspect actual native loader dependencies."""
import json,shlex
from pathlib import Path
from experiment import ROOT,Experiment,write
from image_progress import record

def main():
 results=[]
 for r in json.loads((ROOT/'migration/reports/image-I0-private-SDKs.json').read_text()):
  e=Experiment('I0','image-native-private-'+r['SDK'],'cuda-setup',sources=[__file__]);raw=ROOT/json.loads((ROOT/r.get('archive_evidence',r['evidence'])/'manifest.json').read_text())['raw_artifact_dir'];remote='/tmp/image-library-private-SDKs/'+r['SDK']+'-'+r['version'];archive=remote+'/sdk.tar.xz';rc=e.command(['ssh','nvidia-5090x2',shlex.join(['mkdir','-p',remote])],'private-native-prefix');rc=rc or e.command(['scp',str(raw/r.get('archive_file','sdk.tar.xz')),'nvidia-5090x2:'+archive],'verified-archive-upload',timeout=300)
  code='''import pathlib,hashlib,tarfile,json,subprocess
root=pathlib.Path(REMOTE);p=root/'sdk.tar.xz';assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==EXPECTED
with tarfile.open(p,'r:xz') as f:f.extractall(root,filter='data')
libs=[p for p in root.rglob('*.so*') if p.is_file()];result={str(p):dict(sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),ldd=subprocess.run(['ldd',str(p)],capture_output=True,text=True).stdout) for p in libs};print(json.dumps(result))
'''.replace('REMOTE',repr(remote)).replace('EXPECTED',repr(r['vendor_sha256']))
  rc=rc or e.command(['ssh','nvidia-5090x2',shlex.join(['python3','-c',code])],'native-archive-hash-unpack-and-loader',timeout=240);row=dict(SDK=r['SDK'],remote=remote,status='SDK_INSTALLED' if rc==0 else 'SDK_UNAVAILABLE',return_code=rc,identity=r);write(e.path/'native-SDK.json',row);ref=e.finish('OBSERVED' if rc==0 else 'SDK_UNAVAILABLE');row['evidence']=ref;results.append(row);write(ROOT/'migration/reports/image-I0-native-private-SDKs.json',results);record('I0',r['SDK']+' SDK私有部署到5090并核对实际loader依赖，结果 '+row['status']+'。',[ref]);print(r['SDK'],rc,flush=True)
 return int(any(r['return_code'] for r in results))
if __name__=='__main__':raise SystemExit(main())
