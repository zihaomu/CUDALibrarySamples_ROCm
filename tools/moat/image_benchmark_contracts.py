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
                          stdout_starts=f'Image {w}x{h}, {iters} iterations per timing, median of 5',stderr_starts='',
                          products={'gauss.raw':w*h,'canny.raw':w*h,'resize.raw':(w//2)*(h//2),'color.raw':w*h}))
    cases += [dict(case='invalid-dimensions',arguments=['-w','15'],expected_return_code=1,products={},stdout_starts='',stderr_starts='Invalid option: need 16 <= -w/-h <= 16384 and -n >= 1'),
              dict(case='missing-input',arguments=['-i','/definitely/missing/benchmark.raw'],expected_return_code=1,products={},stdout_starts='',stderr_starts='Cannot read 2097152 bytes from /definitely/missing/benchmark.raw'),
              dict(case='unknown-option',arguments=['--unknown'],expected_return_code=1,products={},stdout_starts='Usage: ',stderr_starts='')]
    semantics=dict(
        policy_history='Expanded after independent review; earlier coarse CLI-only contracts remain sealed and all cases must be replayed.',
        gaussian=dict(project='separable [1,4,6,4,1]^2 /256, replicate border, integer round half up',
                      project_max_abs=0,project_mean_abs=0,
                      opencv='OpenCV GaussianBlur ksize5 sigma0 default REFLECT_101',
                      native='NPP 5x5 Gaussian replicate border; original emits mean absolute error but no output pixels',
                      equivalence='documented project binomial algorithm variant; no NPP pixel equivalence claim'),
        canny=dict(project='independent Sobel/L2/NMS/local threshold existing C1 contract',
                   project_max_abs=0,project_mean_abs=0,
                   opencv='OpenCV Canny thresholds60/120 aperture3 L2=true',
                   equivalence='documented edge algorithm variant; no mask inference from matching counts'),
        resize=dict(project='floor half dimensions, pixel-center bilinear, nearest rounding',
                    project_max_abs=1,project_mean_abs=0.3,opencv='OpenCV INTER_LINEAR'),
        rgb_gray=dict(project='RGB coefficients [19595,38470,7471]/65536 nearest rounding',
                      project_max_abs=1,project_mean_abs=0.3,opencv='OpenCV COLOR_RGB2GRAY'),
        printed_mean_abs_tolerance=0.0051,
        performance='raw per-device timings observed only; no cross-device speedup claim')
    profile=dict(status='FROZEN',sample_id=SAMPLE,source=str(SOURCE.relative_to(ROOT)),source_sha256=digest(SOURCE),
                 image=str(IMAGE.relative_to(ROOT)),image_sha256=digest(IMAGE),image_bytes=IMAGE.stat().st_size,
                 case_count=len(cases),cases=cases,semantic_policy=semantics)
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
