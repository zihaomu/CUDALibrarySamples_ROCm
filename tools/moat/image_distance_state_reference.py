#!/usr/bin/env python3
"""Independent complete storage checks for distance state transitions."""
import hashlib
import numpy as np
from image_distance_model import model

FORMATS={'distance':('<f8',1,167,40),'visualization':('<u2',1,185,18),'indices':('<i2',2,171,20),'relative':('<i2',2,173,28),'site_ids':('<u8',1,205,24),'sites_xy':('<f8',2,221,32)}
def initial(case,payload):
 w,h=case['width'],case['height'];return dict(src=payload,work=bytes([211])*(80*w*h+8),**{k:bytes([pad])*(h*(w*np.dtype(dtype).itemsize*channels+extra)) for k,(dtype,channels,pad,extra) in FORMATS.items()})
def hashes(blobs):return {k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}
def read_state(path,case):
 names={'src','work',*FORMATS}
 if {p.name for p in path.iterdir()}!={n+'.bin' for n in names}:raise ValueError('all eight complete state buffers')
 result={n:(path/(n+'.bin')).read_bytes() for n in names};w,h=case['width'],case['height'];lengths=initial(case,bytes(h*case['pitch']))
 if any(len(result[n])!=len(b) for n,b in lengths.items()):raise ValueError('exact state buffer lengths')
 return result
def check_values(blobs,case,payload,disabled=(),rejected=False):
 w,h=case['width'],case['height'];expected_initial=initial(case,payload);checks=[dict(check='complete-frozen-input-and-padding',passed=blobs['src']==payload)]
 math=None
 if not rejected:
  item=np.dtype(case['dtype']).itemsize;a=np.frombuffer(payload,np.uint8).reshape(h,case['pitch'])[:,:w*item].copy().view(case['dtype']).reshape(h,w);math=model(a,case['mode'],case['cutoff'],case['remap_circle'])
 for key,(dtype,channels,pad,extra) in FORMATS.items():
  if rejected or key in disabled:checks.append(dict(check=key+'/rejected-or-disabled-storage-preserved',passed=blobs[key]==expected_initial[key]));continue
  dt=np.dtype(dtype);pitch=w*channels*dt.itemsize+extra;raw=np.frombuffer(blobs[key],np.uint8).reshape(h,pitch);a=raw[:,:w*channels*dt.itemsize].copy().view(dt).reshape((h,w) if channels==1 else(h,w,channels));b=math[key];okay=np.array_equal(a,b)
  if key=='distance':
   finite=np.isfinite(b);okay=not np.any(np.isnan(a)) and np.array_equal(np.isfinite(a),finite) and np.array_equal(np.isposinf(a),np.isposinf(b)) and np.array_equal(np.isneginf(a),np.isneginf(b)) and np.array_equal(np.signbit(a),np.signbit(b)) and np.array_equal(a==0,b==0) and np.all(np.abs(a[finite]-b[finite])<=2e-11+1e-12*np.abs(b[finite]))
  checks.extend([dict(check=key+'/all-actual-values',passed=bool(okay)),dict(check=key+'/all-row-padding',passed=bool(np.all(raw[:,w*channels*dt.itemsize:]==pad)))])
 return checks
def descriptor(case,actual,disabled=()):
 w,h=case['width'],case['height'];expected=dict(width=w,height=h,input_pitch=case['pitch'],workspace_bytes=80*w*h+8,cutoff=case['cutoff'],mode=case['mode'],input_type=case['input_type'],remap_circle=case['remap_circle'],reserved=0)
 for key,(dtype,channels,pad,extra) in FORMATS.items():expected[key+'_pitch']=0 if key in disabled else w*np.dtype(dtype).itemsize*channels+extra
 okay=all(actual[k]==v for k,v in expected.items()) and all(actual[k] is None for k in disabled)
 for k in ['input','workspace','distance',*FORMATS]:
  if k in disabled:continue
  alignment=np.dtype(case['dtype']).itemsize if k=='input' else 8 if k in ['workspace','distance','site_ids','sites_xy'] else 2;okay=okay and isinstance(actual[k],int) and actual[k]>0 and actual[k]%alignment==0
 return dict(check='actual-complete-descriptor-and-optional-pointer-contract',passed=bool(okay))
def spans(case,actual):
 initial_blobs=initial(case,bytes(case['height']*case['pitch']));return [(actual['input' if k=='src' else 'workspace' if k=='work' else k],len(v)) for k,v in initial_blobs.items()]
