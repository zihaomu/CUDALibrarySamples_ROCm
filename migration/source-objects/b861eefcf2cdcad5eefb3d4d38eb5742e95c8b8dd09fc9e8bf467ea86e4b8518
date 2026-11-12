#!/usr/bin/env python3
"""Prove the complete four-operation benchmark dispatches the real HIP kernels."""
import collections,csv,json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record
from image_benchmark_build import dependencies

NAMES=['gauss5','sobel','suppress','local_threshold','resize_half','rgb_gray']
def main():
    build=json.loads((ROOT/'migration/reports/image-benchmark-build.json').read_text())
    run=next(x for x in json.loads((ROOT/'migration/reports/image-benchmark-runs.json').read_text()) if x['case']=='small')
    source=ROOT/'NPP/opencvBenchmark/images/CircuitBoard_2048x1024_8u.raw'
    e=Experiment('I3','OpenCV-benchmark-all-four-actual-GPU-kernel-traces','rocm-trace',
       sources=[__file__,source,*dependencies()],parent=build['experiment_id'])
    observed=capture();write(e.path/'backend.observed.json',observed)
    output=e.path/'outputs';output.mkdir()
    rc=e.command(['rocprofv3','--kernel-trace','--output-format','csv','--output-directory',str(e.path/'trace'),
       '--',str(ROOT/build['binary']),'-i',str(source),'-w','128','-h','96','-n','1'],
       'profile-complete-four-operation-C++-entry',cwd=output,timeout=300)
    traces=list((e.path/'trace').rglob('*kernel_trace.csv'));agents=list((e.path/'trace').rglob('*agent_info.csv'))
    checks=[dict(check='actual-process-success',passed=rc==0),
      dict(check='single-kernel-and-agent-trace',passed=len(traces)==len(agents)==1),
      dict(check='all-four-GPU-products-match-unprofiled-CLI',passed={p.name:digest(p) for p in output.iterdir() if p.is_file()}
        =={name:x['sha256'] for name,x in run['products'].items()}),
      dict(check='build-sources-current',passed=all(digest(ROOT/n)==h for n,h in build['dependencies'].items()))]
    counts=collections.Counter()
    if len(traces)==len(agents)==1:
      agent={r['Node_Id']:r for r in csv.DictReader(agents[0].open())}
      pci={d['pci_bdf'] for d in observed['devices'] if d['physical_id']==1}
      for row in csv.DictReader(traces[0].open()):
        name=row['Kernel_Name'];hits=[key for key in NAMES if key in name]
        if not hits:continue
        for key in hits:counts[key]+=1
        node=agent[row['Agent_Id'].split()[-1]];loc=int(node['Location_Id'])
        bdf=f"{int(node['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}"
        checks.append(dict(check='real-device-kernel/'+name[:75],passed=bdf in pci
          and int(row['End_Timestamp'])>int(row['Start_Timestamp']) and int(row['Grid_Size_X'])>0))
      checks.append(dict(check='all-four-operations-and-three-Canny-stages-dispatched',
        passed=all(counts[name]>=1 for name in NAMES)))
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED'
    result=dict(status=status,return_code=rc,counts=dict(counts),checks=checks,
      build_evidence=build['evidence'],reference_evidence=run['evidence'])
    write(e.path/'trace-result.json',result)
    result['evidence']=e.finish(status if status=='PASSED' else 'PROFILER_FAILED',dict(status=status,checks=checks))
    write(ROOT/'migration/reports/image-benchmark-trace.json',result)
    record('I3','benchmark四GPU算子含Canny各阶段实际rocprof内核/PCI/产品重放：'+status+'。',[result['evidence']])
    print(status,dict(counts),[(c['check'],c['passed']) for c in checks if not c['passed']]);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
