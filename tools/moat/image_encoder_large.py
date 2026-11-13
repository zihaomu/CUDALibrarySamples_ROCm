#!/usr/bin/env python3
"""Freeze and run large/maximum-axis original-entry JPEG encoder cases."""
import argparse,hashlib,json,struct,csv,math
from pathlib import Path
import numpy as np
from PIL import Image
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_prefix_trace_contract import algorithm_count,SELECTION

PROFILE=ROOT/'migration/rewrite/image-encoder-large-profile.json'
REPORT=ROOT/'migration/reports/image-encoder-large-runs.json'

def fixture(case):
    w,h=case['width'],case['height']
    if case['pattern']=='random':rgb=np.random.default_rng(case['seed']).integers(0,256,(h,w,3),dtype=np.uint8)
    else:
        axis=((np.arange(max(w,h),dtype=np.uint32)//8)&1).astype(np.uint8)*255
        rgb=np.repeat(axis.reshape(h,w,1),3,axis=2)
    stride=(w*3+3)&~3;rows=np.zeros((h,stride),dtype=np.uint8);rows[:,:w*3]=rgb[::-1,:,::-1].reshape(h,w*3)
    bmp=struct.pack('<2sIHHI',b'BM',54+rows.nbytes,0,0,54)+struct.pack('<IiiHHIIiiII',40,w,h,1,24,0,rows.nbytes,2835,2835,0,0)+rows.tobytes()
    return rgb,bmp

def freeze():
    if PROFILE.exists():raise ValueError('large original-entry contract already frozen')
    wide=json.loads((ROOT/'migration/rewrite/image-encoder-wide-profile.json').read_text());cases=[]
    for old in wide['cases']:
        c=dict(old,id='entry-'+old['id'],pattern='random',optimized=old['sampling']==1,jobs=3,exact_source_pixels=False)
        rgb,bmp=fixture(c)
        if hashlib.sha256(rgb.tobytes()).hexdigest()!=old['sha256']:raise ValueError('wide input regeneration drift')
        c['bmp_bytes']=len(bmp);c['bmp_sha256']=hashlib.sha256(bmp).hexdigest();cases.append(c)
    for w,h,s,opt in [(65535,1,2,False),(1,65535,1,True)]:
        c=dict(id=f'entry-{w}x{h}-maximum-axis',width=w,height=h,sampling=s,optimized=opt,quality=100,jobs=3,pattern='block-gray',exact_source_pixels=True)
        rgb,bmp=fixture(c);c.update(bytes=rgb.nbytes,sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),bmp_bytes=len(bmp),bmp_sha256=hashlib.sha256(bmp).hexdigest());cases.append(c)
    e=Experiment('I5','JPEG-large-original-entry-contract','CPU-contract',sources=[__file__,ROOT/'migration/rewrite/image-encoder-wide-profile.json',ROOT/'migration/environments/stb-image-reference.lock.json'])
    value=dict(status='FROZEN',cases=cases,
        gates=['Original entry, one state/two prepared slots/three requested jobs, exact three output filenames and serial-core JPEG byte identity.',
               'Every product decoded by the pinned independent CPU stb reference; complete dimensions/RGB byte count.',
               'For <=65500 random images, stb vs independent Pillow decoder: maxAbs<=4, every-channel RMSE<=1 and p99Abs<=2, PSNR>=48, per-channel global SSIM>=0.995.',
               'For 65535-axis Q100 grayscale blocks, independent CPU pixels must exactly equal all source bytes; no libjpeg dimension guard modification.',
               'Trace contains all two preparation plus three requested full-GPU images, and actual allowed GPU1.'],
        notes=['Raw random tensors and BMP files regenerate from pinned seed/shape/dtype and SHA. Large files may be omitted from the Git evidence copy, never from identity records.',
               'CPU decoder comparison validates legal interoperable output; full held-out native encoder equivalence and performance remain separate owed gates.'])
    write(e.path/'profile.json',value);value['evidence']=e.finish('OBSERVED');write(PROFILE,value)
    record('IMG-01','冻结8组大图原入口合同：6组65500单行列/4097x4095随机图，加65535横/竖轴Q100灰阶8像素块；24产品全部CPU跨解码，最大轴须源像素精确；完整CUDA等价仍另验。',[str(PROFILE.relative_to(ROOT)),value['evidence']]);print(value['evidence'])

def compare_decoders(actual,reference):
    a=actual.reshape(-1,3).astype(np.float64);b=reference.reshape(-1,3).astype(np.float64);difference=a-b;absolute=np.abs(difference)
    mse=float(np.mean(difference*difference));rmse=np.sqrt(np.mean(difference*difference,axis=0));p99=np.percentile(absolute,99,axis=0)
    ma=a.mean(axis=0);mb=b.mean(axis=0);va=a.var(axis=0);vb=b.var(axis=0);cov=((a-ma)*(b-mb)).mean(axis=0)
    ssim=((2*ma*mb+6.5025)*(2*cov+58.5225))/((ma*ma+mb*mb+6.5025)*(va+vb+58.5225))
    psnr=None if mse==0 else 10*math.log10(255*255/mse)
    metrics=dict(max_abs=int(absolute.max()),channel_rmse=rmse.tolist(),channel_p99_abs=p99.tolist(),psnr_db=psnr,channel_global_ssim=ssim.tolist())
    return metrics,bool(metrics['max_abs']<=4 and np.all(rmse<=1) and np.all(p99<=2) and (psnr is None or psnr>=48) and np.all(ssim>=0.995))

def run():
    from snapshot import capture
    profile=json.loads(PROFILE.read_text());names=['image-encoder-instances-v2-build.json','image-encoder-pipeline-build.json','image-stb-reference-build.json']
    reports=[ROOT/'migration/reports'/n for n in names];builds=[json.loads(p.read_text()) for p in reports];candidate,reference,cpu=builds
    for b in builds:
        if b['status']!='BUILT' or digest(ROOT/b['binary'])!=b['binary_sha256'] or any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()):raise ValueError('stale large-case executable')
    binaries=[dict(binary=b['binary'],sha256=b['binary_sha256'],build_report=str(path.relative_to(ROOT)),build_report_sha256=digest(path)) for b,path in zip(builds,reports)]
    rows=[]
    for case in profile['cases']:
        rgb,bmp=fixture(case)
        if rgb.nbytes!=case['bytes'] or hashlib.sha256(rgb.tobytes()).hexdigest()!=case['sha256'] or len(bmp)!=case['bmp_bytes'] or hashlib.sha256(bmp).hexdigest()!=case['bmp_sha256']:raise ValueError('frozen large fixture drift')
        e=Experiment('I5','JPEG-large-original-entry','rocm-trace-CPU-reference',case=case['id'],sources=[__file__,PROFILE,SELECTION,ROOT/'tools/moat/image_prefix_trace_contract.py',*reports,*[ROOT/n for b in builds for n in b['dependencies']]],parent=candidate['experiment_id'])
        observed=capture();write(e.path/'backend.observed.json',observed);folder=e.path/'inputs';folder.mkdir();bmp_path=folder/'image.bmp';bmp_path.write_bytes(bmp);del bmp
        raw=e.path/'source.rgb';rgb.tofile(raw);write(folder/'manifest.json',dict(contract=case,regenerate=['build/image-cpu-venv/bin/python','tools/moat/image_encoder_large.py','regenerate','--case',case['id'],'--output',str(folder)]))
        out=e.path/'products';out.mkdir();args=[str(ROOT/candidate['binary']),'-i',str(folder),'-o',str(out),'-j','1','-s','1','-n',str(case['jobs']),'-b','gpu','-q',str(case['quality'])]
        if case['sampling']==1:args+=['-p']
        if case['optimized']:args+=['-f']
        rc=e.command(['rocprofv3','--kernel-trace','--output-format','csv','--output-directory',str(e.path/'trace'),'--',*args],'large-original-entry-trace',timeout=600)
        checks=[dict(check='original-entry-command',passed=rc==0)];products=[];metrics={}
        try:
            with Image.open(bmp_path) as image:checks.append(dict(check='independent-BMP-load-exact-source',passed=image.size==(case['width'],case['height']) and image.convert('RGB').tobytes()==rgb.tobytes()))
            dest=e.path/'serial-reference';rr=e.command([str(ROOT/reference['binary']),str(raw),str(case['width']),str(case['height']),str(case['quality']),str(case['sampling']),str(int(case['optimized'])),'0','1',str(dest)],'separate-serial-core-reference',timeout=600)
            checks.append(dict(check='serial-reference-command',passed=rr==0));oracle=dest/'serial-reference.jpg';oracle_sha=digest(oracle)
            checks.append(dict(check='exact-three-products',passed={x.name for x in out.iterdir()}=={str(i)+'.jpg' for i in range(case['jobs'])}))
            ld=e.command(['ldd',str(ROOT/cpu['binary'])],'actual-CPU-reference-loader')
            loader=(e.path/e.commands[-1]['stdout']).read_text().lower();checks.append(dict(check='actual-CPU-reference-no-HIP-CUDA-libjpeg-link',passed=ld==0 and all(x not in loader for x in ['libamdhip','libcuda','libjpeg','libnvjpeg'])))
            pillow=None
            if not case['exact_source_pixels']:
                with Image.open(oracle) as image:pillow=np.array(image.convert('RGB'))
            for index in range(case['jobs']):
                path=out/(str(index)+'.jpg');decoded=e.path/(str(index)+'.cpu.rgb')
                checks.append(dict(check='complete-JPEG-byte-exact-'+str(index),passed=digest(path)==oracle_sha))
                cr=e.command([str(ROOT/cpu['binary']),str(path),str(decoded)],'independent-CPU-decode-'+str(index),timeout=300)
                checks.append(dict(check='CPU-decode-command-'+str(index),passed=cr==0));info=json.loads((e.path/e.commands[-1]['stdout']).read_text())
                checks.append(dict(check='complete-CPU-RGB-geometry-'+str(index),passed=info==dict(width=case['width'],height=case['height'],source_components=3,RGB_bytes=case['bytes']) and decoded.stat().st_size==case['bytes']))
                pixels=np.fromfile(decoded,dtype=np.uint8).reshape(rgb.shape)
                if case['exact_source_pixels']:
                    exact=bool(np.array_equal(pixels,rgb));comparison=dict(source_pixels_exact=exact);passed=exact
                else:comparison,passed=compare_decoders(pixels,pillow)
                checks.append(dict(check='independent-CPU-pixel-reference-'+str(index),passed=passed))
                products.append(dict(name=path.name,bytes=path.stat().st_size,sha256=digest(path),decoded_rgb_sha256=digest(decoded),comparison=comparison))
            traces=list((e.path/'trace').rglob('*kernel_trace.csv'));agents=list((e.path/'trace').rglob('*agent_info.csv'))
            if len(traces)!=len(agents) or len(traces)!=1:raise ValueError('missing unique trace/agent tables')
            kernels=list(csv.DictReader(traces[0].open()));app=[r for r in kernels if not r['Kernel_Name'].startswith('__amd_rocclr_')]
            expected=(case['jobs']+2)*algorithm_count(oracle,case['optimized']);streams={r['Stream_Id'] for r in app}
            checks.append(dict(check='all-preparation-and-requested-GPU-images',passed=len(app)==expected and len(streams)==2,actual=len(app),expected=expected,streams=sorted(streams)))
            lookup={r['Node_Id']:r for r in csv.DictReader(agents[0].open())};allowed={d['pci_bdf'] for d in observed['devices'] if d['physical_id']==1};valid=True
            for row in kernels:
                agent=lookup[row['Agent_Id'].split()[-1]];loc=int(agent['Location_Id']);pci=f"{int(agent['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}"
                valid &= pci in allowed and int(row['End_Timestamp'])>int(row['Start_Timestamp']) and int(row['Grid_Size_X'])>0
            checks.append(dict(check='all-actual-kernels-on-GPU1',passed=bool(kernels) and valid));metrics=dict(kernel_count=len(app),source_rgb_sha256=case['sha256'],bmp_sha256=case['bmp_sha256'])
        except Exception as error:checks.append(dict(check='validation-exception',passed=False,error=repr(error)))
        status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(case=case['id'],status=status,checks=checks,products=products,metrics=metrics,binaries=binaries,experiment_id=e.id)
        write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks));rows.append(row);write(REPORT,rows)
        record('IMG-01','大图原入口 '+case['id']+'：'+status+'；3产品、第二CPU跨解码/像素和实际5图GPU trace完整记录。',[row['evidence']]);print(case['id'],status,flush=True)
    return int(any(r['status']!='PASSED' for r in rows))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','run','regenerate']);parser.add_argument('--case');parser.add_argument('--output');args=parser.parse_args()
    if args.action=='regenerate':
        c=next(c for c in json.loads(PROFILE.read_text())['cases'] if c['id']==args.case);rgb,bmp=fixture(c);folder=Path(args.output);folder.mkdir(parents=True,exist_ok=True);(folder/'image.bmp').write_bytes(bmp);rgb.tofile(folder/'source.rgb')
    else:raise SystemExit(globals()[args.action]())
