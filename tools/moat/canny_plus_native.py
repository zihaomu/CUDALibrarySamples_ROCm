#!/usr/bin/env python3
"""Run native NPP+ on the frozen full-profile inputs, with binary/input receipts."""
import json,shlex,shutil,tarfile
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def main():
 profile=ROOT/'migration/rewrite/canny-plus-profile.json';spec=json.loads(profile.read_text());source=ROOT/'rocm/probes/image/canny_native.cpp'
 sdk=next(r for r in json.loads((ROOT/'migration/reports/image-I0-native-private-SDKs.json').read_text()) if r['SDK']=='nppplus')
 prefix=sdk['remote']+'/libnpp_plus-linux-x86_64-'+sdk['identity']['version']+'_'+sdk['identity']['variant']+'-archive'
 e=Experiment('I1',spec['sample_id'],'cuda-build',sources=[__file__,source,profile]);remote='/tmp/'+e.id
 bundle=e.path/'inputs.tar.gz'
 with tarfile.open(bundle,'w:gz') as tar:
  tar.add(source,arcname='canny.cpp')
  for case in spec['cases']:tar.add(ROOT/case['fixture'],arcname='inputs/'+case['case'])
 commands=[(['ssh','nvidia-5090x2',shlex.join(['mkdir','-p',remote])],'prepare'),(['scp',str(bundle),'nvidia-5090x2:'+remote+'/inputs.tar.gz'],'upload-frozen-inputs'),(['ssh','nvidia-5090x2',shlex.join(['tar','-xzf',remote+'/inputs.tar.gz','-C',remote])],'extract'),
 (['ssh','nvidia-5090x2',shlex.join(['/usr/local/cuda-13.4/bin/nvcc','-std=c++17','-O2','-arch=sm_120','-DIMAGE_NPP_PLUS','-I'+prefix+'/include',remote+'/canny.cpp','-L'+prefix+'/lib','-Xlinker','-rpath','-Xlinker',prefix+'/lib','-lnpp_plus_if','-lnpp_plus_c','-o',remote+'/canny'])],'build-real-NPPPlus-counterpart'),
 (['ssh','nvidia-5090x2',shlex.join(['sha256sum',remote+'/canny',prefix+'/lib/libnpp_plus_if.so',prefix+'/lib/libnpp_plus_c.so'])],'binary-and-SDK-identities')]
 rc=0
 for command,phase in commands:
  rc=e.command(command,phase,timeout=300)
  if rc:break
 build=dict(status='BUILT' if not rc else 'FAILED',remote=remote,SDK=sdk['identity'],experiment_id=e.id)
 if not rc:
  lines=(e.path/'logs/0005-binary-and-SDK-identities.stdout.log').read_text().splitlines();build['binary_sha256']=lines[0].split()[0]
  if lines[1].split()[0]!=sdk['identity']['files']['lib/libnpp_plus_if.so']['sha256']:rc=1;build['status']='SDK_MISMATCH'
 write(e.path/'build.json',build);build['evidence']=e.finish('EXECUTED' if not rc else 'NATIVE_BUILD_FAILED');write(ROOT/'migration/reports/canny-plus-native-build.json',build)
 if rc:return 1
 rows=[]
 for case in spec['cases']:
  name=case['case'];r=Experiment('I1',spec['sample_id'],'cuda-run',case=name,sources=[__file__,source,profile],parent=e.id,comparison_id=case['manifest_sha256'])
  shutil.copytree(ROOT/case['fixture'],r.path/'inputs');out=r.path/'outputs';out.mkdir();where=remote+'/outputs/'+name
  config=dict(binary=remote+'/canny',fixture=remote+'/inputs/'+name,output=where,binary_sha256=build['binary_sha256'],manifest_sha256=case['manifest_sha256'])
  code='''import pathlib,hashlib,json,subprocess,os,sys
config=json.loads(__CONFIG__)
binary=pathlib.Path(config['binary']);fixture=pathlib.Path(config['fixture']);output=pathlib.Path(config['output']);output.mkdir(parents=True,exist_ok=True)
assert hashlib.file_digest(binary.open('rb'),'sha256').hexdigest()==config['binary_sha256']
assert hashlib.file_digest((fixture/'manifest.json').open('rb'),'sha256').hexdigest()==config['manifest_sha256']
manifest=json.loads((fixture/'manifest.json').read_text())
for name,row in manifest['files'].items():
 p=fixture/name;assert p.stat().st_size==row['bytes'];assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==row['sha256']
print(json.dumps(dict(binary_sha256=config['binary_sha256'],input_manifest_sha256=config['manifest_sha256'])),flush=True)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='1');env.pop('IMAGE_GRADIENT_OUTPUT',None);env.pop('IMAGE_SCRATCH_FILL',None)
sys.exit(subprocess.run([str(binary),str(fixture),str(output)],env=env).returncode)
'''.replace('__CONFIG__',repr(json.dumps(config)))
  compile(code,'native-wrapper','exec')
  rc=r.command(['ssh','nvidia-5090x2',shlex.join(['python3','-c',code])],'actual-native-with-frozen-identities',timeout=180)
  rc_copy=r.command(['scp','-r','nvidia-5090x2:'+where+'/.',str(out)],'collect-output',timeout=120)
  error=(r.path/'logs/0001-actual-native-with-frozen-identities.stderr.log').read_text()
  rejected=rc==1 and case['native_size_extension'] and any(x in error for x in ['scratch-query status=-6','native-canny status=-6'])
  row=dict(case=name,return_code=rc,collection_return_code=rc_copy,expected_size_rejection=rejected,
           inputs=str((r.path/'inputs').relative_to(ROOT)),outputs=str(out.relative_to(ROOT)),input_manifest_sha256=case['manifest_sha256'],build=build,experiment_id=r.id,
           output_sha256={p.name:digest(p) for p in out.iterdir() if p.is_file()})
  write(r.path/'run.json',row);row['evidence']=r.finish('OBSERVED' if rc==0 and rc_copy==0 else 'EXPECTED_REJECTION' if rejected else 'NATIVE_MISMATCH');rows.append(row);write(ROOT/'migration/reports/canny-plus-native.json',rows)
  record('I1',name+' native NPP+：'+('输出已封存。' if not rc else '尺寸扩展被原生拒绝。' if rejected else '失败已封存。'),[row['evidence']]);print(name,rc,flush=True)
  if (rc or rc_copy) and not rejected:return 1
 return int(any((r['return_code'] or r['collection_return_code']) and not r['expected_size_rejection'] for r in rows))
if __name__=='__main__':raise SystemExit(main())
