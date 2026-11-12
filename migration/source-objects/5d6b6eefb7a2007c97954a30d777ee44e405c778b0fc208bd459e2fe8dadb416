#!/usr/bin/env python3
"""Freeze five valid non-default Hough invocations and exact RAW identities."""
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_progress import record

OUT=ROOT/'migration/rewrite/image-hough-options-profile.json'
def cases():
    cross=Path('tests/fixtures/image-hough/cross.raw')
    blank=Path('tests/fixtures/image-hough/blank.raw')
    entries=[('low-vote-threshold',cross,['-t','8','-n','0']),
             ('maximum-one-line',cross,['-t','8','-m','1','-n','0']),
             ('changed-canny-thresholds',cross,['-cl','50','-ch','100','-n','0']),
             ('combined-nondefault-timed',cross,['-t','8','-m','2','-cl','50','-ch','100','-n','2']),
             ('blank-low-threshold',blank,['-t','1','-n','0'])]
    return [dict(case='raw-option-'+name,kind='valid',
                 arguments=['-i',str(path),'-w','256','-h','192',*options],
                 width=256,height=192,input=str(path),sha256=digest(ROOT/path),
                 bytes=(ROOT/path).stat().st_size,expected_return_code=0,
                 products=['hough_result.ppm','hough_lines.csv','stdout'])
            for name,path,options in entries]

def main():
    rows=cases();profile=dict(status='FROZEN',sample_id='NPP/houghLines::houghLines.cpp',
                              case_count=5,cases=rows)
    e=Experiment('I3','Hough-valid-nondefault-options-contract','CPU-contract',
                 sources=[__file__,ROOT/'migration/rewrite/image-hough-profile.json',
                          *[ROOT/'tests/fixtures/image-hough'/n for n in ['cross.raw','blank.raw']]])
    write(OUT,profile);write(e.path/'profile.json',profile)
    result=dict(status='FROZEN',case_count=5,case_ids=[r['case'] for r in rows])
    write(e.path/'contracts.json',result)
    result['evidence']=e.finish('OBSERVED')
    write(ROOT/'migration/reports/image-hough-options-contracts.json',result)
    record('I3','Hough五个有效非默认参数的输入SHA、argv及产品冻结合同：FROZEN。',[result['evidence']])
    print(result['status'],result['evidence'])

if __name__=='__main__':main()
