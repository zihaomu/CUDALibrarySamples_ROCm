#!/usr/bin/env python3
"""Native NPP C3 API counterpart, using the exact frozen pitched input bytes."""
import json,shlex,shutil,tarfile
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def main():
 profile=ROOT/'migration/rewrite/canny-color-profile.json';spec=json.loads(profile.read_text());source=ROOT/'rocm/probes/image/canny_native.cpp';e=Experiment('I1','C3-Canny-native-build','cuda-build',sources=[__file__,source,profile]);remote='/tmp/'+e.id;bundle=e.path/'inputs.tar.gz';sdk='/usr/local/cuda-13.4'
 with tarfile.open(bundle,'w:gz') as tar:
  tar.add(source,arcname='canny.cpp')
  for c in spec['cases']:tar.add(ROOT/c['fixture'],arcname='inputs/'+c['case'])
 commands=[(['ssh','nvidia-5090x2',shlex.join(['mkdir','-p',remote])],'prepare'),(['scp',str(bundle),'nvidia-5090x2:'+remote+'/inputs.tar.gz'],'upload-frozen-inputs'),(['ssh','nvidia-5090x2',shlex.join(['tar','-xzf',remote+'/inputs.tar.gz','-C',remote])],'extract'),(['ssh','nvidia-5090x2',shlex.join([sdk+'/bin/nvcc','-std=c++17','-O2','-arch=sm_120',remote+'/canny.cpp','-L'+sdk+'/lib64','-Xlinker','-rpath','-Xlinker',sdk+'/lib64','-lnppif','-lnppc','-o',remote+'/canny'])],'build-real-native-NPP-C3'),(['ssh','nvidia-5090x2',shlex.join(['sha256sum',remote+'/canny',sdk+'/lib64/libnppif.so',sdk+'/lib64/libnppc.so'])],'actual-binary-and-SDK-identities')]
 rc=0
 for cmd,phase in commands:
  rc=e.command(cmd,phase,timeout=300)
  if rc:break
 build=dict(status='BUILT' if not rc else 'FAILED',remote=remote,experiment_id=e.id,SDK=sdk)
 if not rc:
  lines=(e.path/'logs/0005-actual-binary-and-SDK-identities.stdout.log').read_text().splitlines();build.update(binary_sha256=lines[0].split()[0],libraries={line.split()[1]:line.split()[0] for line in lines[1:]})
 write(e.path/'build.json',build);build['evidence']=e.finish('EXECUTED' if not rc else 'NATIVE_BUILD_FAILED');write(ROOT/'migration/reports/canny-color-native-build.json',build)
 if rc:return rc
 rows=[]
 for case in spec['cases']:
  name=case['case'];r=Experiment('I1','C3-Canny-native-mask','cuda-run',case=name,sources=[__file__,source,profile],parent=e.id,comparison_id=case['manifest_sha256']);shutil.copytree(ROOT/case['fixture'],r.path/'inputs');output=r.path/'outputs';output.mkdir();where=remote+'/outputs/'+name
  config=dict(binary=remote+'/canny',fixture=remote+'/inputs/'+name,output=where,binary_sha256=build['binary_sha256'],manifest_sha256=case['manifest_sha256']);code='''import pathlib,hashlib,json,subprocess,os,sys
c=json.loads(__CONFIG__);binary=pathlib.Path(c['binary']);fixture=pathlib.Path(c['fixture']);output=pathlib.Path(c['output']);output.mkdir(parents=True,exist_ok=True)
assert hashlib.file_digest(binary.open('rb'),'sha256').hexdigest()==c['binary_sha256']
assert hashlib.file_digest((fixture/'manifest.json').open('rb'),'sha256').hexdigest()==c['manifest_sha256']
for n,v in json.loads((fixture/'manifest.json').read_text())['files'].items():
 p=fixture/n;assert p.stat().st_size==v['bytes'];assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==v['sha256']
print(json.dumps(dict(binary_sha256=c['binary_sha256'],input_manifest_sha256=c['manifest_sha256'])),flush=True)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='1');env.pop('IMAGE_GRADIENT_OUTPUT',None);env.pop('IMAGE_SCRATCH_FILL',None)
sys.exit(subprocess.run([str(binary),str(fixture),str(output)],env=env).returncode)
'''.replace('__CONFIG__',repr(json.dumps(config)));compile(code,'native-C3-wrapper','exec')
  rc=r.command(['ssh','nvidia-5090x2',shlex.join(['python3','-c',code])],'actual-native-C3-frozen-identities',timeout=180);copyrc=r.command(['scp','-r','nvidia-5090x2:'+where+'/.',str(output)],'collect-native-output',timeout=120);c=json.loads((r.path/'inputs/config.json').read_text());stderr=(r.path/'logs/0001-actual-native-C3-frozen-identities.stderr.log').read_text();extension=(c['width']<3 or c['height']<3) and rc==1 and 'status=-6' in stderr
  row=dict(case=name,return_code=rc,collection_return_code=copyrc,expected_size_rejection=extension,input_manifest_sha256=case['manifest_sha256'],inputs=str((r.path/'inputs').relative_to(ROOT)),outputs=str(output.relative_to(ROOT)),experiment_id=r.id,build=build,files={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in output.iterdir()});write(r.path/'run.json',row);row['evidence']=r.finish('OBSERVED' if not rc and not copyrc else 'EXPECTED_REJECTION' if extension else 'NATIVE_MISMATCH');rows.append(row);write(ROOT/'migration/reports/canny-color-native.json',rows);record('I1',name+'真实NPP C3 rc='+str(rc)+'；原始像素完整保留，按C3单独算法profile比较。',[row['evidence']]);print(name,rc,flush=True)
  if (rc or copyrc) and not extension:return 1
 return 0
if __name__=='__main__':raise SystemExit(main())
