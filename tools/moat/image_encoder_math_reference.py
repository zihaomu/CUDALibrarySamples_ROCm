#!/usr/bin/env python3
"""Independent fresh retained CPU encoder and quality gates with actual loader IDs."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import numpy as np
import PIL,PIL._imaging
from PIL import Image,ImageFile,JpegImagePlugin,features
from experiment import ROOT,Experiment,digest,write
from audit import check as audit_check
from image_completion_progress import record
from image_encoder_math_validation import validate,strict_reference_build
from image_encoder_math_binding import BUILD,current,probe_binding,cpu_binding
PROFILE=ROOT/'migration/rewrite/image-encoder-math-variant-v2-profile.json'
LOCK=ROOT/'migration/environments/image-quality-cpu-reference.json'
REPORT=ROOT/'migration/reports/image-encoder-math-cpu.json'

def identity():
    libs={Path(line.split()[-1]).resolve() for line in Path('/proc/self/maps').read_text().splitlines() if 'libjpeg' in line and '.so' in line}
    if len(libs)!=1:raise ValueError('one actual CPU libjpeg required')
    paths=[Path(PIL._imaging.__file__),Path(Image.__file__),Path(JpegImagePlugin.__file__),*sorted(libs)]
    if any(not p.is_relative_to(ROOT/'build/image-cpu-venv') for p in paths):raise ValueError('CPU reference escaped pinned venv')
    return dict(Pillow=PIL.__version__,libjpeg=features.version_codec('jpg'),jpeg_turbo=features.version_feature('libjpeg_turbo'),
        python=sys.version,dependencies={str(p.relative_to(ROOT)):digest(p) for p in paths})

def freeze():
    if LOCK.exists():raise ValueError('reference identity already frozen')
    value=identity();e=Experiment('I5','encoder-quality-independent-CPU-identity','CPU-contract',sources=[__file__,PROFILE,*[ROOT/n for n in value['dependencies']]])
    write(e.path/'identity.json',value);value['evidence']=e.finish('OBSERVED');write(LOCK,value)
    record('IMG-01','编码质量独立CPU环境锁定：Pillow/libjpeg实际加载路径、SHA及版本已封存，后续每次比较重核。',[value['evidence']])

def frame_identity(data):
    if data[:2]!=b'\xff\xd8':raise ValueError('JPEG SOI required')
    cursor=2;frames=[]
    while cursor<len(data):
        if data[cursor]!=255:raise ValueError('invalid JPEG header marker')
        while cursor<len(data) and data[cursor]==255:cursor+=1
        if cursor>=len(data):raise ValueError('truncated marker')
        marker=data[cursor];cursor+=1
        if marker in [0xda,0xd9]:break
        if marker in [0,0xd8,0x01] or 0xd0<=marker<=0xd7:raise ValueError('unexpected header marker')
        length=int.from_bytes(data[cursor:cursor+2],'big')
        if length<2 or cursor+length>len(data):raise ValueError('invalid segment length')
        if 0xc0<=marker<=0xcf and marker not in [0xc4,0xc8,0xcc]:
            if length<8 or length!=8+3*data[cursor+7]:raise ValueError('invalid SOF length')
            frames.append(dict(sof=marker,precision=data[cursor+2],components=data[cursor+7]))
        cursor+=length
    if len(frames)!=1:raise ValueError('exactly one JPEG frame required')
    return frames[0]

def baseline(frame):return frame==dict(sof=0xc0,precision=8,components=3)

def decode(path):
    with Image.open(path) as im:
        im.load();rgb=np.array(im.convert('RGB'));info=dict(size=list(im.size),sampling=JpegImagePlugin.get_sampling(im),
            quant={str(k):v for k,v in im.quantization.items()},progressive=bool(im.info.get('progression',im.info.get('progressive',0))),frame=frame_identity(path.read_bytes()))
    return rgb,info

def metrics(actual,source):
    a=actual.reshape(-1,3).astype(np.float64);b=source.reshape(-1,3).astype(np.float64);d=a-b;mse=(d*d).mean(0)
    ma=a.mean(0);mb=b.mean(0);va=a.var(0);vb=b.var(0);cov=((a-ma)*(b-mb)).mean(0)
    ssim=((2*ma*mb+6.5025)*(2*cov+58.5225))/((ma*ma+mb*mb+6.5025)*(va+vb+58.5225))
    return dict(channel_mse=mse.tolist(),channel_psnr=[10*math.log10(65025/x) if x else None for x in mse],
        channel_global_ssim=ssim.tolist(),max_abs=int(np.abs(d).max()),channel_p99_abs=np.percentile(np.abs(d),99,axis=0).tolist())

def tiles(actual,source,size):
    return np.array([((actual[y:y+size,x:x+size].astype(np.float64)-source[y:y+size,x:x+size])**2).mean(axis=(0,1))
        for y in range(0,source.shape[0],size) for x in range(0,source.shape[1],size)])

def quality_checks(candidate,reference,source,g,label):
    a=metrics(candidate,source);b=metrics(reference,source);at=tiles(candidate,source,g['tile_size']);bt=tiles(reference,source,g['tile_size'])
    checks=[dict(check=label+'-source-channel-MSE',passed=bool(np.all(np.array(a['channel_mse'])<=np.array(b['channel_mse'])*g['source_channel_mse_factor']+g['source_channel_mse_floor']))),
        dict(check=label+'-source-every-tile-MSE',passed=bool(np.all(at<=bt*g['source_tile_mse_factor']+g['source_tile_mse_floor']))),
        dict(check=label+'-source-channel-global-SSIM',passed=bool(np.all(np.array(a['channel_global_ssim'])>=np.array(b['channel_global_ssim'])-g['source_global_ssim_drop'])))]
    return checks,dict(pairwise=metrics(candidate,reference),candidate_tile_mse=at.tolist(),reference_tile_mse=bt.tolist())

def run():
    p=json.loads(PROFILE.read_text());g=p['gates'];lock=json.loads(LOCK.read_text())
    if identity()!={k:v for k,v in lock.items() if k!='evidence'}:raise ValueError('actual CPU reference identity drift')
    paths={s:ROOT/f'migration/reports/image-encoder-math-{s}.json' for s in ['amd','native']};sides={s:json.loads(path.read_text()) for s,path in paths.items()}
    for side,rows in sides.items():
        if [r['case'] for r in rows]!=[c['id'] for c in p['cases']] or len(rows)!=80:raise ValueError('incomplete '+side+' quality matrix')
        for r in rows:
            proof=ROOT/r['evidence']
            if audit_check(proof) or json.loads((proof/'result.json').read_text())!={k:v for k,v in r.items() if k!='evidence'} or r['status']!='PASSED' or not all(c['passed'] for c in r['checks']):raise ValueError('invalid '+side+' run')
            if len(r['products'])!=1 or r['products'][0]['name']!='0.jpg':raise ValueError('wrong product set')
            item=r['products'][0];q=ROOT/item['path']
            if digest(q)!=item['sha256'] or q.stat().st_size!=item['bytes']:raise ValueError('product drift')
    probe_path=ROOT/'migration/reports/image-encoder-math-probe.json';probes=json.loads(probe_path.read_text())
    expected=[c['id'] for c in p['cases'] if not c['optimized']]
    if [r['case'] for r in probes]!=expected:raise ValueError('complete probe case set required')
    for r in probes:
        proof=ROOT/r['evidence']
        if audit_check(proof) or json.loads((proof/'result.json').read_text())!={k:v for k,v in r.items() if k!='evidence'} or r['status']!='PASSED':raise ValueError('invalid probe proof')
    probe_map={r['case']:r for r in probes};reference=json.loads((ROOT/'migration/reports/image-encoder-math-reference-build.json').read_text())
    candidate=json.loads(BUILD.read_text());current(candidate);cpu_binding(reference)
    extra=[ROOT/'tools/moat'/n for n in ['image_encoder_math_validation.py','image_encoder_math_oracle.py','image_jpeg_baseline_entropy_reference.py','image_jpeg_reference_modes.py','image_encoder_math_binding.py']]
    extra += [BUILD,probe_path,ROOT/'migration/reports/image-encoder-math-reference-build.json',ROOT/'rocm/probes/image/jpeg_cpu_coefficients_strict.cpp',ROOT/reference['library']]
    rows=[]
    for index,c in enumerate(p['cases']):
        item=next(i for i in p['inputs'] if i['id']==c['input']);source_path=ROOT/item['path'];runs={s:r[index] for s,r in sides.items()};products={s:ROOT/r['products'][0]['path'] for s,r in runs.items()}
        probe=probe_map[c['id'].rsplit('-opt',1)[0]+'-opt0']
        probe_binding(probe,candidate,c,item)
        if runs['amd']['binary_sha256']!=candidate['binary_sha256'] or runs['amd']['build_report_sha256']!=digest(BUILD):raise ValueError('candidate original-entry build receipt')
        e=Experiment('I5','encoder-complete-mathematical-quality','CPU-reference',case=c['id'],sources=[__file__,PROFILE,LOCK,*extra,*[ROOT/a['path'] for a in probe['products']],source_path,Path(ImageFile.__file__),*paths.values(),*products.values(),*[ROOT/n for n in lock['dependencies']]])
        checks=[];diagnostics=[];data={};decoded={}
        try:
            observed=identity();write(e.path/'CPU-loader-identity.json',observed);checks.append(dict(check='actual-CPU-reference-identity',passed=observed=={k:v for k,v in lock.items() if k!='evidence'}))
            with Image.open(source_path) as im:source=np.array(im.convert('RGB'))
            checks.append(dict(check='complete-frozen-source-identity',passed=digest(source_path)==item['sha256'] and hashlib.sha256(source.tobytes()).hexdigest()==item['rgb_sha256']))
            # Pillow guesses 1 or 2 bytes/pixel for optimized RGB output.
            # Reserve room for baseline entropy, stuffing and marker overhead.
            ImageFile.MAXBLOCK=source.nbytes*8+65536
            write(e.path/'CPU-destination-buffer.json',dict(bytes=ImageFile.MAXBLOCK,reason='24 bytes/pixel plus markers; codec and quality parameters unchanged'))
            output=e.path/'cpu.jpg';Image.fromarray(source).save(output,format='JPEG',quality=c['quality'],subsampling=0 if c['sampling']==1 else 2,optimize=c['optimized']);products['cpu']=output
            arrays={};structure={}
            for side,path in products.items():arrays[side],structure[side]=decode(path);decoded[side]=hashlib.sha256(arrays[side].tobytes()).hexdigest()
            checks.append(dict(check='geometry-sampling-DQT-baseline-exact',passed=all(a.shape==source.shape for a in arrays.values()) and all(v==structure['cpu'] for v in structure.values()) and all(baseline(v['frame']) for v in structure.values()) and not structure['cpu']['progressive'] and structure['cpu']['sampling']==(0 if c['sampling']==1 else 2)))
            for side in ['cpu','native']:
                tests,values=quality_checks(arrays['amd'],arrays[side],source,g,side)
                checks += [t for t in tests if not t['check'].endswith('-source-every-tile-MSE')]
                diagnostics += [t for t in tests if t['check'].endswith('-source-every-tile-MSE')]
                data[side]=values
            tests,values=validate(e,source,c,products['amd'],probe,reference,p);checks+=tests;data['mathematics']=values
            data['structures']=structure;data['source_metrics']={s:metrics(a,source) for s,a in arrays.items()}
        except Exception as error:checks.append(dict(check='validation-exception',passed=False,error=repr(error)))
        status='PASSED' if checks and all(x['passed'] for x in checks) else 'FAILED'
        row=dict(case=c['id'],status=status,acceptance=p['acceptance'],checks=checks,tile_diagnostics=diagnostics,metrics=data,decoded_sha256=decoded,experiment_id=e.id,evidence_references=[r['evidence'] for r in runs.values()]+[probe['evidence'],reference['evidence'],candidate['evidence']])
        write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks));rows.append(row);write(REPORT,rows)
        record('IMG-01','完整数学变体三方编码 '+c['id']+'：'+status+'；逐像素/系数/全部MCU数学门槛及原全图质量检查，旧局部比值单列诊断。',[row['evidence']]);print(c['id'],status,flush=True)
    return int(any(r['status']!='PASSED' for r in rows))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','run']);a=parser.parse_args();raise SystemExit(globals()[a.action]())
