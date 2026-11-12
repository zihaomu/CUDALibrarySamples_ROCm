#!/usr/bin/env python3
"""Freeze correctness-gated GPU event timing cases for JPEG prefix scans."""
from experiment import ROOT,Experiment,write
from image_progress import record

PROFILE=ROOT/'migration/rewrite/image-jpeg-prefix-bench-profile.json'

def main():
    if PROFILE.exists():raise ValueError('prefix benchmark profile already frozen')
    cases=[dict(mode=mode,count=count,seed=0x7139+count+(0 if mode=='bits' else 200000))
           for mode in ('bits','stuff') for count in (256,65536,1048576)]
    e=Experiment('I5','parallel-vs-serial-JPEG-prefix-benchmark-contract','CPU-contract',sources=[__file__])
    p=dict(status='FROZEN',cases=cases,method='Same GPU, same input, each candidate checked against host oracle, 3 warmup + 20 timed HIP event runs; report median milliseconds; serial then parallel.',
           limits='Single physical GPU1, no end-to-end JPEG throughput claim. Small cases may favor serial; integration decision is separate.')
    write(e.path/'profile.json',p)
    p['evidence']=e.finish('OBSERVED',dict(status='FROZEN',checks=[dict(check='six-benchmark-cases-and-oracle-gate',passed=True)]))
    write(PROFILE,p)
    record('I5','JPEG prefix 并行与旧单线程性能实验先冻结：bits/stuff 各 256、65536、1048576 元素，同GPU event中位数、每候选先CPU精确验收，不把孤立速度冒充整码流吞吐。',[p['evidence'],str(PROFILE.relative_to(ROOT))])
    print(p['evidence'])

if __name__=='__main__':main()
