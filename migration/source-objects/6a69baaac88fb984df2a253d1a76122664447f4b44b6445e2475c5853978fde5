#!/usr/bin/env python3
"""Verify real Canny and Hough kernel dispatches for the complete original entry."""
import collections,csv,json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record
from image_hough_build import dependencies

def main():
    build=json.loads((ROOT/'migration/reports/image-hough-build.json').read_text())
    original=next(r for r in json.loads((ROOT/'migration/reports/image-hough-runs.json').read_text())
                  if r['case']=='synthetic-no-timing')
    e=Experiment('I3','Hough-full-synthetic-real-GPU-Canny-votes-peaks-trace','rocm-trace',
                 sources=[__file__,ROOT/'migration/rewrite/image-hough-profile.json',*dependencies()],parent=build['experiment_id'])
    write(e.path/'backend.observed.json',capture());out=e.path/'outputs';out.mkdir(exist_ok=True)
    rc=e.command(['rocprofv3','--kernel-trace','--output-format','csv',
                  '--output-directory',str(e.path/'trace'),'--',str(ROOT/build['binary']),'-n','0'],
                 'actual-complete-Canny-Hough-GPU-kernels',cwd=out,timeout=300)
    traces=list((e.path/'trace').rglob('*kernel_trace.csv'))
    agents=list((e.path/'trace').rglob('*agent_info.csv'))
    checks=[dict(check='real-profiled-process-exit',passed=rc==0),
            dict(check='single-kernel-and-agent-trace',passed=len(traces)==len(agents)==1),
            dict(check='complete-output-unchanged',passed=(out/'hough_result.ppm').exists() and digest(out/'hough_result.ppm')==original['ppm_sha256'])]
    counter=collections.Counter()
    if len(traces)==len(agents)==1:
        lookup={r['Node_Id']:r for r in csv.DictReader(agents[0].open())}
        allowed={d['pci_bdf'] for d in json.loads((e.path/'backend.observed.json').read_text())['devices'] if d['physical_id']==1}
        for row in csv.DictReader(traces[0].open()):
            name=row['Kernel_Name']
            for key in ['cast_votes','extract_peaks','local_threshold','sobel','suppress']:
                if key in name:counter[key]+=1
            if not any(key in name for key in ['cast_votes','extract_peaks','local_threshold','sobel','suppress']):continue
            agent=lookup[row['Agent_Id'].split()[-1]];loc=int(agent['Location_Id'])
            pci=f"{int(agent['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}"
            checks.append(dict(check='actual-project-kernel/'+name[:75],passed=pci in allowed and int(row['End_Timestamp'])>int(row['Start_Timestamp']) and int(row['Grid_Size_X'])>0))
        checks.append(dict(check='both-Hough-kernels-dispatched',passed=counter['cast_votes']>=1 and counter['extract_peaks']>=1))
        checks.append(dict(check='complete-Canny-stage-dispatch',passed=all(counter[k]>=1 for k in ['sobel','suppress','local_threshold'])))
    status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED'
    result=dict(status=status,return_code=rc,checks=checks,counts=dict(counter),
                build_evidence=build['evidence'],original_evidence=original['evidence'])
    write(e.path/'trace-result.json',result)
    result['evidence']=e.finish('PASSED' if status=='PASSED' else 'PROFILER_FAILED',dict(status=status,checks=checks))
    write(ROOT/'migration/reports/image-hough-trace.json',result)
    record('I3','Hough完整默认合成原例真实GPU kernel trace：'+status+'；逐PCI/网格/时长检查Canny、180角投票与GPU峰提取。',[result['evidence']])
    print(status,dict(counter))
    return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
