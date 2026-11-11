#!/usr/bin/env python3
"""Actual C3 pitched C ABI, GPU tensor and original NumPy public API calls."""
import argparse,ctypes,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'rocm/python'))
import numpy as np,torch
from image.canny_color import NPPCanny
from experiment import ROOT,write,digest

def main():
 p=argparse.ArgumentParser();p.add_argument('--library',type=Path,required=True);p.add_argument('--expected-sha',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert digest(a.library)==a.expected_sha
 detector=NPPCanny(a.library);spec=json.loads((ROOT/'migration/rewrite/canny-color-profile.json').read_text());a.output.mkdir(parents=True);rows=[]
 for case in spec['cases']:
  d=ROOT/case['fixture'];assert digest(d/'manifest.json')==case['manifest_sha256'];manifest=json.loads((d/'manifest.json').read_text());assert all(digest(d/n)==v['sha256'] and (d/n).stat().st_size==v['bytes'] for n,v in manifest['files'].items());c=json.loads((d/'config.json').read_text());h,w=c['height'],c['width'];out=a.output/case['case'];out.mkdir();data=np.fromfile(d/'input.bin',np.uint8).reshape(h,c['pitch']);source=torch.from_numpy(data).cuda();target=torch.full((h,c['output_pitch']),173,dtype=torch.uint8,device='cuda');size=ctypes.c_uint64();assert detector.size(w,h,ctypes.byref(size))==0;workspace=torch.empty(size.value,dtype=torch.uint8,device='cuda');stream=torch.cuda.current_stream()
  rc=detector.call(source.data_ptr(),source.numel(),c['pitch'],w,h,c['low'],c['high'],target.data_ptr(),target.numel(),c['output_pitch'],workspace.data_ptr(),workspace.numel(),stream.cuda_stream)
  if rc:raise RuntimeError('C3 C ABI status '+str(rc)+' '+case['case'])
  target.cpu().numpy().tofile(out/'pitched.bin');detector.tensor(source[:,:3*w].reshape(h,w,3),c['low'],c['high']).cpu().numpy().tofile(out/'tensor.bin');detector.detect(data[:,:3*w].reshape(h,w,3),c['low'],c['high']).tofile(out/'numpy.bin');assert np.array_equal(source.cpu().numpy(),data)
  rows.append(dict(case=case['case'],input_manifest_sha256=case['manifest_sha256'],library_sha256=a.expected_sha,width=w,height=h,files={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in out.iterdir()}));write(a.output/'results.json',rows);print(case['case'],flush=True)
 return 0
if __name__=='__main__':raise SystemExit(main())
