#!/usr/bin/env python3
"""Freeze and measure native convergence on analytically zero monotone ramps."""
import argparse,json,shlex,tarfile
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
PROFILE=ROOT/'migration/rewrite/image-watershed-monotone-native-profile.json'
FOLDER=ROOT/'migration/fixtures/image-watershed-monotone-native'
SOURCE=ROOT/'rocm/probes/image/watershed_monotone_native.cpp'

def freeze():
    if PROFILE.exists():raise ValueError('already frozen')
    FOLDER.mkdir(parents=True,exist_ok=True);rows=[]
    for side in [17,33,49,65,97,129]:
        y,x=np.indices((side,side))
        for direction,array in [('x',x),('y',y),('diagonal',np.minimum(x+y,255)),('reverse-x',side-1-x)]:
            name=f'{direction}-{side}';path=FOLDER/(name+'.raw');path.write_bytes(array.astype(np.uint8).tobytes());rows.append(dict(id=name,width=side,height=side,path=str(path.relative_to(ROOT)),bytes=side*side,sha256=digest(path)))
    (FOLDER/'cases.txt').write_text(''.join(f'{r["id"]} {r["width"]} {r["height"]}\n' for r in rows))
    e=Experiment('I3','watershed-native-monotone-diagnostic-contract','CPU-contract',sources=[__file__,SOURCE,*[ROOT/r['path'] for r in rows]])
    result=dict(status='FROZEN_OBSERVATION_ONLY',inputs=rows,expected='Every nonzero pixel has a strictly lower neighbor and every terminal minimum has value0. The complete strict-descent image is therefore all0; do not assume vendor implementation reaches that result.',scope='Diagnose native NPP+ disagreement, not relax project acceptance.',dimensions=[17,33,49,65,97,129],layouts=['padded','compact'],vendors=['NPP','NPPPlus'],image_modes=5,repeats=2,additional_consecutive_NONE_passes=4);write(e.path/'profile.json',result);result['evidence']=e.finish('OBSERVED');write(PROFILE,result)
    record('IMG-02','针对NPP+长坡度差异冻结24个新解析输入（17–129、四方向）、两种pitch和4次连续调用；每个非零像素都有严格更低邻居，终点灰度必为0，作为独立收敛诊断。',[result['evidence']])

def run(plus,tight):
    p=json.loads(PROFILE.read_text());vendor='NPPPlus' if plus else 'NPP';layout='compact' if tight else 'padded';e=Experiment('I3','watershed-native-monotone-'+vendor+'-'+layout,'cuda-diagnosis',sources=[__file__,SOURCE,PROFILE,FOLDER/'cases.txt',*[ROOT/i['path'] for i in p['inputs']]])
    remote='/tmp/'+e.id;archive=e.path/'inputs.tar';flags=['-lnppif','-lnppc']
    if plus:
        sdk=next(r for r in json.loads((ROOT/'migration/reports/image-I0-native-private-SDKs.json').read_text()) if r['SDK']=='nppplus');prefix=sdk['remote']+'/libnpp_plus-linux-x86_64-'+sdk['identity']['version']+'_'+sdk['identity']['variant']+'-archive';flags=['-DIMAGE_NPP_PLUS','-I'+prefix+'/include','-L'+prefix+'/lib','-Xlinker','-rpath','-Xlinker',prefix+'/lib','-lnpp_plus_if','-lnpp_plus_c']
    if tight:flags=['-DIMAGE_TIGHT_PITCH',*flags]
    with tarfile.open(archive,'w') as tar:tar.add(SOURCE,arcname='probe.cpp');tar.add(FOLDER,arcname='inputs')
    steps=[(['ssh','nvidia-5090x2',shlex.join(['mkdir','-p',remote])],'prepare'),(['scp',str(archive),'nvidia-5090x2:'+remote+'/inputs.tar'],'upload'),(['ssh','nvidia-5090x2',shlex.join(['tar','xf',remote+'/inputs.tar','-C',remote])],'unpack'),(['ssh','nvidia-5090x2',shlex.join(['/usr/local/cuda-13.4/bin/nvcc','-std=c++17','-O2','-arch=sm_120',remote+'/probe.cpp','-o',remote+'/probe',*flags])],'build'),(['ssh','nvidia-5090x2',shlex.join(['env','CUDA_VISIBLE_DEVICES=1',remote+'/probe',remote+'/inputs',remote+'/outputs'])],'native-monotone-diagnosis'),(['scp','-r','nvidia-5090x2:'+remote+'/outputs',str(e.path/'outputs')],'collect')]
    rc=0
    for cmd,phase in steps:
        rc=e.command(cmd,phase,timeout=600)
        if rc:break
    folder=e.path/'outputs';files={f.name:dict(bytes=f.stat().st_size,sha256=digest(f)) for f in folder.glob('*') if f.is_file()} if folder.exists() else {};rows=[]
    if rc==0:
        for item in p['inputs']:
            values={}
            for suffix in ['-n8-m0-r0.segments','-n8-m0-r1.segments',*[f'-pass{k}.segments' for k in range(1,5)]]:
                a=np.fromfile(folder/(item['id']+suffix),np.uint8);values[suffix]=dict(nonzero_pixels=int(np.count_nonzero(a)),maximum=int(a.max()))
            rows.append(dict(case=item['id'],observations=values));print(vendor,layout,rows[-1],flush=True)
    result=dict(status='OBSERVED' if rc==0 else 'COMMAND_FAILED',vendor=vendor,layout=layout,return_code=rc,rows=rows,products=files);write(e.path/'result.json',result);result['evidence']=e.finish(result['status']);write(ROOT/f'migration/reports/image-watershed-monotone-{vendor}-{layout}.json',result)
    record('IMG-02',vendor+' '+layout+' 的24解析坡度/4次连续调用诊断：'+result['status']+'；实际非零像素及各次最大值封存，区分stride和全局传播行为。',[result['evidence']]);return int(rc!=0)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','run']);p.add_argument('--plus',action='store_true');p.add_argument('--tight',action='store_true');a=p.parse_args();raise SystemExit(freeze() if a.action=='freeze' else run(a.plus,a.tight))
