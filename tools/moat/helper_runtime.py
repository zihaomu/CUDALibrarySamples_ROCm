#!/usr/bin/env python3
"""Actual invalid language entrypoints and C ABI calls; no simulated API results."""
import ctypes as C,json,shutil
from experiment import ROOT,Experiment,write
from snapshot import capture

class Query(C.Structure):_fields_=[('sizes',C.c_int64*5),('pointers',C.c_void_p*8),('codes',C.c_int32*8)]
def main():
 build=json.loads((ROOT/'migration/reports/rewrite-R9-helper-build.json').read_text());profiles=json.loads((ROOT/'migration/rewrite/helpers-benchmark.json').read_text())['helpers'];results=[];observed=capture()
 for p in profiles:
  src=ROOT/'tests/fixtures/rewrite-helpers'/p['language']/p['kind']/'original';e=Experiment('R9',p['sample_id'],'invalid-entry',case='wrong-profile',sources=[__file__]+[ROOT/n for n in build['dependencies']],parent=build['experiment_id']);shutil.copytree(src,e.path/'inputs');text=(e.path/'inputs/config.txt').read_text().split();text[0]='0';(e.path/'inputs/config.txt').write_text(' '.join(text)+'\n');out=e.path/'outputs';out.mkdir();binary=next(r for r in build['binaries'] if r['sample_id']==p['sample_id']);rc=e.command([str(ROOT/binary['binary'])],'real-'+p['language']+'-invalid-profile',env=dict(REWRITE_INPUT=str(e.path/'inputs'),REWRITE_OUTPUT=str(out)));valid=dict(status='PASSED' if rc!=0 else 'FAILED',checks=[dict(check='actual-entry-rejects-wrong-profile',passed=rc!=0)]);r=dict(sample_id=p['sample_id'],return_code=rc,passed=rc!=0);write(e.path/'backend.observed.json',observed);r['evidence']=e.finish('EXPECTED_REJECTION' if r['passed'] else 'SELF_TEST_FAILED',valid);results.append(r)
 e=Experiment('R9','matrix-helper-ABI-negative','rocm-ABI',sources=[__file__]+[ROOT/n for n in build['dependencies']],parent=build['experiment_id']);write(e.path/'backend.observed.json',observed);lib=C.CDLL(str(ROOT/build['shared_library']));ptr=C.c_void_p;ints=C.POINTER(C.c_int32)
 lib.mh_alloc.argtypes=[C.POINTER(ptr),C.c_size_t];lib.mh_upload.argtypes=[ptr,ptr,C.c_size_t];lib.mh_download.argtypes=[ptr,ptr,C.c_size_t];lib.mh_free.argtypes=[ptr];lib.mh_create.argtypes=[C.c_int,C.c_int,ints,ints,ints,ints,ptr,ptr,ptr,C.c_int,C.POINTER(ptr)];lib.mh_get.argtypes=[ptr,C.POINTER(Query),C.c_int];lib.mh_destroy.argtypes=[ptr];lib.mh_set_values.argtypes=[ptr,ptr];lib.mh_set_csr.argtypes=[ptr,ptr,ptr,ptr];lib.mh_query_bytes.restype=C.c_size_t
 values=(C.c_double*12)(*range(12));device=ptr();assert lib.mh_alloc(C.byref(device),C.sizeof(values))==0;assert lib.mh_upload(device,values,C.sizeof(values))==0
 nr=(C.c_int32*2)(3,4);nc=(C.c_int32*2)(2,2);nz=(C.c_int32*2)(0,0);ld=(C.c_int32*2)(6,6);h=ptr();assert lib.mh_create(1,1,nr,nc,nz,ld,None,None,device,0,C.byref(h))==0;checks=[]
 def rejected(name,rc):checks.append(dict(check=name,passed=rc!=0))
 for f,b,base in [(0,1,0),(3,1,0),(9,1,0),(1,0,0),(1,17,0),(1,2,0),(1,1,2)]:
  bad=ptr();rejected('invalid-descriptor-'+str((f,b,base)),lib.mh_create(f,b,nr,nc,nz,ld,None,None,device,base,C.byref(bad)))
 saved=nr[0];nr[0]=0;bad=ptr();rejected('zero-rows',lib.mh_create(1,1,nr,nc,nz,ld,None,None,device,0,C.byref(bad)));nr[0]=saved
 ld[0]=2;rejected('invalid-leading-dimension',lib.mh_create(1,1,nr,nc,nz,ld,None,None,device,0,C.byref(bad)));ld[0]=6
 for mask in [-1,0,8]:rejected('invalid-query-mask-'+str(mask),lib.mh_get(h,C.byref(Query()),mask))
 rejected('null-query',lib.mh_get(h,None,7));rejected('null-values',lib.mh_set_values(h,None));rejected('foreign-values',lib.mh_set_values(h,ptr(0x1234)));rejected('CSR-setter-on-dense',lib.mh_set_csr(h,device,device,device));q=Query();assert lib.mh_get(h,C.byref(q),7)==0;checks.append(dict(check='failed-setters-preserve-old-pointer',passed=q.pointers[2]==device.value));checks.append(dict(check='ABI-width',passed=lib.mh_query_bytes()==C.sizeof(Query)))
 assert lib.mh_destroy(h)==0;rejected('stale-query',lib.mh_get(h,C.byref(Query()),7));rejected('double-destroy',lib.mh_destroy(h));echo=(C.c_double*12)();assert lib.mh_download(echo,device,C.sizeof(values))==0;checks.append(dict(check='caller-device-storage-survives-object',passed=bytes(echo)==bytes(values)));assert lib.mh_free(device)==0;rejected('double-device-free',lib.mh_free(device))
 valid=dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks);write(e.path/'ABI-checks.json',valid);evidence=e.finish('PASSED' if valid['status']=='PASSED' else 'SELF_TEST_FAILED',valid);write(ROOT/'migration/reports/rewrite-R9-helper-runtime.json',dict(status='PASSED' if valid['status']=='PASSED' and all(r['passed'] for r in results) else 'FAILED',entries=results,ABI=dict(**valid,evidence=evidence)));print('actual invalid entries',len(results),'ABI checks',len(checks),valid['status'])
if __name__=='__main__':main()
