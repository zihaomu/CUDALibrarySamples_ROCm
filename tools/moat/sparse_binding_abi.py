#!/usr/bin/env python3
"""Exercise actual shared-library phase, type-width and lifetime errors."""
import argparse,ctypes,json,sys
from experiment import ROOT,Experiment,write
def run(library):
 import numpy as np
 from sparse_binding_reference import validate
 lib=ctypes.CDLL(library);ip=ctypes.POINTER(ctypes.c_int);dp=ctypes.POINTER(ctypes.c_double);vp=ctypes.c_void_p;size=ctypes.c_size_t
 lib.rw_sparse_create.argtypes=[ctypes.c_int,ctypes.c_int,ip,ip,dp,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.POINTER(vp)];lib.rw_sparse_analyze.argtypes=[vp,ip,ip,ctypes.POINTER(size)];lib.rw_sparse_solve.argtypes=[vp,ctypes.c_int,dp,ctypes.c_int,dp,ctypes.c_int,ip];lib.rw_sparse_destroy.argtypes=[vp];lib.rw_sparse_set_values.argtypes=[vp,ctypes.c_int,dp]
 rows=np.array([1,3,5,7,8,9],dtype=np.int32);cols=np.array([1,3,2,3,3,5,4,5],dtype=np.int32);vals=np.array([4,1,3,2,5,1,1,2],dtype=np.float64);b=np.array([7,12,25,4,13],dtype=np.float64);x=np.zeros(5,dtype=np.float64);info=ctypes.c_int();h=vp();rp=np.zeros(5,dtype=np.int32);cp=rp.copy();nbytes=size();checks=[]
 def check(name,value):checks.append(dict(check=name,passed=bool(value)))
 ptr=lambda array,kind:array.ctypes.data_as(kind)
 check('C-widths',ctypes.sizeof(ctypes.c_int)==4 and ctypes.sizeof(ctypes.c_double)==8 and ctypes.sizeof(size)==8)
 check('create',lib.rw_sparse_create(5,8,ptr(rows,ip),ptr(cols,ip),ptr(vals,dp),1,1,1,ctypes.byref(h))==0 and bool(h))
 check('solve-before-analysis-rejected',lib.rw_sparse_solve(h,1,ptr(b,dp),5,ptr(x,dp),5,ctypes.byref(info))==1)
 check('query',lib.rw_sparse_analyze(h,ptr(rp,ip),ptr(cp,ip),ctypes.byref(nbytes))==0 and nbytes.value==20)
 check('set-values-requires-retained-factor',lib.rw_sparse_set_values(h,8,ptr(vals,dp))==1)
 check('bad-stride-rejected',lib.rw_sparse_solve(h,1,ptr(b,dp),4,ptr(x,dp),5,ctypes.byref(info))==1)
 check('solve',lib.rw_sparse_solve(h,1,ptr(b,dp),5,ptr(x,dp),5,ctypes.byref(info))==0 and info.value==0 and np.allclose(x,[1,2,3,4,5],atol=1e-12))
 check('updated-value-shape-rejected',lib.rw_sparse_set_values(h,7,ptr(vals,dp))==1)
 vals*=2;check('selected-values-reuse',lib.rw_sparse_set_values(h,8,ptr(vals,dp))==0 and lib.rw_sparse_solve(h,1,ptr(b,dp),5,ptr(x,dp),5,ctypes.byref(info))==0 and info.value==0 and np.allclose(x,[.5,1,1.5,2,2.5],atol=1e-12))
 check('destroy',lib.rw_sparse_destroy(h)==0);check('double-destroy-rejected',lib.rw_sparse_destroy(h)==1);check('stale-handle-rejected',lib.rw_sparse_analyze(h,ptr(rp,ip),ptr(cp,ip),ctypes.byref(nbytes))==1);check('null-handle-rejected',lib.rw_sparse_destroy(None)==1)
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks)
p=argparse.ArgumentParser();p.add_argument('--single',nargs=2);args=p.parse_args()
if args.single:
 r=run(args.single[0]);write(args.single[1],r);raise SystemExit(r['status']!='PASSED')
from snapshot import capture
b=json.loads((ROOT/'migration/reports/rewrite-sparse-binding-build.json').read_text());e=Experiment('R5','sparse-binding-C-ABI','rocm-ABI',sources=[__file__,ROOT/'rocm/adapters/fortran/sparse_bridge.cpp'],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());report=e.path/'abi-report.json';rc=e.command([sys.executable,__file__,'--single',str(ROOT/b['shared_library']),str(report)],'actual-C-ABI');r=json.loads(report.read_text());r['evidence']=e.finish('PASSED' if rc==0 else 'RUNTIME_ERROR',r);write(ROOT/'migration/reports/rewrite-sparse-binding-abi.json',r);print(r['status'])
