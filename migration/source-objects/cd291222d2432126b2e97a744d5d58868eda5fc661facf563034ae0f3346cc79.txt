#!/usr/bin/env python3
"""Verify concurrent HIP stream IDs and input-change replay for the JPEG encoder."""
import csv,json,shutil
from pathlib import Path
from experiment import ROOT,Experiment,digest,write
from image_progress import record
from snapshot import capture

PROFILE=ROOT/'migration/rewrite/image-jpeg-encoder-instances-profile.json'
BUILD=ROOT/'migration/reports/image-jpeg-encoder-instances-build.json'
RUNS=ROOT/'migration/reports/image-jpeg-encoder-instances-runs.json'
REPORT=ROOT/'migration/reports/image-jpeg-encoder-instances-trace.json'
def main():
 profile=json.loads(PROFILE.read_text());build=json.loads(BUILD.read_text());runs=json.loads(RUNS.read_text())
 original=next(x for x in runs if x['case']=='repeat-seven')
 src=ROOT/profile['inputs'][0]['path'];folder=src.parent
 e=Experiment('I5','original-JPEG-encoder-concurrent-HIP-streams-and-changed-input','rocm-trace',
  sources=[__file__,PROFILE,BUILD,*[ROOT/x['path'] for x in profile['inputs']],
   ROOT/'rocm/common/image/jpeg_encoder_instances.hpp',ROOT/'rocm/common/image/jpeg_encoder_gpu.hpp',
   ROOT/'rocm/common/image/jpeg_full_gpu.hpp',ROOT/'rocm/common/image/jpeg_entropy_gpu.hpp'],
  parent=original['experiment_id'])
 observed=capture();write(e.path/'backend.observed.json',observed)
 output=e.path/'outputs';output.mkdir()
 cmd=['rocprofv3','--kernel-trace','--output-format','csv','--output-directory',str(e.path/'trace'),
  '--',str(ROOT/build['binary']),'-i',str(folder),'-n','7','-j','2','-s','4',
  '-o',str(output),'-b','gpu','-q','75']
 rc=e.command(cmd,'concurrent-real-GPU-JPEG-encode',timeout=300)
 stdout=(e.path/'logs/0001-concurrent-real-GPU-JPEG-encode.stdout.log').read_text()
 traces=list((e.path/'trace').rglob('*kernel_trace.csv'));agents=list((e.path/'trace').rglob('*agent_info.csv'))
 checks=[dict(check='profiler-command-exit-zero',passed=rc==0),
  dict(check='baseline-full-GPU-entropy-reported',passed='cpu_entropy=0 gpu_full_encode=1' in stdout),
  dict(check='one-GPU-kernel-trace-and-agent-map',passed=len(traces)==len(agents)==1),
  dict(check='seven-traced-products-match-nonprofiled',passed=all(
   (output/(str(i)+'.jpg')).is_file() and digest(output/(str(i)+'.jpg'))==
   next(p['sha256'] for p in original['products'] if p['product']==str(i)+'.jpg') for i in range(7)))]
 stage_counts={};streams=set();pci=set()
 if len(traces)==len(agents)==1:
  lookup={r['Node_Id']:r for r in csv.DictReader(agents[0].open())}
  allowed={d['pci_bdf'] for d in observed['devices'] if d['physical_id']==1}
  for row in csv.DictReader(traces[0].open()):
   stage=next((x for x in ('rgb_to_plane','forward_dct_quantize','gather_mcu_coefficients',
      'encode_blocks','prefix_bits','pack_bytes','prefix_stuff','scatter_stuff')
      if x in row['Kernel_Name']),None)
   if not stage:continue
   stage_counts[stage]=stage_counts.get(stage,0)+1;streams.add(row['Stream_Id'])
   agent=lookup[row['Agent_Id'].split()[-1]];loc=int(agent['Location_Id'])
   location=f"{int(agent['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}"
   pci.add(location)
   checks.append(dict(check=stage+'-actual-physical-GPU1-'+str(stage_counts[stage]),
    passed=location in allowed and int(row['End_Timestamp'])>int(row['Start_Timestamp'])
    and int(row['Grid_Size_X'])>0,pci_bdf=location,stream_id=row['Stream_Id']))
  expected={'rgb_to_plane':21,'forward_dct_quantize':21,**{x:7 for x in
      ('gather_mcu_coefficients','encode_blocks','prefix_bits','pack_bytes',
       'prefix_stuff','scatter_stuff')}}
  checks.append(dict(check='all-seven-images-full-12-kernel-JPEG-encode',
   passed=stage_counts==expected,counts=stage_counts,expected=expected))
  checks.append(dict(check='at-least-two-actual-HIP-streams',passed=len(streams)>=2,
   stream_ids=sorted(streams)))
 changed=e.path/'changed-input';shutil.copytree(folder,changed)
 name=Path(profile['inputs'][0]['path']).name;altered=changed/name
 payload=bytearray(altered.read_bytes());payload[54]^=0xff;altered.write_bytes(payload)
 changed_output=e.path/'changed-output';changed_output.mkdir()
 mutation_rc=e.command([str(ROOT/build['binary']),'-i',str(changed),'-n','3','-j','2',
  '-s','2','-o',str(changed_output),'-b','gpu','-q','75'],
  'changed-input-replay',timeout=300)
 checks.append(dict(check='changed-input-run-succeeds',passed=mutation_rc==0))
 checks.append(dict(check='mutated-BMP-hash-differs',passed=digest(altered)!=digest(src),
                    original_sha256=digest(src),changed_sha256=digest(altered)))
 checks.append(dict(check='changed-source-changes-JPEG-while-others-stable',passed=
  all((changed_output/(str(i)+'.jpg')).is_file() for i in range(3)) and
  digest(changed_output/'0.jpg')!=digest(output/'0.jpg') and
  all(digest(changed_output/(str(i)+'.jpg'))==digest(output/(str(i)+'.jpg')) for i in (1,2))))
 status='PASSED' if all(x['passed'] for x in checks) else 'PROFILER_FAILED'
 result=dict(status=status,checks=checks,return_code=rc,mutation_return_code=mutation_rc,
  kernel_counts=stage_counts,stream_ids=sorted(streams),pci_bdfs=sorted(pci),experiment_id=e.id)
 write(e.path/'trace-result.json',result)
 result['evidence']=e.finish(status,dict(status=status,checks=checks));write(REPORT,result)
 record('I5','原始多实例 JPEG 编码器 7 图/84 kernel、多 HIP stream、物理 GPU1、改输入重放：'+status+'。',
  [result['evidence']]);print(status,stage_counts,sorted(streams));return int(status!='PASSED')
if __name__=='__main__':raise SystemExit(main())
