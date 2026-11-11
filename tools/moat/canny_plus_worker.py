#!/usr/bin/env python3
"""Actual Torch/C ABI worker; all expected pixels are checked outside this process."""
import argparse,ctypes,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'rocm/python'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np,torch
from image.canny import CannyEdgeDetector
from experiment import ROOT,write,digest

def main():
 p=argparse.ArgumentParser();p.add_argument('--profile',required=True);p.add_argument('--library',required=True);p.add_argument('--expected-sha',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 library=Path(a.library);assert digest(library)==a.expected_sha
 spec=json.loads(Path(a.profile).read_text());out=Path(a.output);out.mkdir(parents=True)
 detector=CannyEdgeDetector(library);rows=[]
 for case in spec['cases']:
  fixture=ROOT/case['fixture'];assert digest(fixture/'manifest.json')==case['manifest_sha256']
  manifest=json.loads((fixture/'manifest.json').read_text())
  assert all(digest(fixture/n)==r['sha256'] and (fixture/n).stat().st_size==r['bytes'] for n,r in manifest['files'].items())
  c=json.loads((fixture/'config.json').read_text());w,h=c['width'],c['height'];d=out/case['case'];d.mkdir()
  data=np.fromfile(fixture/'input.bin',np.uint8).reshape(h,c['pitch']);source=torch.from_numpy(data).cuda();output=torch.full((h,c['output_pitch']),173,dtype=torch.uint8,device='cuda')
  size=ctypes.c_uint64();assert detector.size(w,h,ctypes.byref(size))==0;workspace=torch.empty(size.value,dtype=torch.uint8,device='cuda');stream=torch.cuda.current_stream()
  status=detector.call(source.data_ptr(),source.numel(),source.stride(0),w,h,1,c['low'],c['high'],output.data_ptr(),output.numel(),output.stride(0),workspace.data_ptr(),workspace.numel(),stream.cuda_stream)
  if status:raise RuntimeError('C ABI status '+str(status)+' case '+case['case'])
  torch.cuda.synchronize();output.cpu().numpy().tofile(d/'pitched.bin')
  actual=detector(source[:,:w],c['low'],c['high']);actual.cpu().numpy().tofile(d/'python.bin')
  after=source.cpu().numpy();assert np.array_equal(after,data)
  row=dict(case=case['case'],input_manifest_sha256=case['manifest_sha256'],GPU_input_sha256=digest(fixture/'input.bin'),width=w,height=h,source_pitch=c['pitch'],output_pitch=c['output_pitch'],library_sha256=digest(library),outputs={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in d.iterdir()});rows.append(row);write(out/'results.json',rows);print(case['case'],flush=True)
 return 0
if __name__=='__main__':raise SystemExit(main())
