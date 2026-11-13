#!/usr/bin/env python3
"""Freeze comparable process timing and separate profiler memory measurements."""
import json
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

def main():
    dest=ROOT/'migration/rewrite/image-encoder-performance-profile.json'
    if dest.exists():raise ValueError('performance profile already frozen')
    old=ROOT/'migration/rewrite/image-encoder-quality-profile.json';fresh=ROOT/'migration/rewrite/image-encoder-math-variant-v2-profile.json';large=ROOT/'migration/rewrite/image-encoder-large-profile.json'
    a=json.loads(old.read_text());b=json.loads(fresh.read_text());big=json.loads(large.read_text())
    small=next(i for i in a['inputs'] if i['width']==64 and i['height']==64)
    natural=next(i for i in b['inputs'] if i['id']=='math-natural-img5');noise=next(i for i in b['inputs'] if i['id']=='math-noise')
    large_case=next(c for c in big['cases'] if c['width']==4097 and c['height']==4095 and c['sampling']==2)
    inputs={'small':small,'natural':natural,'noise':noise,'large':dict(generator='tools/moat/image_encoder_large.py',profile=str(large.relative_to(ROOT)),case=large_case)}
    cases=[]
    for name,key,n,s,o,mode in [('small-device-standard','small',1024,2,False,'device'),('small-download-optimized','small',512,1,True,'download'),('medium-device-standard','natural',64,2,False,'device'),('medium-download-optimized','noise',64,1,True,'download'),('medium-write-optimized','natural',16,2,True,'write'),('large-download-standard','large',4,2,False,'download')]:
        cases.append(dict(id=name,input=key,jobs=n,sampling=s,optimized=o,mode=mode,quality=80,threads=2,states=2,runs=1))
    value=dict(status='FROZEN',cases=cases,inputs=inputs,warmups=2,repetitions=7,
        timing='Separate unprofiled process per repetition, monotonic timer immediately around subprocess on each local host; includes process startup, preparation, encode, transfer/write and teardown, excludes SSH and input staging. Same frozen BMP bytes and original CLI n/j/s/r/q/p/f/d/o modes on AMD/native.',
        statistics=['all raw repetitions','min','median','max','p95','median absolute deviation','images / process wall seconds'],
        internal_metrics='Preserve vendor Throughput and Latency plus AMD preparation/measured/end-to-end fields with exact source boundaries; they are not interchangeable. Native throughput uses integer milliseconds and latency is GPU event aggregate. Do not call AMD batch wall/images a native GPU latency comparison.',
        memory='One separate profiled execution per case/side, outside timing distribution. Reconstruct live device and pinned allocations from actual allocation/free trace events with address, size, device and timestamp. Report peak traced allocation bytes and coverage limitations, separately from CPU max RSS. Never equate visible free-memory delta or workspace lower bound with peak allocation.',
        profiler='rocprofv3 allocation/copy/HIP/kernel trace on AMD; nsys CUDA memory usage and trace on native. Profiler outputs cannot supply unprofiled throughput.',
        scope='Observational performance comparison, no minimum speedup requirement. Only current independently accepted candidate/current production identity may be used for final report. All nonzero exits, absent products, nonfinite timings or missing allocation coverage remain explicit failures, not performance successes.')
    e=Experiment('I5','encoder-end-to-end-performance-contract','CPU-contract',sources=[__file__,old,fresh,large,*[ROOT/i['path'] for i in [small,natural,noise]]])
    write(e.path/'profile.json',value);value['evidence']=e.finish('OBSERVED');write(dest,value)
    record('IMG-01','冻结6场景性能合同：设备/下载/写盘、标准/优化、64像素至4097×4095；2次预热+7次无profiler进程墙钟，峰值分配另跑trace，暂未产生性能结论。',[str(dest.relative_to(ROOT)),value['evidence']]);print(value['evidence'])

if __name__=='__main__':main()
