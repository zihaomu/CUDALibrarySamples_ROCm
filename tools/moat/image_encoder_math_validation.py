#!/usr/bin/env python3
"""Full local transform and entropy validation under the frozen variant."""
import json
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_encoder_math_oracle import color,coefficient_checks,precision_check
from image_jpeg_baseline_entropy_reference import decode as entropy_decode
from image_jpeg_reference_modes import loaded_library_check

PROFILE=ROOT/'migration/rewrite/image-encoder-math-variant-v2-profile.json'

def strict_reference_build():
    source=ROOT/'rocm/probes/image/jpeg_cpu_coefficients_strict.cpp';jpeg=ROOT/'build/cpu-codecs';lib=jpeg/'lib/libjpeg.so.62.4.0'
    e=Experiment('I5','encoder-math-strict-CPU-reference','CPU-build',sources=[__file__,PROFILE,source,jpeg/'include/jpeglib.h',lib,ROOT/'tools/moat/image_encoder_math_oracle.py'])
    binary=e.path/'coefficients';rc=e.command(['c++','-std=c++17','-O2','-I'+str(jpeg/'include'),str(source),'-o',str(binary),'-L'+str(jpeg/'lib'),'-Wl,-rpath,'+str(jpeg/'lib'),'-ljpeg','-ldl'],'build-strict-coefficient-reference')
    precision=precision_check();checks=[dict(check='build',passed=rc==0),dict(check='80-digit-oracle-crosscheck',**precision)]
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(status=status,checks=checks,binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary) if binary.exists() else None,library=str(lib.relative_to(ROOT)),library_sha256=digest(lib))
    write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'PROBE_FAILED',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-math-reference-build.json',row)
    record('IMG-01','独立严格CPU系数参考及576频率/80位Decimal校验：'+status+'；maxAbs='+str(precision['max_abs'])+'。',[row['evidence']])
    if status!='PASSED':raise ValueError('strict reference build/precision failed')
    return row

def validate(e,rgb,case,jpeg,probe,reference,profile):
    if digest(ROOT/reference['binary'])!=reference['binary_sha256'] or digest(ROOT/reference['library'])!=reference['library_sha256']:raise ValueError('strict CPU reference drift')
    rc=e.command([str(ROOT/reference['binary']),str(jpeg)],'independent-strict-CPU-coefficients')
    checks=[dict(check='independent-full-coefficient-read-zero-warnings',passed=rc==0)]
    loaded=loaded_library_check(e,e.commands[-1],dict(dependencies={reference['library']:reference['library_sha256']}));checks.append(loaded)
    decoded=json.loads((e.path/e.commands[-1]['stdout']).read_text());strict=entropy_decode(jpeg.read_bytes())
    h,w=rgb.shape[:2];s=case['sampling'];mx=(w+8*s-1)//(8*s);my=(h+8*s-1)//(8*s)
    checks.append(dict(check='strict-frame-dimensions',passed=(strict['width'],strict['height'],strict['sampling'])==(w,h,s) and (decoded['width'],decoded['height'],len(decoded['components']))==(w,h,3)))
    products={(a['kind'],a['channel']):a for a in probe['products']}
    if len(products)!=6 or len(probe['products'])!=6:raise ValueError('exact GPU array set required')
    arrays={};details=[];expected_keys=set();expected_dummy=0
    for c in range(3):
        plane=color(rgb,c,s);ph,pw=plane.shape;bh,bw=(ph+7)//8,(pw+7)//8
        for kind,shape,dtype in [('color',(ph,pw),np.uint8),('coeff',(bh,bw,8,8),'<i2')]:
            product=products[kind,c];path=ROOT/product['path']
            if digest(path)!=product['sha256'] or path.stat().st_size!=product['bytes']:raise ValueError('GPU array drift')
            arrays[kind,c]=np.fromfile(path,dtype=dtype).reshape(shape)
        checks.append(dict(check=f'all-color-pixels-exact-{c}',passed=np.array_equal(plane,arrays['color',c]),pixels=int(plane.size)))
        component=decoded['components'][c];quant=component['quant'];code=arrays['coeff',c]
        if (component['width_blocks'],component['height_blocks'])!=(bw,bh):raise ValueError('CPU component geometry')
        checks.append(dict(check=f'complete-JPEG-valid-coefficients-exact-GPU-{c}',passed=np.array_equal(np.array(component['coefficients']).reshape(code.shape),code),coefficients=int(code.size)))
        mathematical=coefficient_checks(plane,code,quant,profile['mathematics']['absolute_DCT_error_budget']);details.append(dict(channel=c,**mathematical))
        checks.append(dict(check=f'every-coefficient-independent-mathematics-{c}',passed=mathematical['passed']))
        checks.append(dict(check=f'independent-parser-DQT-{c}',passed=strict['quant'][strict['components'][c]['quant']]==quant))
        scale=s if c==0 else 1
        for by in range(my*scale):
            for bx in range(mx*scale):
                expected_keys.add((c,bx,by));expected_dummy+=int(bx>=bw or by>=bh)
    seen=set();equal=True;dummy=0;first_differences=[]
    for block in strict['blocks']:
        c,x,y=block['channel'],block['x'],block['y'];key=(c,x,y)
        if key in seen:raise ValueError('duplicate entropy block')
        seen.add(key);array=arrays['coeff',c]
        expected=array[y,x].ravel().tolist() if y<array.shape[0] and x<array.shape[1] else [0]*64
        dummy+=int(y>=array.shape[0] or x>=array.shape[1])
        if block['coefficients']!=expected:
            equal=False
            if len(first_differences)<10:first_differences.append(dict(key=key,expected=expected,actual=block['coefficients']))
    checks.append(dict(check='complete-MCU-positions-and-zero-padding-coefficients',passed=seen==expected_keys and equal and dummy==expected_dummy,blocks=len(seen),dummy_blocks=dummy))
    return checks,dict(components=details,strict_entropy=dict(bytes=strict['entropy_bytes'],pad_bits=strict['pad_bits'],MCU_blocks=len(seen),dummy_blocks=dummy,first_differences=first_differences))
