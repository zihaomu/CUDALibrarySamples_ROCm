#!/usr/bin/env python3
"""Compare the unchanged native C++ PNG workflow against its native API oracle."""
import json
import cv2,numpy as np
from experiment import ROOT,Experiment,write,digest
from image_validation import file_set,array_check
from image_progress import record

def validate(run):
 profile=json.loads((ROOT/'migration/rewrite/canny-color-profile.json').read_text());case=next(c for c in profile['cases'] if c['case']=='original-teapot');f=ROOT/case['fixture'];c=json.loads((f/'config.json').read_text());h,w=c['height'],c['width'];row=next(r for r in json.loads((ROOT/'migration/reports/canny-color-native.json').read_text()) if r['case']=='original-teapot');native=np.fromfile(ROOT/row['outputs']/'output.bin',np.uint8).reshape(h,c['output_pitch'])[:,:w];image=np.fromfile(f/'input.bin',np.uint8).reshape(h,c['pitch'])[:,:3*w].reshape(h,w,3);gray=cv2.Canny(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY),50,100,L2gradient=True);channels=cv2.split(image);merged=cv2.bitwise_or(cv2.Canny(channels[0],50,100,L2gradient=True),cv2.bitwise_or(cv2.Canny(channels[1],50,100,L2gradient=True),cv2.Canny(channels[2],50,100,L2gradient=True)));out=ROOT/run['outputs'];checks=[dict(check='unmodified-original-CUDA-process-success',passed=run['return_code']==0),file_set(out,['edges_npp.png','edges_opencv_gray.png','edges_opencv_3ch.png'])]
 for name,expected in [('edges_npp.png',native),('edges_opencv_gray.png',gray),('edges_opencv_3ch.png',merged)]:
  actual=cv2.imread(str(out/name),cv2.IMREAD_UNCHANGED);checks.append(dict(check=name+'/all-original-native-pixels',passed=actual is not None and actual.shape==expected.shape and actual.dtype==np.uint8 and np.array_equal(actual,expected)))
 return dict(status='PASSED' if all(c['passed'] is True for c in checks) else 'FAILED',checks=checks,scope='Original C++ native NPP output matches the separately run native NPP API; project classical hysteresis variant has its own explicitly reported differences.')

def main():
 run=json.loads((ROOT/'migration/reports/canny-color-original-cuda-cpp.json').read_text());e=Experiment('I1','C3-Canny-original-CUDA-file-verification','CPU-reference',sources=[__file__,ROOT/'NPP/nppCanny/npp_canny_simple.cpp',ROOT/'migration/rewrite/canny-color-profile.json',ROOT/'tools/moat/image_validation.py'],parent=run['experiment_id'])
 try:v=validate(run)
 except Exception as error:v=dict(status='FAILED',checks=[dict(check='complete-original-native-files',passed=False,error=repr(error))])
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NATIVE_MISMATCH',v);v['parent']=run['evidence'];write(ROOT/'migration/reports/canny-color-original-cuda-validation.json',v);record('I1','原始CUDA C++三张PNG对独立native NPP API及OpenCV完整像素验收：'+v['status']+'；项目经典变体差异保持单列。',[v['evidence']]);print(v['status'],[c for c in v['checks'] if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
