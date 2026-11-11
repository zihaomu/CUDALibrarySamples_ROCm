#!/usr/bin/env python3
"""Bind unchanged native receipts/files and recompute complete CPU/HIP/vendor differences."""
import json,re,shlex
import numpy as np
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_distance_model import model
from image_distance_original_reference import validate_one,values
from image_progress import record

def validate(native):
 spec=json.loads((ROOT/'migration/rewrite/image-distance-original-contract.json').read_text());profile=json.loads((ROOT/'migration/rewrite/image-distance-profile.json').read_text());inputs=spec['datasets']['original'];root=ROOT/native['outputs'];meta=json.loads((ROOT/native['evidence']/'manifest.json').read_text());raw=ROOT/meta['raw_artifact_dir'];commands=json.loads((raw/'commands.json').read_text());execute=next(c for c in commands if c['phase']=='actual-vendor-five-input-twelve-output-workflow-with-receipts');receipt=json.loads((raw/execute['stdout']).read_text().splitlines()[0]);assets=ROOT/'NPP+/distanceTransform/images';asset_hashes={p.name:digest(p) for p in assets.glob('*.raw')};products={}
 for c in inputs:
  n=c['width']*c['height'];products[c['output_prefix']+'_64f.raw']=8*n;products[c['output_prefix']+'_16u.raw']=2*n
 products[spec['signed_lith_indices']]=4*554*554;products[spec['signed_lith_relative']]=4*554*554;expected={**{n:(assets/n).stat().st_size for n in asset_hashes},**products};checks=[]
 checks.append(dict(check='native-original-source-and-all-seven-input-identities',passed=native['original_source']==profile['original_source'] and native['original_source_sha256']==profile['original_source_sha256']==digest(ROOT/profile['original_source']) and native['config']['inputs']==receipt['inputs']==asset_hashes and receipt['source_sha256']==profile['original_source_sha256']))
 checks.append(dict(check='actual-native-successful-build-run-and-receipt',passed=native['status']=='EXECUTED' and native['return_code']==native['collection_return_code']==0 and len(commands)==6 and all(c['return_code']==0 for c in commands) and bool(re.fullmatch('[0-9a-f]{64}',receipt['binary_sha256']))))
 compile=next(c for c in commands if c['phase']=='compile-unmodified-vendor-original');args=shlex.split(compile['argv'][-1]);prefix=native['config']['prefix'];checks.append(dict(check='actual-source-binary-SDK-and-GPU-binding',passed=native['remote']+'/source.cpp' in args and args[args.index('-o')+1]==native['remote']+'/distance' and '-DNPP_PLUS_ENABLE' in args and '-I'+prefix+'/include' in args and '-L'+prefix+'/lib' in args and receipt['physical_device_index']==1 and receipt['CUDA_VISIBLE_DEVICES']=='1' and '5090' in receipt['device']))
 libraries=receipt['libraries'];sdk=native['SDK']['files'];matched=set()
 for path,v in libraries.items():
  for family in ['if','c']:
   if Path(path).name.startswith('libnpp_plus_'+family+'.so') and path.startswith(prefix+'/lib/') and any(v['sha256']==info['sha256'] and v['bytes']==info['bytes'] for name,info in sdk.items() if name.startswith('lib/libnpp_plus_'+family+'.so')):matched.add(family)
 checks.append(dict(check='both-actual-loaded-NPPplus-libraries-match-private-SDK',passed=matched=={'if','c'}))
 files_ok=set(native['files'])==set(expected) and {p.name for p in root.iterdir()}==set(expected)
 for name,size in expected.items():
  p=root/name;row=native['files'].get(name,{});files_ok=files_ok and p.is_file() and p.stat().st_size==size and row.get('bytes')==size and row.get('sha256')==digest(p)
 checks.append(dict(check='all-nineteen-input-and-original-output-files-complete',passed=files_ok))
 checks.append(dict(check='native-collection-path-is-actual-command-target',passed=commands[-1]['argv'][-1]==str(root)))
 if not all(c['passed'] for c in checks):return dict(status='FAILED',case_count=0,checks=checks,results=[])
 rocm=next(r for r in json.loads((ROOT/'migration/reports/image-distance-originals.json').read_text()) if r['case']=='explicit-original');rule=next(r for r in spec['workflows'] if r['case']=='explicit-original');actual=validate_one(rocm,rule);checks.append(dict(check='actual-current-HIP-complete-original-files-and-site-audit',passed=actual['status']=='PASSED'));results=[]
 for c in inputs:
  w,h=c['width'],c['height'];source=np.frombuffer((root/c['filename']).read_bytes(),c['dtype']).reshape(h,w)
  if digest(root/c['filename'])!=c['sha256']:raise ValueError('same original native/CPU/HIP input bytes')
  expected=model(source,c['mode'],c['cutoff'],c['remap_circle']);distance=root/(c['output_prefix']+'_64f.raw');vendor=np.fromfile(distance,'<f8').reshape(h,w);target=expected['distance'];hip=ROOT/rocm['outputs']/distance.name;checks.append(dict(check=c['case']+'/HIP-distance-and-visualization-on-same-frozen-input',passed=values(hip,target,True) and values(ROOT/rocm['outputs']/(c['output_prefix']+'_16u.raw'),expected['visualization'])));both=np.isfinite(vendor)&np.isfinite(target);delta=np.abs(vendor[both]-target[both]);budget=2e-11+1e-12*np.abs(target[both]);neighbors=[]
  for axis in [0,1]:
   a=vendor[1:,:] if axis==0 else vendor[:,1:];b=vendor[:-1,:] if axis==0 else vendor[:,:-1];okay=np.isfinite(a)&np.isfinite(b);d=np.abs(a[okay]-b[okay]);neighbors.append(dict(axis=axis,max_adjacent_difference=float(d.max(initial=0)),above_classical_one_Lipschitz=int(np.count_nonzero(d>1+1e-9))))
  result=dict(case=c['case'],comparison_mode='EXACT_UNSIGNED_OR_DOCUMENTED_SIGNED_ALGORITHM_VARIANT',native_nonfinite=int(np.count_nonzero(~np.isfinite(vendor))),max_abs_difference=float(delta.max(initial=0)),mean_abs_difference=float(delta.mean()) if len(delta) else None,p99_abs_difference=float(np.quantile(delta,.99)) if len(delta) else None,outside_project_CPU_budget=int(np.count_nonzero(delta>budget)),sign_disagreement=int(np.count_nonzero(np.signbit(vendor)!=np.signbit(target))),zero_set_disagreement=int(np.count_nonzero((vendor==0)!=(target==0))),native_adjacent_distance_observations=neighbors,visualization_different_values=int(np.count_nonzero(np.fromfile(root/(c['output_prefix']+'_16u.raw'),'<u2').reshape(h,w)!=expected['visualization'])))
  if c['input_type']==1:result['Voronoi_differences']={key:int(np.count_nonzero(np.fromfile(root/name,'<i2').reshape(h,w,2)!=expected[key])) for key,name in [('indices',spec['signed_lith_indices']),('relative',spec['signed_lith_relative'])]}
  results.append(result)
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',case_count=5,native_output_count=12,checks=checks,results=results,receipt=receipt,scope='Native execution and full comparisons completed. Signed algorithms/Voronoi conventions differ; numerical differences are observed, not fitted acceptance thresholds or vendor-correctness claims.')

def main():
 native=json.loads((ROOT/'migration/reports/image-distance-native.json').read_text());e=Experiment('I2','Distance-complete-native-CPU-HIP-comparison','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_distance_model.py',ROOT/'tools/moat/image_distance_original_reference.py',ROOT/'tools/moat/image_distance_reference.py',ROOT/'tools/moat/image_distance_inputs.py',ROOT/'migration/rewrite/image-distance-profile.json',ROOT/'migration/rewrite/image-distance-original-contract.json'],parent=native['experiment_id'])
 try:v=validate(native)
 except Exception as error:v=dict(status='FAILED',checks=[dict(check='complete-unchanged-vendor-baseline-and-full-comparison',passed=False,error=repr(error))],results=[])
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=v['checks']));write(ROOT/'migration/reports/image-distance-native-validation.json',v);record('I2','EDT原生未改源码/7输入12输出、binary/实际SDK库/GPU receipt绑定及CPU/HIP/native完整比较：'+v['status']+'；signed算法差异和Voronoi规则差异独立记录，不拟合容差。',[v['evidence']]);print(v['status'],[c for c in v['checks'] if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
