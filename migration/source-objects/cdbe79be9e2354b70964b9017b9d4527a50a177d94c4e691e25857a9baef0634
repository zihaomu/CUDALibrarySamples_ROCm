#!/usr/bin/env python3
"""Execute every frozen full Hough C++ CLI case on the actual HIP device."""
import json
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record
from image_hough_build import dependencies

PROFILE=ROOT/'migration/rewrite/image-hough-profile.json'
REPORT=ROOT/'migration/reports/image-hough-runs.json'

def main():
    profile=json.loads(PROFILE.read_text());build=json.loads((ROOT/'migration/reports/image-hough-build.json').read_text())
    if build['status']!='BUILT' or any(digest(ROOT/n)!=h for n,h in build['dependencies'].items()):
        raise ValueError('current Hough binary source required')
    rows=[]
    for case in profile['cases']:
        e=Experiment('I3','Hough-complete-C++-original-CLI','rocm-original',case=case['case'],
                     sources=[__file__,PROFILE,ROOT/'migration/reports/image-hough-build.json',*dependencies()])
        write(e.path/'backend.observed.json',capture())
        output=e.path/'outputs';output.mkdir(exist_ok=True)
        args=case['arguments'].copy()
        if '-i' in args:
            i=args.index('-i')+1;args[i]=str(ROOT/args[i])
        rc=e.command([str(ROOT/build['binary']),*args],'execute-complete-Hough-entry',cwd=output,timeout=240)
        ppm=output/'hough_result.ppm'
        line_file=output/'hough_lines.csv'
        expected=case['expected_return_code'];status='EXECUTED' if rc==expected else 'FAILED'
        row=dict(case=case['case'],status=status,return_code=rc,expected_return_code=expected,
                 arguments=args,build=build['evidence'],experiment_id=e.id,
                 ppm_sha256=digest(ppm) if ppm.exists() else None,
                 ppm_bytes=ppm.stat().st_size if ppm.exists() else None,
                 lines_sha256=digest(line_file) if line_file.exists() else None,
                 lines_bytes=line_file.stat().st_size if line_file.exists() else None)
        write(e.path/'run.json',row)
        row['evidence']=e.finish('EXECUTED' if rc==0 else 'EXPECTED_REJECTION' if rc==expected else 'COMMAND_FAILED')
        rows.append(row);write(REPORT,rows)
        record('I3','Hough真实GPU完整CLI '+case['case']+' 返回'+str(rc)+'，期望'+str(expected)+'；'+status+'。逐像素、峰值、原生差异及独立CPU验收另行核对。',[row['evidence']])
        print(case['case'],status,rc,flush=True)
    return int(any(r['status']!='EXECUTED' for r in rows))

if __name__=='__main__':raise SystemExit(main())
