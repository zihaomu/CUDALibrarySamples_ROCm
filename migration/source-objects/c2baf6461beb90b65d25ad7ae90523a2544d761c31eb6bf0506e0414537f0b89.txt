#!/usr/bin/env python3
"""Independent oracles must reject all output and execution-semantics corruptions."""
import importlib,json,pathlib,tempfile
from catalog import ROOT
from run import digest,evidence_directory
from batches12_15_spec import kind
from validate_blas import np
rows=json.loads((ROOT/'migration/reports/batches12_15-rocm.json').read_text());tests=[]
def write(p,data):p.unlink();p.write_bytes(data)
def binary(d,name,dtype,change):
 p=d/name;a=np.fromfile(p,dtype);change(a);write(p,a.tobytes())
def metadata(d,name,change):
 p=d/name;x=json.loads(p.read_text());change(x);write(p,(json.dumps(x,indent=2)+'\n').encode())
def run(r,label,mutate,case='irregular'):
 ref=importlib.import_module('batch'+r['batch'][1:]+'_reference');original=evidence_directory(next(c['evidence'] for c in r['runs'] if c['case']==case));assert ref.validate(r['source'],case,original)['status']=='PASSED',(r['source'],'baseline')
 with tempfile.TemporaryDirectory(prefix='b12-b15-negative-',dir=ROOT/'build') as tmp:
  d=pathlib.Path(tmp)
  for p in original.rglob('*'):
   q=d/p.relative_to(original)
   if p.is_dir():q.mkdir(exist_ok=True)
   elif p.is_file():q.symlink_to(p.resolve())
  mutate(d)
  try:rejected=ref.validate(r['source'],case,d)['status']=='FAILED';reason='independent gate rejected'
  except (ValueError,TypeError,IndexError,KeyError,AssertionError) as e:rejected=True;reason=type(e).__name__+': '+str(e)
  assert rejected,(r['source'],label);tests.append(dict(source=r['source'],case=case,fault=label,rejected=True,reason=reason));print(r['source'],label,'REJECTED',flush=True)
for r in rows:
 k=kind(r['source'])
 for fault in ['finite','nan-or-truncation']:
  def mutate(d):
   if r['batch']=='b12':name='r0_output.bin';dtype=np.float64 if k=='geadd' else np.float32
   elif r['batch']=='b13':name='r0_frequency_y_slab.bin' if k=='mp_fft' else 'r0_output.bin' if k=='mg_tensor' else 'r0_solution.bin';dtype=np.complex64 if k=='mp_fft' else np.float32 if k=='mg_tensor' else np.float64
   elif r['batch']=='b14':name='output.bin';dtype=np.complex64 if k=='simple_fft_block' else np.complex128 if k=='potrf_block' else np.float64
   else:
    name='i0_mask.bin' if k in ['flood','canny'] else 'i0_output.bin';dtype=np.uint8 if k in ['flood','canny'] else np.float32
    if dtype==np.uint8:
     p=d/name;data=p.read_bytes();write(p,bytes([data[0]^1])+data[1:] if fault=='finite' else data[:-1]);return
   binary(d,name,dtype,lambda x:x.__setitem__(0,x[0]+100 if fault=='finite' else np.nan))
  run(r,fault,mutate)
r=next(r for r in rows if kind(r['source'])=='geadd');run(r,'same-PCI-on-both-ranks',lambda d:metadata(d,'rank1.json',lambda x:x.__setitem__('pci',json.loads((d/'rank0.json').read_text())['pci'])));run(r,'same-PID-on-MPI-ranks',lambda d:metadata(d,'rank1.json',lambda x:x.__setitem__('pid',json.loads((d/'rank0.json').read_text())['pid'])))
r=next(r for r in rows if kind(r['source'])=='matmul_ag');run(r,'missing-AllGather',lambda d:metadata(d,'rank0.json',lambda x:x.__setitem__('allgather',0)))
r=next(r for r in rows if kind(r['source'])=='mp_fft');run(r,'missing-FFT-transpose-SendRecv',lambda d:binary(d,'r0_config.bin',np.int32,lambda x:x.__setitem__(9,0)))
r=next(r for r in rows if kind(r['source'])=='mg_lu');run(r,'wrong-Mg-process-model',lambda d:metadata(d,'rank1.json',lambda x:x.__setitem__('pid',json.loads((d/'rank0.json').read_text())['pid']+1)));run(r,'no-local-factor-columns-executed',lambda d:binary(d,'r0_config.bin',np.int32,lambda x:x.__setitem__(5,0)))
r=next(r for r in rows if kind(r['source'])=='potrf_block');run(r,'shared-padding-overwritten',lambda d:binary(d,'trace.bin',np.int32,lambda x:x.__setitem__(5,0)))
r=next(r for r in rows if kind(r['source'])=='philox_thread_api');run(r,'wrong-Philox-counter-word',lambda d:binary(d,'raw.bin',np.uint32,lambda x:x.__setitem__(0,x[0]^1)))
r=next(r for r in rows if kind(r['source'])=='simple_fft_block');run(r,'wrong-cooperative-block-width',lambda d:binary(d,'trace.bin',np.int32,lambda x:x.__setitem__(3,0)))
r=next(r for r in rows if kind(r['source'])=='canny');run(r,'output-stride-padding-overwritten',lambda d:binary(d,'i0_output.bin',np.uint8,lambda x:x.__setitem__(-1,0)))
r=next(r for r in rows if kind(r['source'])=='distance');run(r,'wrong-Voronoi-displacement',lambda d:binary(d,'i0_voronoi.bin',np.int16,lambda x:x.__setitem__(0,x[0]+7)))
r=next(r for r in rows if kind(r['source'])=='ncc');run(r,'invalid-GPU-argmax-index',lambda d:binary(d,'i0_best.bin',np.int32,lambda x:x.__setitem__(0,-1)))
r=next(r for r in rows if kind(r['source'])=='canny');run(r,'empty-work-must-not-qualify',lambda d:write(d/'trace.bin',b''))
(ROOT/'migration/reports/batches12_15-negative.json').write_text(json.dumps(dict(status='PASSED',oracles=len(rows),output_faults=40,semantic_faults=len(tests)-40,tests=tests,generator_sha256=digest(pathlib.Path(__file__))),indent=2)+'\n')
