#!/usr/bin/env python3
"""Independent FP64 FFT correlation and integral-moment NCC oracle."""
import argparse,json,re,sys
from pathlib import Path
from experiment import ROOT,write
sys.path.insert(0,str(ROOT/'build/python-reference'))
import numpy as np

def validate(out,log):
 c=np.fromfile(out/'config.bin',np.int32);W,H,tx,ty,tw,th,iterations,bestx,besty=map(int,c);image=np.fromfile(out/'input.bin',np.uint8).reshape(H,W);tpl=np.fromfile(out/'template.bin',np.uint8).reshape(th,tw);actual=np.fromfile(out/'scores.bin',np.float32).reshape(H-th+1,W-tw+1);checks=[]
 def gate(name,value,**fields):checks.append(dict(check=name,passed=bool(value),**fields))
 def moments(x):
  s=np.pad(x.astype(np.float64).cumsum(0).cumsum(1),((1,0),(1,0)));return s[th:,tw:]-s[:-th,tw:]-s[th:,:-tw]+s[:-th,:-tw]
 sa=moments(image);saa=moments(image.astype(np.float64)**2);sb=float(tpl.sum());sbb=float((tpl.astype(np.float64)**2).sum());count=tw*th;aa=count*saa-sa*sa;bb=count*sbb-sb*sb
 shape=(1<<(H+th-2).bit_length(),1<<(W+tw-2).bit_length())
 cross=np.fft.irfftn(np.fft.rfftn(image,s=shape,axes=(0,1))*np.fft.rfftn(tpl[::-1,::-1],s=shape,axes=(0,1)),s=shape,axes=(0,1))[th-1:H,tw-1:W]
 degenerate=(aa<=0)|(bb<=0);expected=np.full(actual.shape,np.finfo(np.float32).max if bb<=0 else 0,dtype=np.float64)
 good=~degenerate
 if good.any():expected[good]=(count*cross[good]-sa[good]*sb)/np.sqrt(aa[good]*bb)
 delta=np.abs(actual[good].astype(np.float64)-expected[good]);gate('independent-full-FP64-correlation',np.isfinite(actual).all() and np.all(delta<=2e-4),elements=int(actual.size),max_abs=float(delta.max(initial=0)),atol=2e-4)
 gate('native-observed-zero-variance-policy',np.all(actual[degenerate]==np.finfo(np.float32).max) if bb<=0 else np.all(np.abs(actual[degenerate])<=2e-4),elements=int(np.count_nonzero(degenerate)))
 gate('GPU-argmax-is-global-maximum',0<=bestx<actual.shape[1] and 0<=besty<actual.shape[0] and actual[besty,bestx]==actual.max())
 marked=image.copy();marked[besty,bestx:bestx+tw]=255;marked[besty+th-1,bestx:bestx+tw]=255;marked[besty:besty+th,bestx]=255;marked[besty:besty+th,bestx+tw-1]=255
 expected_pgm=f'P5\n{W} {H}\n255\n'.encode()+marked.tobytes();gate('PGM-header-box-and-untouched-pixels-exact',(out/'match_result.pgm').read_bytes()==expected_pgm)
 text=Path(log).read_text()
 if iterations==0:gate('zero-iteration-timing-skip','Timing skipped (-n 0)' in text)
 else:
  found=re.search(r'([0-9.]+) ms per match \(average of (\d+) runs\)',text);gate('GPU-event-timing-reported',bool(found) and float(found[1])>0 and int(found[2])==iterations)
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,oracle='FP64 FFT cross-correlation plus integral moments; native-observed undefined-variance sentinel; exact PGM pixels',config=c.tolist())

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--log',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();r=validate(a.output,a.log);write(a.report,r);print(json.dumps(r));raise SystemExit(r['status']!='PASSED')
