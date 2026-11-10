#!/usr/bin/env python3
"""Compare genuine NPP outputs separately, preserving semantic differences and tie freedom."""
import json,pathlib
from catalog import ROOT
from run import digest,evidence_directory
from validate_blas import np
from batches12_15_spec import kind
native=json.loads((ROOT/'migration/reports/batch15-native-npp.json').read_text());amd=json.loads((ROOT/'migration/reports/batches12_15-rocm.json').read_text());rows=[]
for c in native['runs']:
 r=next(r for r in amd if kind(r['source'])==c['kind']);d=evidence_directory(next(x['evidence'] for x in r['runs'] if x['case']==c['case']));nd=evidence_directory(c['evidence']);row=dict(c,source=r['source'],amd_evidence=str(d.relative_to(ROOT)),implementation_sha256=r['implementation_sha256'],helper_sha256=digest(ROOT/'rocm/common/batch15_image.hpp'),native_source_sha256=native['source_sha256'],comparisons=[])
 if c['return_code']:row['status']='NATIVE_API_REJECTED';rows.append(row);continue
 yes=True
 for file in sorted(nd.glob('*_output.bin')):
  ident=file.name.split('_')[0];p=np.fromfile(d/(ident+'_params.bin'),np.int32);W,H,C,stride,rx,ry,w,h=p[:8];a=np.fromfile(d/file.name,np.uint8 if c['kind']=='canny' else np.float32);b=np.fromfile(file,np.uint8 if c['kind']=='canny' else np.float32)
  if c['kind']=='canny':a=a.reshape(h,w+5)[:,:w].ravel()
  delta=np.abs(a.astype(np.float64)-b);tolerance=0 if c['kind'] in ['canny','distance'] else 2e-4;passed=bool(np.isfinite(a).all() and np.isfinite(b).all() and np.all(delta<=tolerance));detail=dict(file=file.name,max_abs=float(delta.max(initial=0)),different=int(np.count_nonzero(delta)),elements=int(delta.size),absolute_tolerance=tolerance,passed=passed)
  if c['kind']=='distance':
   x=np.fromfile(d/(ident+'_truncated.bin'),np.uint16);y=np.fromfile(nd/(ident+'_truncated.bin'),np.uint16);detail['integer_truncation_exact']=bool(np.array_equal(x,y));pa=np.fromfile(d/(ident+'_voronoi.bin'),np.int16).reshape(h,w,2);pb=np.fromfile(nd/(ident+'_voronoi.bin'),np.int16).reshape(h,w,2);detail['voronoi_direct_differences']=int(np.count_nonzero(pa!=pb));raw=np.fromfile(d/(ident+'_input.bin'),np.uint8).reshape(H,stride)[:,:W].reshape(H,W)[ry:ry+h,rx:rx+w];yy,xx=np.indices((h,w));bounds=True
   for label,v in [('amd',pa),('native',pb)]:
    sx=xx-v[:,:,0];sy=yy-v[:,:,1];valid=bool(np.all((sx>=0)&(sx<w)&(sy>=0)&(sy<h)));valid=bool(valid and np.all(raw[sy,sx]==0) and np.allclose(np.sqrt((xx-sx)**2+(yy-sy)**2),b.reshape(h,w),rtol=2e-6,atol=1e-6));detail[label+'_displacement_is_valid_nearest_site']=valid;bounds&=valid
   passed=passed and detail['integer_truncation_exact'] and bounds;detail['passed']=bool(passed)
  yes&=passed;row['comparisons'].append(detail)
 row['status']='PASSED' if yes else 'DIFFERENT';rows.append(row);print(c['kind'],c['case'],row['status'],flush=True)
report=dict(scope='Genuine NPP APIs on identical bytes; original sizes required for native PBA; native small/empty API rejections remain explicit. Voronoi fields are pixel-minus-site displacement, ties accept any actual nearest site.',generator_sha256=digest(pathlib.Path(__file__)),native_probe_source_sha256=native['source_sha256'],rows=rows)
(ROOT/'migration/reports/batch15-native-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
