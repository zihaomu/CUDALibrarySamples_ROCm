#!/usr/bin/env python3
"""Record the complete original CUDA and project HIP Hough output difference."""
import json,re
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_progress import record
from image_hough_reference import LINE,TRUTH

def lines(text):return [(int(float(rho)),int(float(theta))) for theta,rho in LINE.findall(text)]

def main():
    native=next(r for r in json.loads((ROOT/'migration/reports/image-I3-native-originals.json').read_text())
                if r['source']=='NPP/houghLines/houghLines.cpp')
    project=next(r for r in json.loads((ROOT/'migration/reports/image-hough-runs.json').read_text())
                 if r['case']=='synthetic-default')
    validations=json.loads((ROOT/'migration/reports/image-hough-validation.json').read_text())
    if len(validations)!=14 or any(v['status']!='PASSED' for v in validations):raise ValueError('all project CPU validations required')
    nd=ROOT/native['evidence'];pd=ROOT/project['evidence']
    nbytes=(ROOT/native['outputs']/'work/hough_result.ppm').read_bytes()
    pbytes=(ROOT/json.loads((pd/'manifest.json').read_text())['raw_artifact_dir']/'outputs/hough_result.ppm').read_bytes()
    nlines=lines((nd/'logs/0005-actual-complete-native-default-with-source-input-library-GPU-receipt.stdout.log').read_text())
    plines=lines((pd/'logs/0001-execute-complete-Hough-entry.stdout.log').read_text())
    header=b'P6\n1024 768\n255\n'
    if not nbytes.startswith(header) or not pbytes.startswith(header) or len(nbytes)!=len(pbytes):raise ValueError('complete RGB PPM shape')
    n=np.frombuffer(nbytes[len(header):],np.uint8).reshape(768,1024,3)
    p=np.frombuffer(pbytes[len(header):],np.uint8).reshape(768,1024,3)
    npix=np.all(n==[255,40,40],axis=2);ppix=np.all(p==[255,40,40],axis=2)
    overlap=int(np.count_nonzero(npix&ppix));union=int(np.count_nonzero(npix|ppix))
    result=dict(status='PASSED',native_lines=nlines,project_lines=plines,
                native_line_count=len(nlines),project_line_count=len(plines),
                differing_RGB_pixels=int(np.count_nonzero(np.any(n!=p,axis=2))),
                red_line_IoU=overlap/union if union else 1.,
                native_red_pixels=int(np.count_nonzero(npix)),project_red_pixels=int(np.count_nonzero(ppix)),
                native_ppm_sha256=digest(ROOT/native['outputs']/'work/hough_result.ppm'),
                project_ppm_sha256=digest(ROOT/json.loads((pd/'manifest.json').read_text())['raw_artifact_dir']/'outputs/hough_result.ppm'),
                comparison_mode='DOCUMENTED_HOUGH_ACCUMULATOR_VARIANT',
                scope='Default complete synthetic original only; no vendor-exact line or performance claim.',
                native_evidence=native['evidence'],project_evidence=project['evidence'])
    checks=[dict(check='unmodified-real-native-CUDA-exit-and-product',passed=native['return_code']==native['build_return_code']==native['collection_return_code']==0 and result['native_ppm_sha256']==native['files']['work/hough_result.ppm']['sha256']),
            dict(check='project-complete-PPM-and-independent-CPU',passed=result['project_ppm_sha256']==project['ppm_sha256'] and all(v['status']=='PASSED' for v in validations)),
            dict(check='same-ten-geometric-lines-and-truth',passed=len(nlines)==len(plines)==10 and all(any(abs(r-r0)<=3 and abs(t-t0)<=1 for r,t in a) for a in (nlines,plines) for r0,t0 in TRUTH))]
    result['status']='PASSED' if all(c['passed'] for c in checks) else 'FAILED'
    e=Experiment('I3','Hough-complete-native-CUDA-project-HIP-CPU-comparison','CPU-reference',
                 sources=[__file__,ROOT/'migration/rewrite/image-hough-profile.json',
                 ROOT/'migration/reports/image-hough-runs.json',ROOT/'migration/reports/image-hough-validation.json'])
    write(e.path/'comparison.json',result)
    result['evidence']=e.finish('PASSED' if result['status']=='PASSED' else 'NATIVE_MISMATCH',dict(status=result['status'],checks=checks))
    write(ROOT/'migration/reports/image-hough-native-comparison.json',result)
    record('I3','Hough 5090原生与项目HIP完整默认PPM/10线差异：'+result['status']+'；'+str(result['differing_RGB_pixels'])+' RGB像素不同、red IoU '+str(round(result['red_line_IoU'],5))+'；双方五真值均覆盖，完整原始产物封存。',[result['evidence'],native['evidence']])
    print(result['status'],result['differing_RGB_pixels'],result['red_line_IoU'])
    return int(result['status']!='PASSED')

if __name__=='__main__':raise SystemExit(main())
