#!/usr/bin/env python3
"""Freeze the original four-operation benchmark CLI and output sizes."""
from experiment import ROOT,Experiment,write,digest
from image_progress import record

SAMPLE='NPP/opencvBenchmark::opencvBenchmark.cpp'
SOURCE=ROOT/'NPP/opencvBenchmark/opencvBenchmark.cpp'
IMAGE=ROOT/'NPP/opencvBenchmark/images/CircuitBoard_2048x1024_8u.raw'

def main():
    cases=[]
    for name,w,h,iters in [('small',128,96,1),('odd-half',129,97,1),('original-default',4096,2048,20)]:
        argv=[] if name=='original-default' else ['-w',str(w),'-h',str(h),'-n',str(iters)]
        cases.append(dict(case=name,arguments=argv,width=w,height=h,iterations=iters,expected_return_code=0,
                          products={'gauss.raw':w*h,'canny.raw':w*h,'resize.raw':(w//2)*(h//2),'color.raw':w*h}))
    cases += [dict(case='invalid-dimensions',arguments=['-w','15'],expected_return_code=1,products={}),
              dict(case='missing-input',arguments=['-i','/definitely/missing/benchmark.raw'],expected_return_code=1,products={}),
              dict(case='unknown-option',arguments=['--unknown'],expected_return_code=1,products={})]
    profile=dict(status='FROZEN',sample_id=SAMPLE,source=str(SOURCE.relative_to(ROOT)),source_sha256=digest(SOURCE),
                 image=str(IMAGE.relative_to(ROOT)),image_sha256=digest(IMAGE),image_bytes=IMAGE.stat().st_size,
                 case_count=len(cases),cases=cases)
    e=Experiment('I3','OpenCV-benchmark-original-CLI-contract','CPU-contract',sources=[__file__,SOURCE,IMAGE])
    write(e.path/'profile.json',profile)
    result=dict(status='FROZEN',case_count=len(cases),case_ids=[c['case'] for c in cases])
    write(e.path/'contracts.json',result)
    result['evidence']=e.finish('OBSERVED')
    write(ROOT/'migration/rewrite/image-benchmark-profile.json',profile)
    write(ROOT/'migration/reports/image-benchmark-contracts.json',result)
    record('I3','OpenCV benchmark四算子原例冻结：默认4096×2048/20次、128×96与奇数尺寸、3个错误CLI；仅合同不增资格。',[result['evidence']])
    print('FROZEN',result['evidence'])

if __name__=='__main__':main()
