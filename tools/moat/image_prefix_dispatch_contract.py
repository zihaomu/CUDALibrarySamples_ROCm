#!/usr/bin/env python3
"""Freeze checked-prefix crossover measurement and guard inputs."""
from experiment import ROOT,Experiment,write
from image_completion_progress import record

def main():
    path=ROOT/'migration/rewrite/image-prefix-dispatch-profile.json'
    if path.exists():raise ValueError('dispatch contract already frozen')
    cases=[]
    for mode in ['bits','stuff']:
        for count in [1,8,16,32,64,128,192,256,384,512,1024,4096,65536,1048576]:
            cases.append(dict(id=f'{mode}-{count}',mode=mode,count=count,seed=19337,pattern='mixed',timed=True))
    for name,mode,count,pattern in [('zero-bit-length','bits',257,'zero'),('excess-bit-length','bits',257,'excess'),
        ('total-bit-overflow','bits',1048576,'maximum'),('stuff-all-ff','stuff',65536,'maximum'),('stuff-no-ff','stuff',65536,'zero')]:
        cases.append(dict(id=name,mode=mode,count=count,seed=19337,pattern=pattern,timed=False))
    e=Experiment('I5','checked-prefix-dispatch-contract','CPU-contract',sources=[__file__])
    profile=dict(status='FROZEN',cases=cases,warmup_pairs=3,measured_pairs=20,
        execution_order='Alternate serial-first and tiled-first within pairs; individual HIP-event intervals include the complete launch path.',
        selection='For each mode separately, choose the largest tested count in the contiguous ascending prefix where serial median <= 0.95 * tiled median. If count1 fails, threshold0. Larger inputs retain checked tiled path.',
        validation='CPU uint64 cumulative reference, every valid offset and total exact; invalid-length/overflow flags checked. No timing until C++ host reference check passes; Python repeats independent checks.',
        holdout='After threshold selection, freeze threshold-1/threshold/threshold+1 for both modes with mixed/all-maximum/all-zero distributions, using valid1-bit values for zero-like bits. Do not retune using these holdouts.',
        scope='Standalone checked prefix calls, not full JPEG throughput. Existing unchecked timings are historical and cannot set production thresholds.')
    write(e.path/'profile.json',profile);profile['evidence']=e.finish('OBSERVED');write(path,profile)
    record('IMG-01','冻结checked prefix分派测量：28个大小/模式、5个边界合同，3对预热+20对交替GPU event测量，按两模式各自连续满足5%优势确定阈值；保留边界集不得再调参。',[str(path.relative_to(ROOT)),profile['evidence']]);print(profile['evidence'])

if __name__=='__main__':main()
