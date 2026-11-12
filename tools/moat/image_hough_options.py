#!/usr/bin/env python3
"""Run valid non-default Hough options and independently verify every line/PPM."""
import json
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record
from image_hough_reference import validate

CASE_PATH=ROOT/'tests/fixtures/image-hough/cross.raw'
BLANK=ROOT/'tests/fixtures/image-hough/blank.raw'
CASES=[
    ('low-vote-threshold',CASE_PATH,['-t','8','-n','0']),
    ('maximum-one-line',CASE_PATH,['-t','8','-m','1','-n','0']),
    ('changed-canny-thresholds',CASE_PATH,['-cl','50','-ch','100','-n','0']),
    ('combined-nondefault-timed',CASE_PATH,['-t','8','-m','2','-cl','50','-ch','100','-n','2']),
    ('blank-low-threshold',BLANK,['-t','1','-n','0']),
]

def main():
    build=json.loads((ROOT/'migration/reports/image-hough-build.json').read_text())
    if build['status']!='BUILT' or any(digest(ROOT/n)!=h for n,h in build['dependencies'].items()):
        raise ValueError('current Hough binary required')
    rows=[]
    for name,path,options in CASES:
        case=dict(case='raw-option-'+name,kind='valid',arguments=['-i',str(path.relative_to(ROOT)),
                  '-w','256','-h','192',*options],width=256,height=192,
                  input=str(path.relative_to(ROOT)),sha256=digest(path),bytes=path.stat().st_size,
                  expected_return_code=0,products=['hough_result.ppm','stdout'])
        e=Experiment('I3','Hough-valid-nondefault-original-options','rocm-original',case=case['case'],
                     sources=[__file__,ROOT/'tools/moat/image_hough_reference.py',path,
                              ROOT/'migration/rewrite/image-hough-profile.json'])
        write(e.path/'backend.observed.json',capture());out=e.path/'outputs';out.mkdir(exist_ok=True)
        args=case['arguments'].copy();args[1]=str(path)
        rc=e.command([str(ROOT/build['binary']),*args],'execute-valid-nondefault-options',cwd=out,timeout=180)
        ppm=out/'hough_result.ppm'
        line_file=out/'hough_lines.csv'
        row=dict(case=case['case'],status='EXECUTED' if rc==0 else 'FAILED',return_code=rc,
                 expected_return_code=0,arguments=args,build=build['evidence'],experiment_id=e.id,
                 ppm_sha256=digest(ppm) if ppm.exists() else None,
                 ppm_bytes=ppm.stat().st_size if ppm.exists() else None,
                 lines_sha256=digest(line_file) if line_file.exists() else None,
                 lines_bytes=line_file.stat().st_size if line_file.exists() else None)
        write(e.path/'run.json',row)
        row['evidence']=e.finish('EXECUTED' if rc==0 else 'COMMAND_FAILED')
        v=validate(case,row)
        cpu=Experiment('I3','Hough-valid-options-independent-CPU','CPU-reference',case=case['case'],
                       parent=e.id,sources=[__file__,ROOT/'tools/moat/image_hough_reference.py',path])
        write(cpu.path/'validation.json',v)
        v['evidence']=cpu.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',
                                dict(status=v['status'],checks=v['checks']))
        rows.append(dict(case=case,run=row,validation=v))
        write(ROOT/'migration/reports/image-hough-options.json',rows)
        record('I3','Hough有效非默认参数 '+name+'，完整线列表和PPM独立CPU：'+v['status']+'。',[row['evidence'],v['evidence']])
        print(name,v['status'],[c['check'] for c in v['checks'] if not c['passed']],flush=True)
    return int(any(r['validation']['status']!='PASSED' for r in rows))

if __name__=='__main__':raise SystemExit(main())
