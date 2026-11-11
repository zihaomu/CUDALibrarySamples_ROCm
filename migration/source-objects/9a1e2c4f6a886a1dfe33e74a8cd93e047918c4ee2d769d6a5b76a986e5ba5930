#!/usr/bin/env python3
"""Describe original JPEG scans and measure complete CPU/GPU pixels without promotion."""
import json,math
import numpy as np
from PIL import Image,features
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def jpeg_markers(data):
    if data[:2]!=b'\xff\xd8':raise ValueError('missing SOI')
    pos=2;sof=[];scans=0
    while pos<len(data):
        if data[pos]!=255:pos+=1;continue
        while pos<len(data) and data[pos]==255:pos+=1
        if pos==len(data):break
        marker=data[pos];pos+=1
        if marker==0 or 0xd0<=marker<=0xd9:continue
        if pos+2>len(data):raise ValueError('truncated segment')
        size=int.from_bytes(data[pos:pos+2],'big')
        if size<2 or pos+size>len(data):raise ValueError('invalid segment size')
        if marker in [0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf]:
            sof.append(dict(marker=hex(marker),precision=data[pos+2],height=int.from_bytes(data[pos+3:pos+5],'big'),width=int.from_bytes(data[pos+5:pos+7],'big')))
        if marker==0xda:scans+=1
        pos+=size
    return dict(SOF=sof,SOS_count=scans)

def main():
    source=ROOT/'migration/reports/image-I0-rocJPEG-files.json';gpu=json.loads(source.read_text())
    raw=ROOT/json.loads((ROOT/gpu['evidence']/'manifest.json').read_text())['raw_artifact_dir']
    e=Experiment('I0','JPEG-original-CPU-and-rocJPEG-observation','CPU-reference',sources=[__file__,source])
    rows=[]
    for filename,sha in gpu['input_files'].items():
        p=ROOT/filename
        if digest(p)!=sha:raise RuntimeError('input changed')
        with Image.open(p) as image:mode=image.mode;rgb=np.array(image.convert('RGB'))
        result=dict(file=filename,input_sha256=sha,CPU_mode=mode,CPU_size=list(rgb.shape),markers=jpeg_markers(p.read_bytes()))
        target=raw/'outputs'/(p.name+'.rgb')
        if target.exists():
            if digest(target)!=gpu['outputs']['outputs/'+target.name]['sha256']:raise RuntimeError('GPU pixels changed')
            actual=np.fromfile(target,np.uint8).reshape(rgb.shape)
            error=actual.astype(np.int32)-rgb.astype(np.int32);mse=float(np.mean(error.astype(np.float64)**2))
            result.update(GPU_output_sha256=digest(target),pixels=int(rgb.size),max_abs=int(np.max(np.abs(error))),MSE=mse,PSNR_dB=10*math.log10(255**2/mse) if mse else None)
        else:result['GPU_status']=next(r for r in gpu['results'] if r.get('file')==p.name)
        rows.append(result)
    result=dict(status='OBSERVED',Pillow_jpeg_version=features.version_codec('jpg'),libjpeg_turbo=features.version_feature('libjpeg_turbo'),
                rows=rows,scope='Full-pixel measurements and input format identification only; no threshold frozen or final JPEG qualification issued.')
    write(e.path/'observations.json',result);ref=e.finish('OBSERVED')
    write(ROOT/'migration/reports/image-I0-JPEG-CPU-observations.json',dict(**result,evidence=ref))
    record('I0','12张原始JPEG均已用独立CPU解码并解析SOF/SOS；rocJPEG成功的10张记录全像素maxAbs/MSE/PSNR，失败2张保留原格式与实际返回值。未按观察结果放宽或签发阈值。',[ref])
    print(json.dumps(result))

if __name__=='__main__':main()
