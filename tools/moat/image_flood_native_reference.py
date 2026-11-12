#!/usr/bin/env python3
"""Bind fresh native receipts/files and report full native/CPU/HIP flood differences."""
import ast,json,re,shlex
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,write,digest
from qualify_canny_plus import sealed
from image_flood_reference import model,validate as validate_gpu,exact_file
from image_flood_inputs import load_case
from image_progress import record
def receipt_code():
 tree=ast.parse((ROOT/'tools/moat/image_regions_native.py').read_text())
 values=[n.value.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str)]
 if len(values)!=1:raise ValueError('one fixed CUDA receipt and execution recipe')
 return values[0]
def validate(native):
 spec=json.loads((ROOT/'migration/rewrite/image-flood-profile.json').read_text());originals=[c for c in spec['cases'] if c['original']];d,m,_=sealed(native['evidence']);commands=json.loads((d/'commands.json').read_text());execute=next(c for c in commands if c['phase']=='actual-complete-native-default-with-source-input-library-GPU-receipt');args=shlex.split(execute['argv'][-1]);config=json.loads(args[-1]);receipt=json.loads((d/execute['stdout']).read_text().splitlines()[0]);root=ROOT/native['outputs'];source=spec['original_source'];assets={Path(c['original']['source']).name:c['original'] for c in originals};products={c['product']:3*c['width']*c['height'] for c in originals};names={'images/'+k for k in assets}|{'images/'+k for k in products};sdk=next(r for r in json.loads((ROOT/'migration/reports/image-I0-native-private-SDKs.json').read_text()) if r['SDK']=='nppplus')['identity'];checks=[]
 checks.append(dict(check='unchanged-original-source-inputs-and-actual-command-configuration',passed=native['source']==source and native['source_sha256']==spec['original_source_sha256']==digest(ROOT/source) and config==native['config'] and config['source']==Path(source).name and config['source_sha256']==receipt['source_sha256']==spec['original_source_sha256'] and config['inputs']==receipt['inputs']=={n:x['sha256'] for n,x in assets.items()}))
 checks.append(dict(check='actual-native-success-and-5090-device-binary-receipt',passed=native['status']=='EXECUTED' and native['build_return_code']==native['return_code']==native['collection_return_code']==0 and len(commands)==6 and all(c['return_code']==0 for c in commands) and receipt['physical_device_index']==1 and receipt['CUDA_VISIBLE_DEVICES']=='1' and '5090' in receipt['device'] and bool(re.fullmatch('[0-9a-f]{64}',receipt['binary_sha256']))))
 compile=shlex.split(next(c for c in commands if c['phase']=='compile-complete-unmodified-original')['argv'][-1]);checks.append(dict(check='actual-native-source-binary-and-private-SDK-build',passed=config['remote']==native['remote'] and native['remote']+'/'+Path(source).name in compile and compile[compile.index('-o')+1]==native['remote']+'/original' and '-DNPP_PLUS_ENABLE' in compile))
 phases=[c['phase'] for c in commands];remote=native['remote'];plus='/tmp/image-library-private-SDKs/nppplus-0.10.0.0/libnpp_plus-linux-x86_64-0.10.0.0_cuda12-archive'
 expected_compile=['/usr/local/cuda-13.4/bin/nvcc','-O2','-std=c++17','-arch=sm_120','-DNPP_PLUS_ENABLE','-I'+plus+'/include','-L'+plus+'/lib','-Xlinker=-rpath','-Xlinker='+plus+'/lib','-lnpp_plus_if','-lnpp_plus_c',remote+'/'+Path(source).name,'-o',remote+'/original']
 launch=shlex.split(execute['argv'][-1]);expected_phases=['prepare-private-full-original','upload-unmodified-sources-and-exact-inputs','extract-private-original','compile-complete-unmodified-original','actual-complete-native-default-with-source-input-library-GPU-receipt','collect-all-inputs-products-and-original-workflow-files']
 checks.append(dict(check='actual-native-compile-execute-recipe-binds-binary-GPU-SDK-and-collection',passed=phases==expected_phases and all(c['cwd']==str(ROOT) for c in commands) and commands[3]['argv'][:2]==['ssh','nvidia-5090x2'] and compile==expected_compile and execute['argv'][:2]==['ssh','nvidia-5090x2'] and launch==['env','CUDA_VISIBLE_DEVICES=1','python3','-c',receipt_code(),json.dumps(config,separators=(',',':'))] and commands[5]['argv']==['scp','-r','nvidia-5090x2:'+remote+'/images','nvidia-5090x2:'+remote+'/work',str(root)]))
 families=set()
 for p,v in receipt['libraries'].items():
  for family in ['if','c']:
   if Path(p).name.startswith('libnpp_plus_'+family+'.so') and '/tmp/image-library-private-SDKs/nppplus-0.10.0.0/' in p and any(v['sha256']==s['sha256'] and v['bytes']==s['bytes'] for name,s in sdk['files'].items() if name.startswith('lib/libnpp_plus_'+family+'.so')):families.add(family)
 checks.append(dict(check='both-actual-loaded-NPPplus-SDK-library-identities',passed=families=={'if','c'}))
 files_ok=set(native['files'])==names and {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}==names
 for name in names:
  p=root/name;size=assets[Path(name).name]['bytes'] if Path(name).name in assets else products[Path(name).name];v=native['files'].get(name,{})
  files_ok=files_ok and p.is_file() and p.stat().st_size==size and v.get('bytes')==size and v.get('sha256')==digest(p)
 checks.append(dict(check='all-two-inputs-five-full-RGB-products-and-exact-byte-inventory',passed=files_ok));checks.append(dict(check='native-products-bound-to-actual-collection-directory',passed=commands[-1]['argv'][-1]==str(root) and root.resolve()==(ROOT/m['raw_artifact_dir']/'outputs').resolve()));matches=re.findall(r'^BoundsRect x (\d+) y (\d+) width (\d+) height (\d+) count (\d+) seed0 (\d+) seed1 (\d+) seed2 (\d+)\.',(d/execute['stdout']).read_text(),re.M);checks.append(dict(check='five-actual-native-region-metadata-lines',passed=len(matches)==5))
 if not all(c['passed'] for c in checks):return dict(status='FAILED',checks=checks,results=[])
 gpu=json.loads((ROOT/'migration/reports/image-flood-all.json').read_text());sealed(gpu['evidence']);current=validate_gpu(gpu);checks.append(dict(check='all29-current-HIP-complete-RGB-mask-metadata-contracts',passed=len(current)==29 and all(r['status']=='PASSED' for r in current)));results=[]
 for i,c in enumerate(originals):
  w,h=c['width'],c['height'];payload=load_case(c);source=np.frombuffer(payload,np.uint8).reshape(h,c['pitch'])[:,:3*w].copy().reshape(h,w,3);input_file=root/'images'/Path(c['original']['source']).name
  if exact_file(input_file,source.nbytes,c['original']['sha256'])!=source.tobytes():raise ValueError('same complete native and HIP input')
  expected=model(source,c);vendor=np.frombuffer(exact_file(root/'images'/c['product'],source.nbytes),np.uint8).reshape(h,w,3);delta=np.abs(vendor.astype(np.int16)-expected['output'].astype(np.int16));actual_info=np.array([int(x) for x in matches[i]],'<u4');results.append(dict(case=c['case'],different_pixels=int(np.count_nonzero(np.any(delta!=0,axis=2))),different_channel_values=int(np.count_nonzero(delta)),max_abs_channel_difference=int(delta.max(initial=0)),mean_abs_channel_difference=float(delta.mean()),native_region=actual_info.tolist(),project_region=expected['region'].tolist(),region_metadata_different_values=int(np.count_nonzero(actual_info!=expected['region'])),native_original_seed_color_equals_input=bool(np.array_equal(actual_info[5:],source[c['seed'][1],c['seed'][0]])),comparison_mode='FROZEN_CLASSICAL_FIXED_SEED_8_CONNECTED_AND_DOCUMENTED_NATIVE_VARIANT'))
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',case_count=5,native_output_count=5,checks=checks,results=results,receipt=receipt,scope='Full original execution and comparison, not vendor numerical-equivalence certification. Project uses independent exact classical all-channel fixed-seed eight-connectivity and inner boundary. Native partition/boundary/metadata differences preserved, never fitted into a pixel tolerance.')
def main():
 n=next(r for r in json.loads((ROOT/'migration/reports/image-I3-native-originals.json').read_text()) if r['source']=='NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp');e=Experiment('I3','FloodFill-full-native-CPU-HIP-and-metadata-comparison','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_flood_reference.py',ROOT/'tools/moat/image_flood_inputs.py',ROOT/'migration/rewrite/image-flood-profile.json',ROOT/'migration/reports/image-I0-native-private-SDKs.json'],parent=n['experiment_id'])
 try:v=validate(n)
 except Exception as error:v=dict(status='FAILED',checks=[dict(check='native-full-command-files-SDK-device-and-comparison',passed=False,error=repr(error))],results=[])
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=v['checks']));write(ROOT/'migration/reports/image-flood-native-validation.json',v);record('I3','完整flood原生当前源码/两输入五RGB/实际库和5090收据绑定、完整CPU/HIP及metadata比较：'+v['status']+'；native分区/边界/seed信息差异明确独立记录，不拟合容差。',[v['evidence']]);print(v['status'],v.get('results'),[c for c in v['checks'] if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
