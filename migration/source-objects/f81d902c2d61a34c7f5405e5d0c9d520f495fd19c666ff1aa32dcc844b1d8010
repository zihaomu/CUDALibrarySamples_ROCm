#!/usr/bin/env python3
"""Qualify current resize products against independent baseline JPEG mathematics."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageFile
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_encoder_math_binding import sealed,cpu_binding
from image_encoder_math_oracle import color,coefficient_checks
from image_encoder_quality_reference import LOCK,identity,decode,baseline,quality_checks
from image_jpeg_baseline_entropy_reference import decode as entropy_decode
from image_jpeg_reference_modes import loaded_library_check

PROFILE=ROOT/'migration/rewrite/image-encoder-resize-math-profile.json'
MATH=ROOT/'migration/rewrite/image-encoder-math-variant-v2-profile.json'
INTEGRATION=ROOT/'migration/reports/image-jpeg-encoder-full-gpu-integration.json'
REFERENCE=ROOT/'migration/reports/image-encoder-math-reference-build.json'
REPORT=ROOT/'migration/reports/image-encoder-resize-math.json'

def bound_member(root,seal,path):
    name=str(path.relative_to(root));expected=seal.get(name)
    if expected is None or not path.is_file() or path.stat().st_size!=expected['bytes'] or digest(path)!=expected['sha256']:
        raise ValueError('product differs from original production seal: '+name)
    return expected['sha256']

def inventory():
    runs=json.loads(INTEGRATION.read_text());products=[]
    if [r['source'] for r in runs]!=['nvJPEG/Image-Resize/imageResize.cpp','nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp']:raise ValueError('both original entries required')
    for run in runs:
        proof=sealed(run,'integration.json')
        if run['status']!='PASSED_SUBSET' or not all(c['passed'] for c in run['checks']):raise ValueError('integration failed')
        if any(digest(ROOT/n)!=h for n,h in run['dependencies'].items()):raise ValueError('integration source drift')
        raw=ROOT/str(proof.relative_to(ROOT)).replace('migration/reports/evidence/','artifacts/')
        seal=json.loads((proof/'sealed.json').read_text())['files']
        if digest(raw/'sample')!=run['binary_sha256']:raise ValueError('integration binary drift')
        count=0
        for case in run['cases']:
            folder=raw/case['case'];meta=folder/'case.json';bound_member(raw,seal,meta);m=json.loads(meta.read_text())
            if len(m['outputs'])!=case['encoded_products']:raise ValueError('complete output count')
            for output in m['outputs']:
                md=output['metadata'];path=folder/output['raw'];jpeg=path.with_name(path.name.rsplit('.rgbi.s',1)[0])
                bound_member(raw,seal,path);bound_member(raw,seal,jpeg)
                # components describes the source JPEG (including grayscale),
                # while rgbi is the three-channel postprocess/encoder input.
                if md['format']!='rgbi' or not md['gpu_full_encode'] or md['cpu_entropy_encode']:raise ValueError('production encoding route')
                if path.stat().st_size!=md['width']*md['height']*3:raise ValueError('RGB extent')
                products.append(dict(source=run['source'],case=case['case'],raw=str(path.relative_to(ROOT)),raw_sha256=digest(path),jpeg=str(jpeg.relative_to(ROOT)),jpeg_sha256=digest(jpeg),metadata=str(meta.relative_to(ROOT)),metadata_sha256=digest(meta),width=md['width'],height=md['height'],quality=output['parameters'].get('quality',85),sampling=2,evidence=run['evidence']))
                count+=1
        if count!=(33 if 'WaterMark' not in run['source'] else 35):raise ValueError('33/35 exact product sets')
    if len(products)!=68:raise ValueError('68 products required')
    return runs,products

def negative():
    e=Experiment('I5','resize-production-seal-negative-controls','CPU-negative',sources=[__file__,INTEGRATION])
    runs,products=inventory();item=products[0];root=ROOT/item['evidence'].replace('migration/reports/evidence/','artifacts/');seal=json.loads((ROOT/item['evidence']/'sealed.json').read_text())['files'];path=ROOT/item['jpeg']
    checks=[dict(check='all68-current-production-products-bound',passed=len(products)==68)]
    target=e.path/'fixture';target.mkdir();copy=target/'image.jpg';copy.write_bytes(path.read_bytes());expected={'image.jpg':dict(bytes=copy.stat().st_size,sha256=digest(copy))}
    checks.append(dict(check='unchanged-sealed-member-accepted',passed=bound_member(target,expected,copy)==digest(path)))
    variants=[('wrong-SHA',{'image.jpg':dict(bytes=copy.stat().st_size,sha256='0'*64)}),('missing-seal-member',{})]
    for name,changed in variants:
        try:bound_member(target,changed,copy);rejected=False
        except ValueError:rejected=True
        checks.append(dict(check='reject-'+name,passed=rejected))
    data=bytearray(copy.read_bytes());data[-1]^=1;copy.write_bytes(data)
    for name in ['replaced-product','missing-product']:
        if name=='missing-product':copy.unlink()
        try:bound_member(target,expected,copy);rejected=False
        except ValueError:rejected=True
        checks.append(dict(check='reject-'+name,passed=rejected))
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(status=status,checks=checks,evidence_references=[r['evidence'] for r in runs])
    write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'VALIDATOR_GAP',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-resize-math-negatives.json',row)
    record('IMG-01','resize生产产品身份修复：'+status+'；逐项对原生产seal核验metadata/raw/JPEG尺寸及SHA，错SHA、缺seal成员、替换与缺文件4项反向检查；先前数值未变。',[row['evidence']]);print(status);return int(status!='PASSED')

def freeze():
    if PROFILE.exists():raise ValueError('profile already frozen')
    runs,products=inventory();math=json.loads(MATH.read_text())
    e=Experiment('I5','resize-baseline-mathematical-contract','CPU-contract',sources=[__file__,MATH,INTEGRATION])
    row=dict(status='FROZEN',acceptance='ALGORITHM_VARIANT',products=products,mathematics=math['mathematics'],gates=math['gates'],scope='Current 68 original resize products; complete RGB input to entropy output mathematics, strict framing, unchanged whole-image CPU quality. Progressive output/metadata/full GPU decode remain outside this subset; no old-versus-old JPEG comparison.')
    write(e.path/'contract.json',row);row['evidence']=e.finish('OBSERVED');write(PROFILE,row)
    record('IMG-01','当前两个resize入口68产品数学合同冻结：原RGB/JPEG/metadata完整SHA、逐系数及全部MCU、CPU全图质量；独立检查新生产输出，原旧码流比较不沿用。',[row['evidence']])

def run():
    profile=json.loads(PROFILE.read_text());runs,products=inventory()
    if products!=profile['products']:raise ValueError('frozen current output set drift')
    reference=json.loads(REFERENCE.read_text());cpu_binding(reference);lock=json.loads(LOCK.read_text())
    if identity()!={k:v for k,v in lock.items() if k!='evidence'}:raise ValueError('Pillow CPU identity drift')
    helpers=['image_encoder_math_binding.py','image_encoder_math_oracle.py','image_encoder_quality_reference.py','image_jpeg_baseline_entropy_reference.py','image_jpeg_reference_modes.py']
    sources=[__file__,PROFILE,MATH,INTEGRATION,REFERENCE,LOCK,*[ROOT/'tools/moat'/n for n in helpers],*[ROOT/n for n in lock['dependencies']],ROOT/reference['library']]
    sources += [ROOT/n for r in runs for n in r['dependencies']]
    sources += [ROOT/i[k] for i in products for k in ['raw','jpeg','metadata']]
    e=Experiment('I5','resize-complete-baseline-mathematical-products','CPU-reference',sources=list(dict.fromkeys(map(str,sources))))
    rows=[];checks=[]
    try:
        write(e.path/'CPU-loader-identity.json',identity())
        for index,item in enumerate(products):
            tests=[];jpeg=ROOT/item['jpeg'];rgb=np.fromfile(ROOT/item['raw'],np.uint8).reshape(item['height'],item['width'],3)
            rc=e.command([str(ROOT/reference['binary']),str(jpeg)],'strict-CPU-'+str(index))
            tests.append(dict(check='strict-libjpeg-zero-warnings',passed=rc==0))
            tests.append(loaded_library_check(e,e.commands[-1],dict(dependencies={reference['library']:reference['library_sha256']})))
            decoded=json.loads((e.path/e.commands[-1]['stdout']).read_text());strict=entropy_decode(jpeg.read_bytes())
            tests.append(dict(check='strict-frame',passed=(strict['width'],strict['height'],strict['sampling'])==(item['width'],item['height'],2) and (decoded['width'],decoded['height'],len(decoded['components']))==(item['width'],item['height'],3)))
            arrays={};details=[];expected=set();mx=(item['width']+15)//16;my=(item['height']+15)//16
            for c,component in enumerate(decoded['components']):
                plane=color(rgb,c,2);ph,pw=plane.shape;bh,bw=(ph+7)//8,(pw+7)//8
                if (component['height_blocks'],component['width_blocks'])!=(bh,bw):raise ValueError('component extent')
                coeff=np.array(component['coefficients']).reshape(bh,bw,8,8);arrays[c]=coeff
                math=coefficient_checks(plane,coeff,component['quant'],profile['mathematics']['absolute_DCT_error_budget']);details.append(dict(channel=c,**math))
                tests.append(dict(check='complete-local-mathematics-'+str(c),passed=math['passed']))
                tests.append(dict(check='independent-DQT-'+str(c),passed=strict['quant'][strict['components'][c]['quant']]==component['quant']))
                scale=2 if c==0 else 1;expected.update((c,x,y) for y in range(my*scale) for x in range(mx*scale))
            seen=set();equal=True;dummy=0
            for block in strict['blocks']:
                c,x,y=block['channel'],block['x'],block['y'];key=c,x,y;array=arrays[c]
                if key in seen:raise ValueError('duplicate entropy block')
                seen.add(key);padding=y>=array.shape[0] or x>=array.shape[1];dummy+=int(padding)
                equal &= block['coefficients']==([0]*64 if padding else array[y,x].ravel().tolist())
            tests.append(dict(check='independent-complete-entropy-and-dummy-coefficients',passed=seen==expected and equal,MCU_blocks=len(seen),dummy_blocks=dummy))
            ImageFile.MAXBLOCK=rgb.nbytes*8+65536;cpu=e.path/f'cpu-{index}.jpg';Image.fromarray(rgb).save(cpu,format='JPEG',quality=item['quality'],subsampling=2,optimize=False)
            actual,structure=decode(jpeg);reference_rgb,reference_structure=decode(cpu)
            tests.append(dict(check='baseline-quality-sampling-DQT-geometry',passed=structure==reference_structure and baseline(structure['frame']) and actual.shape==rgb.shape))
            quality,metrics=quality_checks(actual,reference_rgb,rgb,profile['gates'],'CPU')
            tests += [t for t in quality if not t['check'].endswith('-source-every-tile-MSE')]
            row=dict(index=index,source=item['source'],case=item['case'],JPEG_sha256=item['jpeg_sha256'],raw_RGB_sha256=item['raw_sha256'],checks=tests,mathematics=details,tile_diagnostics=[t for t in quality if t['check'].endswith('-source-every-tile-MSE')],metrics=metrics)
            rows.append(row);checks.append(dict(check='product-'+str(index),passed=all(t['passed'] for t in tests)))
            print(index,item['case'],checks[-1]['passed'],flush=True)
            if not checks[-1]['passed']:break
    except Exception as error:checks.append(dict(check='validation-exception',passed=False,error=repr(error)))
    checks.append(dict(check='all-68-current-products',passed=len(rows)==68))
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED'
    result=dict(status=status,acceptance=profile['acceptance'],checks=checks,products=rows,evidence_references=[r['evidence'] for r in runs]+[reference['evidence']],scope=profile['scope'])
    write(e.path/'result.json',result);result['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks));write(REPORT,result)
    record('IMG-01','当前resize实际68件JPEG独立数学/严格熵/CPU全图质量验收：'+status+'，完成'+str(len(rows))+'/68；原始postprocess像素检查与生产GPU trace分别引用，保留两入口PARTIAL。',[result['evidence']]);print(status,[c for c in checks if not c['passed']]);return int(status!='PASSED')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','run','negative']);a=p.parse_args();raise SystemExit(globals()[a.action]())
