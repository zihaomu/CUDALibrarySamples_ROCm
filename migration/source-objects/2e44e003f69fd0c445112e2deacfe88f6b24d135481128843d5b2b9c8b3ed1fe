#!/usr/bin/env python3
"""Freeze stream/state/optional-output roles and extreme numeric byte fixtures."""
import json
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def main():
 e=Experiment('I2','Distance-state-and-extreme-numeric-contracts','CPU-contract',sources=[__file__,ROOT/'migration/rewrite/image-distance-profile.json']);base=ROOT/'build/image-distance-state-fixtures';numeric={}
 def add(name,a,rc=0,remap=0):
  h,w=a.shape;dtype=a.dtype.newbyteorder('<');a=np.asarray(a,dtype=dtype);pitch=w*dtype.itemsize+24;blob=np.full((h,pitch),197,np.uint8);blob[:,:w*dtype.itemsize]=a.view(np.uint8).reshape(h,w*dtype.itemsize);d=base/name;d.mkdir(parents=True,exist_ok=True);blob.tofile(d/'input.bin');cfg=dict(case=name,width=w,height=h,pitch=pitch,dtype=dtype.str,input_type=1 if dtype.itemsize==4 else 2,mode=1,cutoff=0.,remap_circle=remap);write(d/'config.json',cfg);write(d/'manifest.json',dict(files={n:dict(bytes=(d/n).stat().st_size,sha256=digest(d/n)) for n in ['input.bin','config.json']}));numeric[name]=dict(**cfg,fixture=str(d.relative_to(ROOT)),manifest_sha256=digest(d/'manifest.json'),return_code=rc)
 add('extreme-float64',np.array([[-1e308,1e308,-5e-324,5e-324,0.]],np.float64));add('subnormal-float32',np.array([[-1e-45,1e-45,0.,-1.,1.]],np.float32));add('single-negative-subnormal64',np.array([[-5e-324]],np.float64));add('single-positive-subnormal64',np.array([[5e-324]],np.float64));add('maximum-width-and-negative-relative',np.arange(32768,dtype=np.float64)[None,:]-32767.);add('maximum-height-and-negative-relative',np.arange(32768,dtype=np.float64)[:,None]-32767.)
 for dtype in [np.float32,np.float64]:
  for label,value in [('NaN',np.nan),('positive-Inf',np.inf),('negative-Inf',-np.inf)]:add(label+'-'+np.dtype(dtype).name,np.array([[value,1.,-1.]],dtype),1)
 add('nonfinite-effective-circle-remap',np.array([[1.7e308]],np.float64),1,1)
 rows=[]
 def role(name,kind,source,state,change='original',rc=0,disabled=()):rows.append(dict(case=name,kind=kind,source_case=source,state=state,input_change=change,return_code=rc,disabled_outputs=list(disabled)))
 source='signed-independent-noise-773971'
 for name,change in [('default-original','original'),('repeat-default-original','original'),('changed-zero-logical','zero-logical'),('restored-original','original')]:role(name,'default',source,'A',change)
 role('concurrent-Lith','concurrent','signed-lith-original','B');role('concurrent-circle','concurrent','signed-circle-original','C')
 role('foreign-stream','foreign',source,'A',rc=101);role('destroyed-stream','destroyed',source,'A',rc=709)
 optional=['visualization','indices','relative','site_ids','sites_xy']
 for output in optional:role('optional-'+output,'optional',source,'D',disabled=[output])
 role('optional-all','optional',source,'D',disabled=optional)
 for name,c in numeric.items():role('numeric-'+name,'numeric',name,'numeric-'+name,rc=c['return_code'])
 v=dict(schema_version=1,status='FROZEN',cases=rows,case_count=len(rows),numeric_cases=numeric,device_policy='Exactly physical0/1 visible. All image buffers and kernels on physical1; physical0 only creates/queries an empty foreign stream. Default stream ID0; two actual distinct nondefault streams use overlapping CPU API/synchronize intervals. No GPU overlap/performance claim.',storage='All complete source/output buffers, row padding and original data identity verified. Descriptor/foreign/destroyed errors preserve workspace too; nonfinite effective field may change only workspace. Optional absent output requires null pointer/zero pitch and remains original padding bytes.',concurrency='Two CPU threads enter a barrier, set current logical device1 before calls, then each calls the independent descriptor/stream and synchronizes its own stream; actual intervals must overlap.',default_stream='Callers finish input uploads before cross-stream default calls; synchronize device1 before snapshots.');v['observer_error_cache']='After observing GetDevice, record and clear HIP thread last-error cache with hipGetLastError before further Torch operations. Failed destroyed-stream query returns709 and caches709; this is a query-side effect, not actual context destruction. Original API/query rc and storage remain checked.';write(ROOT/'migration/rewrite/image-distance-state-contract.json',v);write(e.path/'profile.json',v);r=dict(status='FROZEN',case_count=len(rows),numeric_cases=len(numeric));write(e.path/'contracts.json',r);r['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-distance-state-contracts.json',r);record('I2','冻结EDT27项默认/复用变化/恢复/两线程实例/外设备与销毁流/五可选输出及13极值/非有限/最大行列实际输入合同。全部像素仅物理GPU1，物理0只创建空外设备stream。',[r['evidence']]);print(r['status'],r['case_count'],r['evidence']);return 0
if __name__=='__main__':raise SystemExit(main())
