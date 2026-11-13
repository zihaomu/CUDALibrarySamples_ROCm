#!/usr/bin/env python3
"""Freeze independent held-out encoding quality inputs before any candidate run."""
import hashlib,json
import numpy as np
from PIL import Image
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

PROFILE=ROOT/'migration/rewrite/image-encoder-quality-profile.json'

def main():
    if PROFILE.exists():raise ValueError('quality contract is immutable')
    folder=ROOT/'migration/fixtures/image-encoder-quality';folder.mkdir(parents=True,exist_ok=True)
    y,x=np.indices((259,273),dtype=np.uint32)
    gradient=np.stack([(x*255//272),(y*255//258),((x+y)*255//530)],axis=-1).astype(np.uint8)
    noise=np.random.default_rng(29371).integers(0,256,(255,257,3),dtype=np.uint8)
    y,x=np.indices((63,65));palette=np.array([[0,0,0],[255,255,255],[255,0,0],[0,255,0],[0,0,255],[255,255,0],[0,255,255],[255,0,255]],dtype=np.uint8)
    bars=palette[((x//8)+(y//9))%len(palette)]
    original=ROOT/'nvJPEG/nvJPEG-Decoder/input_images/cat.jpg'
    with Image.open(original) as im:natural=np.array(im.convert('RGB'))
    inputs=[]
    for name,rgb in [('gradient',gradient),('noise',noise),('color-edges',bars),('natural-cat',natural)]:
        path=folder/(name+'.bmp');Image.fromarray(rgb).save(path)
        inputs.append(dict(id=name,path=str(path.relative_to(ROOT)),sha256=digest(path),bytes=path.stat().st_size,
            width=rgb.shape[1],height=rgb.shape[0],rgb_sha256=hashlib.sha256(rgb.tobytes()).hexdigest()))
    cases=[dict(id=f"{image['id']}-q{q}-s{s}-opt{opt}",input=image['id'],quality=q,sampling=s,optimized=bool(opt))
           for image in inputs for q in [1,50,80,95,100] for s in [1,2] for opt in [0,1]]
    value=dict(status='FROZEN',cases=cases,inputs=inputs,
        scope='80 original-entry encoding quality cases, independent CPU libjpeg/Pillow and unmodified native CUDA GPU backend. Existing scheduling/errors/large-axis cases remain separately required.',
        gates=dict(exact_geometry_sampling_quantization=True,baseline_required=True,exact_one_product=True,
            source_channel_mse_factor=10**0.1,source_channel_mse_floor=4.0,source_tile_mse_factor=10**0.1,
            source_tile_mse_floor=4.0,tile_size=32,source_global_ssim_drop=0.02,
            optimized_vs_standard_decoded_pixels_exact=True,q100_source_mse_not_worse_than_q1=True),
        rationale='JPEG is lossy: compare reconstruction error to the SAME source, separately against each independent CPU/native encoder at identical DQT and sampling. Maximum permitted per-channel and per-32x32-tile MSE increase is 1 dB plus a 2-LSB RMS rounding floor; per-channel global SSIM drop <=0.02. Also report complete pairwise pixel errors without treating different legal bitstreams as equal. Wrong channels, missing pixels, modes, DQT and file sets are hard failures. The fixed budgets precede all candidate results; no weakening after failures.',
        measurements=['Full-image per-channel source MSE/PSNR/global SSIM for AMD/CPU/native.',
            'Every clipped 32x32 tile source MSE on all three channels; all tiles gated individually.',
            'Pairwise maxAbs, per-channel RMSE/p99 and global SSIM; byte counts and full decoded SHA.',
            'Same input/quality/sampling with optimized Huffman must decode identically to standard on each backend.'],
        references=dict(cpu='Independent Pillow/libjpeg encoder and decoder in build/image-cpu-venv; exact package versions recorded.',
            cuda='Unmodified original CMake/C++20 nvJPEGEncMultipleInstances; GPU backend on physical 5090 GPU1.',
            source_natural=str(original.relative_to(ROOT)),source_natural_sha256=digest(original)),
        performance='Not measured here. Nonprofiled repeated latency/throughput and peak memory require a separate frozen protocol.')
    e=Experiment('I5','encoder-heldout-quality-contract','CPU-contract',sources=[__file__,original,*[ROOT/i['path'] for i in inputs]])
    write(e.path/'profile.json',value);value['evidence']=e.finish('OBSERVED');write(PROFILE,value)
    record('IMG-01','冻结80项编码质量保留矩阵：4种输入×5档Q×2采样×2Huffman模式；CPU/native逐通道和每32×32局部重建MSE门槛为1dB加2LSB RMS底限，SSIM差≤.02，尺寸/模式/DQT严格一致。尚未运行，不预记通过。',[str(PROFILE.relative_to(ROOT)),value['evidence']]);print(value['evidence'])

if __name__=='__main__':main()
