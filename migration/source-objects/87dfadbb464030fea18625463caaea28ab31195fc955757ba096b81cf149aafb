#!/usr/bin/env python3
"""Trace both GPU Huffman cases and reject unchanged entropy after input mutation."""
import csv,json
from experiment import ROOT,Experiment,digest,write
from image_progress import record
from snapshot import capture
PROFILE=ROOT/'migration/rewrite/image-jpeg-encoder-entropy-profile.json'
BUILD=ROOT/'migration/reports/image-jpeg-encoder-entropy-build.json'
RUNS=ROOT/'migration/reports/image-jpeg-encoder-entropy-runs.json'
REPORT=ROOT/'migration/reports/image-jpeg-encoder-entropy-trace.json'
def main():
 profile=json.loads(PROFILE.read_text());build=json.loads(BUILD.read_text());runs=json.loads(RUNS.read_text())
 enc_profile=json.loads((ROOT/'migration/rewrite/image-jpeg-encoder-gpu-profile.json').read_text())
 enc_build=json.loads((ROOT/'migration/reports/image-jpeg-encoder-build.json').read_text())
 original_rgb=next(x for x in enc_profile['inputs'] if x['case']=='odd-420')
 e=Experiment('I5','GPU-Huffman-two-real-traces-and-input-change','rocm-trace',
  sources=[__file__,PROFILE,BUILD,RUNS,ROOT/original_rgb['path'],
   ROOT/'rocm/probes/image/jpeg_huffman_gpu.hip',ROOT/'rocm/probes/image/jpeg_encoder_gpu.hip'],
  parent=build['experiment_id'])
 observed=capture();write(e.path/'backend.observed.json',observed)
 allowed={d['pci_bdf'] for d in observed['devices'] if d['physical_id']==1}
 checks=[];traces=[]
 for item in profile['inputs']:
  case=item['case'];trace=e.path/'trace'/case;gpu=e.path/(case+'.gpu.entropy');ref=e.path/(case+'.original.entropy')
  rc=e.command(['rocprofv3','--kernel-trace','--output-format','csv','--output-directory',str(trace),
   '--',str(ROOT/build['binary']),str(ROOT/item['path']),str(gpu),str(ref)],
   'profile-GPU-Huffman-'+case,timeout=300)
  prior=next(x for x in runs if x['case']==case)
  files=list(trace.rglob('*kernel_trace.csv'));agents=list(trace.rglob('*agent_info.csv'))
  valid=(rc==0 and len(files)==len(agents)==1 and gpu.is_file() and ref.is_file() and
   digest(gpu)==prior['gpu_sha256'] and digest(ref)==prior['original_sha256'])
  count=0;locations=set()
  if len(files)==len(agents)==1:
   lookup={r['Node_Id']:r for r in csv.DictReader(agents[0].open())}
   for row in csv.DictReader(files[0].open()):
    if 'encode_blocks' not in row['Kernel_Name']:continue
    count+=1;agent=lookup[row['Agent_Id'].split()[-1]];loc=int(agent['Location_Id'])
    pci=f"{int(agent['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}";locations.add(pci)
    valid=valid and pci in allowed and int(row['End_Timestamp'])>int(row['Start_Timestamp']) and int(row['Grid_Size_X'])>0
  checks.append(dict(check='real-physical-GPU1-Huffman-'+case,passed=valid and count==1,
   kernel_count=count,pci_bdfs=sorted(locations),traced_sha256=digest(gpu) if gpu.is_file() else None))
  traces.append(dict(case=case,return_code=rc,kernel_count=count,pci_bdfs=sorted(locations)))
 changed=e.path/'changed.rgb';rgb=bytearray((ROOT/original_rgb['path']).read_bytes())
 for y in range(8):
  for x in range(8):rgb[(y*original_rgb['width']+x)*3:(y*original_rgb['width']+x)*3+3]=bytes((255,0,255))
 changed.write_bytes(rgb);jpeg=e.path/'changed.jpg'
 encode_rc=e.command([str(ROOT/enc_build['binary']),str(changed),str(original_rgb['width']),
  str(original_rgb['height']),str(original_rgb['quality']),original_rgb['subsampling'],str(jpeg)],
  'encode-deterministically-mutated-RGB',timeout=300)
 altered_gpu=e.path/'changed.gpu.entropy';altered_ref=e.path/'changed.original.entropy'
 huffman_rc=e.command([str(ROOT/build['binary']),str(jpeg),str(altered_gpu),str(altered_ref)],
  'GPU-Huffman-mutated-image',timeout=300) if encode_rc==0 else -1
 original=next(x for x in runs if x['case']=='odd-420')
 checks.append(dict(check='changed-RGB-makes-valid-different-GPU-entropy',passed=
  digest(changed)!=digest(ROOT/original_rgb['path']) and encode_rc==huffman_rc==0 and
  altered_gpu.is_file() and altered_ref.is_file() and
  digest(altered_gpu)==digest(altered_ref) and digest(altered_gpu)!=original['gpu_sha256'],
  changed_rgb_sha256=digest(changed),changed_gpu_entropy_sha256=digest(altered_gpu) if altered_gpu.is_file() else None))
 status='PASSED' if all(x['passed'] for x in checks) else 'PROFILER_FAILED'
 result=dict(status=status,checks=checks,traces=traces,mutation_encode_return_code=encode_rc,
  mutation_huffman_return_code=huffman_rc,experiment_id=e.id)
 write(e.path/'trace-result.json',result)
 result['evidence']=e.finish(status,dict(status=status,checks=checks));write(REPORT,result)
 record('I5','GPU Huffman odd-420/odd-444 两条真实物理 GPU1 trace 各1内核及改输入重放：'+status+'。',[result['evidence']]);print(status,traces);return int(status!='PASSED')
if __name__=='__main__':raise SystemExit(main())
