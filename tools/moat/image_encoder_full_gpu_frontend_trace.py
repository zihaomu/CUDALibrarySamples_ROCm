#!/usr/bin/env python3
"""Trace the actual two resize C++ frontends through full GPU JPEG encoding."""
import collections,csv,json
from experiment import ROOT,Experiment,digest,write
from image_progress import record
from snapshot import capture
REPORT=ROOT/'migration/reports/image-jpeg-encoder-full-gpu-frontend-trace.json'
STAGES=('rgb_to_plane','forward_dct_quantize','gather_mcu_coefficients',
        'encode_blocks','prefix_bits','pack_bytes','prefix_stuff','scatter_stuff')
def main():
 integrations=json.loads((ROOT/'migration/reports/image-jpeg-encoder-full-gpu-integration.json').read_text())
 if len(integrations)!=2 or any(x['status']!='PASSED_SUBSET' for x in integrations):raise ValueError('both current full-GPU resize builds required')
 rows=[]
 for row in integrations:
  if any(digest(ROOT/n)!=h for n,h in row['dependencies'].items()):raise ValueError('integration source drift')
  binary=ROOT/'artifacts/rewrite/I5'/row['source'].replace('/','_')/row['experiment_id']/'sample'
  if not binary.is_file() or digest(binary)!=row['binary_sha256']:raise ValueError('integration binary drift')
  source=ROOT/'rocm/ported'/row['source'];fixture=ROOT/'tests/fixtures/batch10/444.jpg'
  e=Experiment('I5',row['source']+'/full-GPU-encode-trace','rocm-original-entry-trace',
   sources=[__file__,source,fixture,ROOT/'rocm/common/image/jpeg_decoder_v4.hpp',
    ROOT/'rocm/common/image/jpeg_full_gpu.hpp',ROOT/'rocm/common/image/jpeg_entropy_gpu.hpp'],
   parent=row['experiment_id'])
  observed=capture();write(e.path/'backend.observed.json',observed)
  plain=e.path/'plain';traced=e.path/'traced';plain.mkdir();traced.mkdir()
  args=['-i',str(fixture),'-fmt','rgbi','-rw','40','-rh','32','-q','91']
  rc0=e.command([str(binary),*args,'-o',str(plain)],'original-resize-unprofiled',timeout=300)
  rc1=e.command(['rocprofv3','--kernel-trace','--output-format','csv',
   '--output-directory',str(e.path/'trace'),'--',str(binary),*args,'-o',str(traced)],
   'original-resize-profiled',timeout=300)
  plain_jpeg=plain/'444.jpg';traced_jpeg=traced/'444.jpg'
  traces=list((e.path/'trace').rglob('*kernel_trace.csv'));agents=list((e.path/'trace').rglob('*agent_info.csv'))
  checks=[dict(check='both-original-CLI-commands-exit-zero',passed=rc0==rc1==0),
   dict(check='profiled-and-unprofiled-JPEG-byte-identical',passed=
    plain_jpeg.is_file() and traced_jpeg.is_file() and digest(plain_jpeg)==digest(traced_jpeg)),
   dict(check='single-trace-agent-map',passed=len(traces)==len(agents)==1)]
  metadata_files=list(traced.rglob('*.json'))
  meta=json.loads(metadata_files[0].read_text()) if len(metadata_files)==1 else {}
  checks.append(dict(check='actual-entry-declares-GPU-encode-and-no-CPU-entropy',passed=
   meta.get('gpu_software_encode')==1 and meta.get('gpu_full_encode')==1 and
   meta.get('cpu_entropy_encode')==0))
  counts=collections.Counter();pci=set()
  if len(traces)==len(agents)==1:
   lookup={x['Node_Id']:x for x in csv.DictReader(agents[0].open())}
   allowed={d['pci_bdf'] for d in observed['devices'] if d['physical_id']==1}
   for event in csv.DictReader(traces[0].open()):
    stage=next((x for x in STAGES if x in event['Kernel_Name']),None)
    if not stage:continue
    counts[stage]+=1;agent=lookup[event['Agent_Id'].split()[-1]];loc=int(agent['Location_Id'])
    location=f"{int(agent['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}";pci.add(location)
    checks.append(dict(check=stage+'-physical-GPU1-'+str(counts[stage]),passed=
     location in allowed and int(event['End_Timestamp'])>int(event['Start_Timestamp']) and
     int(event['Grid_Size_X'])>0,pci_bdf=location))
   checks.append(dict(check='full-twelve-JPEG-kernel-dispatches',passed=
    counts['rgb_to_plane']==counts['forward_dct_quantize']==3 and
    all(counts[x]==1 for x in STAGES[2:]),counts=dict(counts)))
  status='PASSED' if all(x['passed'] for x in checks) else 'PROFILER_FAILED'
  result=dict(source=row['source'],status=status,checks=checks,kernel_counts=dict(counts),
   pci_bdfs=sorted(pci),experiment_id=e.id)
  write(e.path/'trace-result.json',result);result['evidence']=e.finish(status,dict(status=status,checks=checks))
  rows.append(result);write(REPORT,rows)
  record('I5',row['source']+' 原始 C++ 入口重编码12个 GPU kernel/禁 CPU entropy/重放 SHA：'+status+'。',[result['evidence']])
  print(row['source'],status,dict(counts),flush=True)
 return int(any(x['status']!='PASSED' for x in rows))
if __name__=='__main__':raise SystemExit(main())
