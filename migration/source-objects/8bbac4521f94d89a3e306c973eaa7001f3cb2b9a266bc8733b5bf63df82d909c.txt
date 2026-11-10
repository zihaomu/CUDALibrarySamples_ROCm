#!/usr/bin/env python3
"""Reject altered full outputs and execution semantics with independent CPU oracles."""
import importlib,json,pathlib,tempfile
from catalog import ROOT
from run import digest,evidence_directory
rows=json.loads((ROOT/'migration/reports/batches9_11-rocm.json').read_text());tests=[]
def clone(origin,d):
 for p in origin.rglob('*'):
  q=d/p.relative_to(origin)
  if p.is_dir():q.mkdir(exist_ok=True)
  elif p.is_file():q.symlink_to(p.resolve())
def replace(p,data):
 p.unlink();p.write_bytes(data)
def edit_log(d,key,change):
 p=d/'run.log';lines=[];changed=False
 for line in p.read_text().splitlines():
  if line.startswith('{"observe":'):
   x=json.loads(line)
   if x['observe']==key:x['values']=change(x['values']);line=json.dumps(x,separators=(',',':'));changed=True
  lines.append(line)
 assert changed,key;replace(p,('\n'.join(lines)+'\n').encode())
def run(row,case,name,mutate,backend='rocm'):
 ref=importlib.import_module('batch'+row['batch'][1:]+'_reference');origin=evidence_directory(next(c['evidence'] for c in row['runs'] if c['case']==case))
 def verify(d):return ref.validate(row['source'],case,d,backend=backend) if row['batch']=='b9' else ref.validate(row['source'],case,d)
 assert verify(origin)['status']=='PASSED',(row['source'],case,'baseline')
 with tempfile.TemporaryDirectory(prefix='b9-b11-negative-',dir=ROOT/'build') as t:
  d=pathlib.Path(t);clone(origin,d);mutate(d)
  try:rejected=verify(d)['status']=='FAILED';reason='independent gate failed'
  except (ValueError,KeyError,IndexError,TypeError,AssertionError) as e:rejected=True;reason=type(e).__name__+': '+str(e)
  assert rejected,(row['source'],case,name)
  tests.append(dict(source=row['source'],case=case,fault=name,backend=backend,rejected=rejected,rejection=reason));print(row['source'],name,'REJECTED',flush=True)
for r in rows:
 case='variable-batch' if r['batch']=='b9' else 'roi-boundary' if r['batch']=='b10' else 'changed-values'
 for fault in ['finite','truncated-or-nan']:
  def mutate(d):
   if r['batch']=='b9':
    p=next(p for p in sorted(d.glob('gpu_decoded_*.bin')) if p.stat().st_size);data=p.read_bytes();replace(p,bytes([data[0]^127])+data[1:] if fault=='finite' else data[:-1])
   elif r['batch']=='b10':
    item=json.loads((d/'case.json').read_text())['outputs'][0];p=d/item['raw'];data=p.read_bytes();replace(p,bytes((b+100)%256 for b in data[:100])+data[100:] if fault=='finite' else data[:-1])
   elif 'reordering_phase' in r['source']:
    edit_log(d,'permutation_b0',lambda x:[x[1]]+x[1:]) if fault=='finite' else edit_log(d,'query_lu_nnz_b0',lambda x:[x[0]+1])
   else:edit_log(d,'solution_b0',lambda x:[x[0]+100 if fault=='finite' else None]+x[1:])
  run(r,case,fault,mutate)
# Lost execution semantics must also fail even when main output buffers are intact.
r=next(r for r in rows if 'low_level_quickstart' in r['source']);run(r,'corrupt-stream','invalid-stream-marked-valid',lambda d:edit_log(d,'preflight_status',lambda x:[0]*len(x)))
def damage_cross(d):
 p=d/'cross_input_stream_0.bin';data=p.read_bytes();replace(p,bytes([data[0]^1])+data[1:])
run(r,'cross-library-interop','wrong-opposite-vendor-stream',damage_cross)
r=next(r for r in rows if 'high_level_quickstart' in r['source']);run(r,'variable-batch','false-GPU-checksum',lambda d:edit_log(d,'manager_output_crc_0',lambda x:[x[0]+1]))
r=next(r for r in rows if 'nvjpegDecoder.cpp' in r['source'])
def false_pass(d):
 rec=json.loads((d/'case.json').read_text());c=next(c for c in rec['calls'] if c['expected_return_code']);p=d/c['log'];replace(p,p.read_bytes()+b'\nRESULT status=PASS\n')
run(r,'invalid-cli','false-PASS-on-error',false_pass)
def wrong_geometry(d):
 p=d/'case.json';rec=json.loads(p.read_text());rec['outputs'][0]['metadata']['width']+=1;replace(p,(json.dumps(rec)+'\n').encode())
run(r,'roi-boundary','incorrect-ROI-output-geometry',wrong_geometry)
r=next(r for r in rows if '/simple_batch/' in r['source']);run(r,'configuration','ignored-matching-config',lambda d:edit_log(d,'config_matching_get',lambda x:[1-x[0]]));run(r,'original','missing-GPU-factor-launches',lambda d:edit_log(d,'factor_launches_b0',lambda x:[0]))
r=next(r for r in rows if '/simple_uniform_batch/' in r['source']);run(r,'configuration','unselected-GPU-buffer-written',lambda d:edit_log(d,'untouched_b0',lambda x:[0]+x[1:]))
# Native CUDA's perturbed singular system must never masquerade as an original solve.
cr=next(r for r in json.loads((ROOT/'migration/reports/batches9_11-cuda.json').read_text()) if '/simple_batch/' in r['source']);run(cr,'singular-info','undeclared-singular-regularization',lambda d:edit_log(d,'cuda_native_perturbed_1x1_pivots_b0',lambda x:[0]),backend='cuda')
(ROOT/'migration/reports/batches9_11-negative.json').write_text(json.dumps(dict(status='PASSED',oracles=len(rows),output_faults=38,semantic_faults=len(tests)-38,tests=tests,generator_sha256=digest(pathlib.Path(__file__))),indent=2)+'\n')
