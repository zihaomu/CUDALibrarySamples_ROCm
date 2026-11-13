#!/usr/bin/env python3
"""Freeze semantic inputs and observe native watershed modes before a new GPU port."""
import argparse,json,shlex,tarfile
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
PROFILE=ROOT/'migration/rewrite/image-watershed-semantics-profile.json'
SOURCE=ROOT/'rocm/probes/image/watershed_semantics_native.cpp'

def freeze():
    if PROFILE.exists():raise ValueError('already frozen')
    folder=ROOT/'migration/fixtures/image-watershed-semantics';folder.mkdir(parents=True,exist_ok=True)
    y,x=np.indices((33,35));flat=np.full((33,35),120,np.uint8)
    samples={'constant':flat,'ramp-x':(x*7).astype(np.uint8),'ramp-y':(y*7).astype(np.uint8),'two-basins':np.minimum((x-8)**2+(y-16)**2,(x-26)**2+(y-16)**2).clip(0,255).astype(np.uint8),'saddle':np.abs((x-17)*(y-16)).clip(0,255).astype(np.uint8),'stairs':((x//5+y//5)*13).astype(np.uint8),'checker':(((x+y)%2)*255).astype(np.uint8),'diagonal-minima':np.where(x==y,0,120).astype(np.uint8),'quantized-random':(np.random.default_rng(73951).integers(0,8,(33,35))*31).astype(np.uint8),'pixel':np.array([[73]],np.uint8),'single-row':np.array([[9,8,8,8,3,3,8,8,8,1,1,8,8,9]],np.uint8),'single-column':np.array([[9,8,8,8,3,3,8,8,8,1,1,8,8,9]],np.uint8).T}
    for name,points in [('plateau-opposite-outlets',[(16,0,0),(16,34,40)]),('plateau-equal-outlets',[(16,0,0),(16,34,0)]),('edge-minimum',[(0,0,0)]),('interior-minimum',[(16,17,0)]),('connected-flat-minima',[(16,i,0) for i in range(8,27)]),('plateau-three-outlets',[(0,17,0),(32,0,20),(32,34,40)])]:
        a=flat.copy()
        for yy,xx,value in points:a[yy,xx]=value
        samples[name]=a
    rows=[]
    for name,a in samples.items():
        p=folder/(name+'.raw');p.write_bytes(a.tobytes());rows.append(dict(id=name,width=a.shape[1],height=a.shape[0],path=str(p.relative_to(ROOT)),sha256=digest(p),bytes=a.nbytes))
    (folder/'cases.txt').write_text(''.join(f'{r["id"]} {r["width"]} {r["height"]}\n' for r in rows))
    e=Experiment('I3','watershed-native-semantic-input-contract','CPU-contract',sources=[__file__,SOURCE,*[ROOT/r['path'] for r in rows]])
    row=dict(status='FROZEN_OBSERVATION_ONLY',inputs=rows,connectivity=[4,8],modes=['NONE','BLACK','WHITE','CONTRAST','ONLY'],scratch_fills=[0,127,255],image_pitch='width+7',labels_pitch='4*(width+5)',scope='Native semantics and repeatability observations, not an AMD acceptance relaxation. Candidate algorithm and held-out partition/boundary contract follow this investigation.',sources=['https://docs.nvidia.com/cuda/archive/11.5.2/npp/group__image__filter__watershed__segmentation.html','https://citius.usc.es/sites/default/files/publicacions/IEEE-OA-efficient-watershed-CA.pdf'])
    write(e.path/'contract.json',row);row['evidence']=e.finish('OBSERVED');write(PROFILE,row)
    record('IMG-02','冻结18个Watershed语义输入：平台、双盆地/鞍点、等高连接、阶梯、边缘种子及单行列；先观察两种邻域/5输出模式/3scratch初始化与padding，未设AMD通过门槛。',[row['evidence']])

def run(plus=False):
    profile=json.loads(PROFILE.read_text());vendor='NPPPlus' if plus else 'NPP';folder=ROOT/'migration/fixtures/image-watershed-semantics'
    if any(digest(ROOT/i['path'])!=i['sha256'] for i in profile['inputs']):raise ValueError('frozen inputs changed')
    e=Experiment('I3','watershed-small-semantics-'+vendor,'cuda-observation',sources=[__file__,SOURCE,PROFILE,folder/'cases.txt',*[ROOT/i['path'] for i in profile['inputs']]])
    remote='/tmp/'+e.id;archive=e.path/'inputs.tar';flags=['-lnppif','-lnppc']
    if plus:
        sdk=next(r for r in json.loads((ROOT/'migration/reports/image-I0-native-private-SDKs.json').read_text()) if r['SDK']=='nppplus');prefix=sdk['remote']+'/libnpp_plus-linux-x86_64-'+sdk['identity']['version']+'_'+sdk['identity']['variant']+'-archive';flags=['-DIMAGE_NPP_PLUS','-I'+prefix+'/include','-L'+prefix+'/lib','-Xlinker','-rpath','-Xlinker',prefix+'/lib','-lnpp_plus_if','-lnpp_plus_c']
    with tarfile.open(archive,'w') as tar:tar.add(SOURCE,arcname='probe.cpp');tar.add(folder,arcname='inputs')
    steps=[(['ssh','nvidia-5090x2',shlex.join(['mkdir','-p',remote])],'prepare'),(['scp',str(archive),'nvidia-5090x2:'+remote+'/inputs.tar'],'upload'),(['ssh','nvidia-5090x2',shlex.join(['tar','xf',remote+'/inputs.tar','-C',remote])],'unpack'),(['ssh','nvidia-5090x2',shlex.join(['/usr/local/cuda-13.4/bin/nvcc','-std=c++17','-O2','-arch=sm_120',remote+'/probe.cpp','-o',remote+'/probe',*flags])],'build'),(['ssh','nvidia-5090x2',shlex.join(['env','CUDA_VISIBLE_DEVICES=1',remote+'/probe',remote+'/inputs',remote+'/outputs'])],'native-semantic-observations'),(['scp','-r','nvidia-5090x2:'+remote+'/outputs',str(e.path/'outputs')],'collect')]
    rc=0
    for cmd,phase in steps:
        rc=e.command(cmd,phase,timeout=240)
        if rc:break
    outputs=e.path/'outputs';files={str(p.relative_to(outputs)):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in outputs.rglob('*') if p.is_file()} if outputs.exists() else {}
    status='OBSERVED' if rc==0 else 'FAILED';row=dict(status=status,vendor=vendor,return_code=rc,remote=remote,products=files,scope=profile['scope'])
    write(e.path/'result.json',row);row['evidence']=e.finish('OBSERVED' if rc==0 else 'NATIVE_MISMATCH');write(ROOT/f'migration/reports/image-watershed-semantics-{vendor}.json',row)
    record('IMG-02',vendor+'18个小输入语义观察：'+status+'，原始API返回/重复scratch/padding和全部产品保留，下一步建立独立规则模型。',[row['evidence']]);print(vendor,status,len(files));return int(rc!=0)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','run']);p.add_argument('--plus',action='store_true');a=p.parse_args();raise SystemExit(freeze() if a.action=='freeze' else run(a.plus))
