#!/usr/bin/env python3
"""Freeze complete Hough sample entry points before implementing a HIP backend."""
import json
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_progress import record

SOURCE='NPP/houghLines/houghLines.cpp'
SAMPLE='NPP/houghLines::houghLines.cpp'
PROFILE=ROOT/'migration/rewrite/image-hough-profile.json'
FIXTURES=ROOT/'tests/fixtures/image-hough'

def raw_images():
    h,w=192,256
    blank=np.full((h,w),40,dtype=np.uint8)
    cross=blank.copy();cross[47:50,:]=220;cross[:,126:129]=220
    diagonal=blank.copy()
    yy,xx=np.indices((h,w));diagonal[np.abs(yy-(xx*3//4+7))<=1]=220
    noise=np.random.default_rng(771183).integers(37,44,size=(h,w),dtype=np.uint8)
    noise[47:50,:]=220;noise[:,126:129]=220
    odd=np.full((17,19),40,dtype=np.uint8);odd[8:11,:]=220
    return {'blank':blank,'cross':cross,'diagonal':diagonal,'noise-cross':noise,'odd-line':odd}

def main():
    native=next(x for x in json.loads((ROOT/'migration/reports/image-I3-native-originals.json').read_text())
                if x['source']==SOURCE)
    if native['status']!='EXECUTED' or native['return_code']!=0 or native['build_return_code']!=0:
        raise ValueError('complete CUDA original baseline required')
    FIXTURES.mkdir(parents=True,exist_ok=True)
    cases=[]
    for name,image in raw_images().items():
        path=FIXTURES/(name+'.raw');data=image.tobytes();path.write_bytes(data)
        h,w=image.shape
        cases.append(dict(case='raw-'+name,kind='valid',arguments=['-i',str(path.relative_to(ROOT)),'-w',str(w),'-h',str(h),'-n','0'],
                          width=w,height=h,input=str(path.relative_to(ROOT)),bytes=len(data),sha256=digest(path),
                          products=['hough_result.ppm','stdout'],expected_return_code=0))
    cases += [
        dict(case='synthetic-default',kind='valid',arguments=[],width=1024,height=768,
             products=['hough_result.ppm','stdout','GPU Canny timing','GPU Hough timing'],expected_return_code=0),
        dict(case='synthetic-no-timing',kind='valid',arguments=['-n','0'],width=1024,height=768,
             products=['hough_result.ppm','stdout'],expected_return_code=0),
        dict(case='invalid-width',kind='invalid',arguments=['-w','15'],expected_return_code=1),
        dict(case='invalid-height',kind='invalid',arguments=['-h','16385'],expected_return_code=1),
        dict(case='invalid-threshold',kind='invalid',arguments=['-t','0'],expected_return_code=1),
        dict(case='invalid-lines',kind='invalid',arguments=['-m','0'],expected_return_code=1),
        dict(case='invalid-canny',kind='invalid',arguments=['-cl','121','-ch','120'],expected_return_code=1),
        dict(case='truncated-raw',kind='invalid',arguments=['-i','tests/fixtures/image-hough/odd-line.raw','-w','19','-h','18','-n','0'],expected_return_code=1),
        dict(case='help',kind='help',arguments=['--help'],expected_return_code=0),
    ]
    profile=dict(status='FROZEN',sample_id=SAMPLE,source=SOURCE,source_sha256=digest(ROOT/SOURCE),
                 native_original_evidence=native['evidence'],comparison_mode='DOCUMENTED_HOUGH_ACCUMULATOR_VARIANT',
                 image_contract='Complete 8-bit C1 synthetic or exact RAW; project GPU Canny then GPU rho/theta voting and peak selection; deterministic line list, truth coverage and exact PPM reproduction against independent CPU project oracle.',
                 rho_step_pixels=1,theta_step_degrees=1,theta_bins=180,
                 truth=[[-150,30],[80,100],[200,75],[-60,160],[0,45]],
                 default=dict(width=1024,height=768,threshold=300,max_lines=500,iterations=50,canny_low=60,canny_high=120),
                 cases=cases,case_count=len(cases))
    e=Experiment('I3','Hough-full-entry-contract','CPU-contract',sources=[__file__,ROOT/SOURCE,ROOT/'migration/reports/image-I3-native-originals.json'])
    write(PROFILE,profile);write(e.path/'profile.json',profile)
    result=dict(status='FROZEN',case_count=len(cases),valid=sum(c['kind']=='valid' for c in cases),
                invalid=sum(c['kind']=='invalid' for c in cases),native_evidence=native['evidence'])
    write(e.path/'contracts.json',result)
    result['evidence']=e.finish('OBSERVED',dict(status='FROZEN',checks=[dict(check='source-and-complete-CUDA-original',passed=True),dict(check='unique-fixed-cases-and-raw-bytes',passed=len({c['case'] for c in cases})==len(cases))]))
    write(ROOT/'migration/reports/image-hough-contracts.json',result)
    record('I3',f'Hough完整入口合同{len(cases)}项冻结：两种完整synthetic、五种固定RAW、非法参数/短文件/help；原生5090完整原例及产品已封存。项目GPU Canny/Hough算法变体待实现与独立CPU核验。',[result['evidence'],native['evidence']])
    print(json.dumps(result))

if __name__=='__main__':main()
