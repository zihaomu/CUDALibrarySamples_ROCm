#!/usr/bin/env python3
"""Run correctness-gated serial versus tiled JPEG GPU prefix timings."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,digest,write
from image_progress import record
from snapshot import capture

PROFILE=ROOT/'migration/rewrite/image-jpeg-prefix-bench-profile.json'
REPORT=ROOT/'migration/reports/image-jpeg-prefix-benchmark.json'
SOURCE=ROOT/'rocm/probes/image/jpeg_prefix_bench.hip'
HEADER=ROOT/'rocm/common/image/jpeg_parallel_prefix.hpp'

def main():
    profile=json.loads(PROFILE.read_text())
    if profile['status']!='FROZEN':raise ValueError('frozen benchmark profile required')
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay'
    build=Experiment('I5','serial-vs-parallel-JPEG-prefix-benchmark-build','rocm-build',
                     sources=[__file__,PROFILE,SOURCE,HEADER],parent=profile['evidence'].split('/')[-1])
    write(build.path/'backend.observed.json',capture());binary=build.path/'bench'
    rc=build.command(['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
                      '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),
                      '--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__',
                      '-I'+str(HEADER.parent),'-x','hip',str(SOURCE),'-o',str(binary),
                      '-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64'],
                     'compile-prefix-benchmark',timeout=300)
    build_ref=build.finish('EXECUTED' if rc==0 else 'BUILD_ERROR',dict(status='BUILT' if rc==0 else 'BUILD_ERROR',
       checks=[dict(check='benchmark-hipcc-build',passed=rc==0)]))
    record('I5','JPEG prefix 旧单线程与并行 tiled 性能探针构建：'+('BUILT' if rc==0 else 'BUILD_ERROR')+'。',[build_ref])
    if rc:return 1
    rows=[]
    for case in profile['cases']:
        name=case['mode']+'-'+str(case['count'])
        e=Experiment('I5','serial-vs-parallel-JPEG-prefix-event-timing','rocm-GPU-benchmark',case=name,
                     sources=[__file__,PROFILE,SOURCE,HEADER],parent=build.id)
        observed=capture();write(e.path/'backend.observed.json',observed)
        status=e.command([str(binary),case['mode'],str(case['count']),str(case['seed'])],
                         'benchmark-'+name,timeout=300)
        output=(e.path/'logs'/('0001-benchmark-'+name+'.stdout.log')).read_text()
        try:metrics=json.loads(output.splitlines()[-1]) if status==0 else {}
        except (ValueError,IndexError):metrics={}
        checks=[dict(check='GPU-serial-and-parallel-exact-host-oracle',passed=metrics.get('status')=='PASSED'),
                dict(check='frozen-case-identity',passed=metrics.get('mode')==case['mode'] and
                     metrics.get('count')==case['count'] and metrics.get('repeats')==20),
                dict(check='positive-event-timing',passed=metrics.get('serial_median_ms',0)>0 and
                     metrics.get('parallel_median_ms',0)>0),
                dict(check='physical-GPU1-binding',passed=all(d['physical_id']==1 for d in observed['devices']))]
        outcome='PASSED' if all(x['passed'] for x in checks) else 'PROFILER_FAILED'
        row=dict(case=name,status=outcome,metrics=metrics,checks=checks,experiment_id=e.id)
        write(e.path/'result.json',row)
        row['evidence']=e.finish(outcome,dict(status=outcome,checks=checks))
        rows.append(row);write(REPORT,dict(status='PASSED' if all(x['status']=='PASSED' for x in rows) else 'FAILED',
                                      build_evidence=build_ref,cases=rows))
        record('I5','JPEG prefix '+name+' GPU event对照：'+outcome+
               (f"；旧单线程{metrics['serial_median_ms']:.6g}ms，并行{metrics['parallel_median_ms']:.6g}ms。" if metrics else '。'),
               [row['evidence']])
        print(name,outcome,metrics.get('serial_median_ms'),metrics.get('parallel_median_ms'),flush=True)
    return int(any(x['status']!='PASSED' for x in rows))

if __name__=='__main__':raise SystemExit(main())
