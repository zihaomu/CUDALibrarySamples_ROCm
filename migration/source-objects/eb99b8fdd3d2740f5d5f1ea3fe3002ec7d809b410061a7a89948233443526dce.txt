#!/usr/bin/env python3
"""Freeze tiled JPEG prefix scan cases before GPU execution."""
from experiment import ROOT, Experiment, write
from image_progress import record

PROFILE = ROOT/'migration/rewrite/image-jpeg-prefix-profile.json'

def main():
    if PROFILE.exists():
        raise ValueError('JPEG prefix contract already frozen')
    cases=[dict(mode=mode,count=count,seed=0x5a17+count+(0 if mode=='bits' else 500000))
           for mode in ('bits','stuff') for count in (1,255,256,257,4096,65536)]
    e=Experiment('I5','parallel-JPEG-prefix-bits-and-stuff-contract','CPU-contract',sources=[__file__])
    profile=dict(status='FROZEN',cases=cases,
                 gates=dict(independent_Python_exact_positions_and_total=True,
                            tile_boundaries=True,real_physical_GPU_trace=True,
                            changed_input_replay=True,oversized_length_rejected=True),
                 limits='Correctness prototype only; original encoder still uses serial prefix until full performance and original-entry requalification.')
    write(e.path/'profile.json',profile)
    profile['evidence']=e.finish('OBSERVED',dict(status='FROZEN',checks=[dict(check='12-exact-prefix-cases',passed=True)]))
    write(PROFILE,profile)
    record('I5','并行 JPEG bits/FF-stuff prefix 原型合同冻结：1/255/256/257/4096/65536 元素×2 模式，Python 独立前缀、tile边界、GPU trace与变输入重放；暂不修改原入口。',[profile['evidence'],str(PROFILE.relative_to(ROOT))])
    print(profile['evidence'])

if __name__=='__main__':main()
