#!/usr/bin/env python3
"""Freeze preflight workspace arithmetic and actual device capacity checks."""
from experiment import ROOT,Experiment,write
from image_completion_progress import record

def main():
    path=ROOT/'migration/rewrite/image-encoder-capacity-profile.json'
    if path.exists():raise ValueError('capacity contract already frozen')
    cases=[]
    for w,h in [(1,1),(17,19),(4097,4095),(65500,1),(1,65500),(65535,65535)]:
        for s in [1,2]:
            for opt in [False,True]:cases.append(dict(id=f'{w}x{h}-s{s}-opt{int(opt)}',width=w,height=h,sampling=s,optimized=opt,valid=True))
    for w,h,s in [(0,1,1),(1,0,2),(-1,17,1),(65536,1,2),(17,19,3)]:cases.append(dict(id=f'invalid-{w}-{h}-{s}',width=w,height=h,sampling=s,optimized=False,valid=False))
    e=Experiment('I5','JPEG-workspace-capacity-contract','CPU-contract',sources=[__file__])
    result=dict(status='FROZEN',cases=cases,
        minimum_workspace='RGB + 3 planes + 3 coefficient arrays + MCU scan/predecessors/components + block bit buffers/lengths/offsets + initial tiled scratch + quant/cosine/Huffman tables + prefix result + optional histogram/invalid flag.',
        boundaries='minimum-1/minimum/minimum+1 available bytes; reuse owned bytes without uint64 addition overflow; all dimension/mode errors reject.',
        histogram_bound='Optimized current unsigned histograms require 63 * block_count <= UINT32_MAX, otherwise explicit capacity error before image workspace allocation.',
        actual_device='Record hipMemGetInfo from allowed physical GPU1 and compare decision to independent Python minimum arithmetic. No enormous image allocation or memory-pressure experiment.',
        scope='Early lower-bound capacity rejection. Dynamic entropy buffers, concurrent allocations and driver overhead still propagate real allocation failures; not a peak-memory measurement.')
    write(e.path/'profile.json',result);result['evidence']=e.finish('OBSERVED');write(path,result)
    record('IMG-01','冻结29组工作区容量合同：24组合法几何、5组非法维度/采样，64位最小工作区、阈值上下与已拥有内存复用；查询真实GPU余量，禁止用巨大分配制造压力。',[str(path.relative_to(ROOT)),result['evidence']]);print(result['evidence'])

if __name__=='__main__':main()
