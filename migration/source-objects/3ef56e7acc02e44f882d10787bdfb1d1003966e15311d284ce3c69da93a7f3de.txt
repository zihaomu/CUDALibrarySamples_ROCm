// SPDX-License-Identifier: Apache-2.0
#include "matrix_helpers.h"
#include <array>
#include <vector>
#include <map>
#include <memory>
#include <fstream>
#include <string>
#include <cstring>
#include <cstdlib>
#include <algorithm>
#include <mutex>
#ifdef MH_NATIVE_CUDA
#include <cuda_runtime.h>
#include <cudss.h>
#define GPU(n) cuda##n
#else
#include <hip/hip_runtime.h>
#define GPU(n) hip##n
#endif
namespace {
std::recursive_mutex lock;
std::map<void*,size_t> allocations;
struct Matrix {
 int format,batch,base; int32_t *nr,*nc,*nnz,*ld;
 std::array<int32_t,4> scalar;
 void *rows,*columns,*values;
#ifdef MH_NATIVE_CUDA
 cudssMatrix_t native=nullptr;
#endif
};
std::map<void*,std::unique_ptr<Matrix>> matrices;
struct Context {
 int batched;GPU(Stream_t) stream=nullptr;
#ifdef MH_NATIVE_CUDA
 cudssHandle_t handle=nullptr;cudssConfig_t config=nullptr;cudssData_t data=nullptr;
#endif
};
std::map<void*,std::unique_ptr<Context>> contexts;
uintptr_t next_token=0x10000;
Matrix* matrix(void*p){auto i=matrices.find(p);return i==matrices.end()?nullptr:i->second.get();}
bool buffer(void*p,size_t bytes){auto i=allocations.find(p);return i!=allocations.end()&&i->second>=bytes;}
bool data_pointer(Matrix&s,void*p){return buffer(p,(s.format&4)?size_t(s.batch)*sizeof(void*):sizeof(double));}
template<class T> bool copy(std::vector<T>&out,const void*ptr,size_t count){out.resize(count);return count==0||mh_download(out.data(),ptr,count*sizeof(T))==0;}
template<class T> bool save(const std::string&name,const std::vector<T>&data){return mh_save(name.c_str(),data.data(),data.size()*sizeof(T))==0;}
}
extern "C" size_t mh_query_bytes(){return sizeof(mh_query);}
extern "C" int mh_alloc(void**p,size_t bytes){std::lock_guard<std::recursive_mutex>g(lock);if(!p||!bytes)return 1;*p=nullptr;auto rc=GPU(Malloc)(p,bytes);if(rc!=GPU(Success))return 2;if(GPU(Memset)(*p,0xa5,bytes)!=GPU(Success)){GPU(Free)(*p);*p=nullptr;return 2;}allocations[*p]=bytes;return 0;}
extern "C" int mh_upload(void*p,const void*h,size_t n){std::lock_guard<std::recursive_mutex>g(lock);if(!h||!buffer(p,n))return 1;return GPU(Memcpy)(p,h,n,GPU(MemcpyHostToDevice))==GPU(Success)?0:2;}
extern "C" int mh_download(void*h,const void*p,size_t n){std::lock_guard<std::recursive_mutex>g(lock);if(!h||!buffer(const_cast<void*>(p),n))return 1;return GPU(Memcpy)(h,p,n,GPU(MemcpyDeviceToHost))==GPU(Success)?0:2;}
extern "C" int mh_free(void*p){std::lock_guard<std::recursive_mutex>g(lock);if(!allocations.count(p))return 1;if(GPU(Free)(p)!=GPU(Success))return 2;allocations.erase(p);return 0;}
extern "C" int mh_context_create(int batched,void**out){std::lock_guard<std::recursive_mutex>g(lock);if(!out)return 1;*out=nullptr;if(batched!=0&&batched!=1)return 1;auto c=std::make_unique<Context>();c->batched=batched;
 if(batched&&GPU(StreamCreate)(&c->stream)!=GPU(Success))return 2;
#ifdef MH_NATIVE_CUDA
 auto rc=cudssCreate(&c->handle);if(rc!=CUDSS_STATUS_SUCCESS){if(c->stream)GPU(StreamDestroy)(c->stream);return 10+int(rc);}
 if(batched){rc=cudssSetStream(c->handle,c->stream);if(rc==CUDSS_STATUS_SUCCESS)rc=cudssConfigCreate(&c->config);if(rc==CUDSS_STATUS_SUCCESS)rc=cudssDataCreate(c->handle,&c->data);if(rc!=CUDSS_STATUS_SUCCESS){if(c->data)cudssDataDestroy(c->handle,c->data);if(c->config)cudssConfigDestroy(c->config);cudssDestroy(c->handle);GPU(StreamDestroy)(c->stream);return 10+int(rc);}}
#endif
 void*token=reinterpret_cast<void*>(next_token+=16);contexts[token]=std::move(c);*out=token;return 0;}
extern "C" int mh_context_destroy(void*p){std::lock_guard<std::recursive_mutex>g(lock);auto i=contexts.find(p);if(i==contexts.end())return 1;auto&c=*i->second;
#ifdef MH_NATIVE_CUDA
 if(c.data&&cudssDataDestroy(c.handle,c.data)!=CUDSS_STATUS_SUCCESS)return 2;if(c.config&&cudssConfigDestroy(c.config)!=CUDSS_STATUS_SUCCESS)return 2;if(cudssDestroy(c.handle)!=CUDSS_STATUS_SUCCESS)return 2;
#endif
 if(c.stream&&(GPU(StreamSynchronize)(c.stream)!=GPU(Success)||GPU(StreamDestroy)(c.stream)!=GPU(Success)))return 2;contexts.erase(i);return 0;}
extern "C" int mh_create(int f,int batch,int32_t*nr,int32_t*nc,int32_t*nz,int32_t*ld,void*r,void*c,void*v,int base,void**h){
 std::lock_guard<std::recursive_mutex>g(lock);if(!h)return 1;*h=nullptr;
 if((f!=1&&f!=2&&f!=5&&f!=6)||batch<1||batch>16||(!(f&4)&&batch!=1)||!nr||!nc||!nz||!ld||base<0||base>1)return 1;
 for(int i=0;i<batch;++i)if(nr[i]<1||nc[i]<1||nr[i]>1000000||nc[i]>1000000||nz[i]<0||ld[i]<nr[i])return 1;
 auto s=std::make_unique<Matrix>();s->format=f;s->batch=batch;s->base=base;s->rows=r;s->columns=c;s->values=v;
 s->scalar={nr[0],nc[0],nz[0],ld[0]};s->nr=(f&4)?nr:&s->scalar[0];s->nc=(f&4)?nc:&s->scalar[1];s->nnz=(f&4)?nz:&s->scalar[2];s->ld=(f&4)?ld:&s->scalar[3];
 if(!data_pointer(*s,v)||((f&2)&&(!buffer(r,(f&4)?batch*sizeof(void*):size_t(nr[0]+1)*4)||!buffer(c,(f&4)?batch*sizeof(void*):size_t(std::max(1,nz[0]))*4))))return 1;
#ifdef MH_NATIVE_CUDA
 cudssStatus_t rc;
 if(f==1)rc=cudssMatrixCreateDn(&s->native,nr[0],nc[0],ld[0],v,CUDA_R_64F,CUDSS_LAYOUT_COL_MAJOR);
 else if(f==2)rc=cudssMatrixCreateCsr(&s->native,nr[0],nc[0],nz[0],r,nullptr,c,v,CUDA_R_32I,CUDA_R_32I,CUDA_R_64F,CUDSS_MTYPE_SYMMETRIC,CUDSS_MVIEW_UPPER,cudssIndexBase_t(base));
 else if(f==5)rc=cudssMatrixCreateBatchDn(&s->native,batch,nr,nc,ld,(const void*const*)v,CUDA_R_32I,CUDA_R_64F,CUDSS_LAYOUT_COL_MAJOR);
 else rc=cudssMatrixCreateBatchCsr(&s->native,batch,nr,nc,nz,(const void*const*)r,nullptr,(const void*const*)c,(const void*const*)v,CUDA_R_32I,CUDA_R_32I,CUDA_R_64F,CUDSS_MTYPE_SPD,CUDSS_MVIEW_UPPER,cudssIndexBase_t(base));
 if(rc!=CUDSS_STATUS_SUCCESS)return 10+int(rc);
#endif
 void*token=reinterpret_cast<void*>(next_token+=16);matrices[token]=std::move(s);*h=token;return 0;
}
extern "C" int mh_get(void*h,mh_query*out,int mask){std::lock_guard<std::recursive_mutex>g(lock);auto*s=matrix(h);if(!s||!out||mask<1||mask>7)return 1;
 mh_query q{};q.sizes[0]=s->batch;q.sizes[1]=s->nr[0];q.sizes[2]=s->nc[0];q.sizes[3]=(s->format&2)?s->nnz[0]:0;q.sizes[4]=(s->format&2)?0:s->ld[0];
 q.pointers[0]=s->rows;q.pointers[1]=s->columns;q.pointers[2]=s->values;
 if(s->format&4){q.pointers[3]=s->nr;q.pointers[4]=s->nc;if(s->format&2)q.pointers[5]=s->nnz;else q.pointers[6]=s->ld;}
 int32_t codes[]={s->format,10,10,1,(s->format&2)?((s->format&4)?3:1):0,(s->format&2)?2:0,(s->format&2)?s->base:0,0};std::copy(codes,codes+8,q.codes);
#ifdef MH_NATIVE_CUDA
 cudaDataType_t it=CUDA_R_32I,ot=CUDA_R_32I,vt=CUDA_R_64F;cudssMatrixType_t mt=CUDSS_MTYPE_GENERAL;cudssMatrixViewType_t mv=CUDSS_MVIEW_FULL;cudssIndexBase_t ib=CUDSS_BASE_ZERO;cudssLayout_t ly=CUDSS_LAYOUT_COL_MAJOR;cudssStatus_t rc;
 if(s->format==1)rc=cudssMatrixGetDn(s->native,&q.sizes[1],&q.sizes[2],&q.sizes[4],&q.pointers[2],&vt,&ly);
 else if(s->format==2)rc=cudssMatrixGetCsr(s->native,&q.sizes[1],&q.sizes[2],&q.sizes[3],&q.pointers[0],&q.pointers[7],&q.pointers[1],&q.pointers[2],&ot,&it,&vt,&mt,&mv,&ib);
 else if(s->format==5)rc=cudssMatrixGetBatchDn(s->native,&q.sizes[0],&q.pointers[3],&q.pointers[4],&q.pointers[6],(void***)&q.pointers[2],&it,&vt,&ly);
 else rc=cudssMatrixGetBatchCsr(s->native,&q.sizes[0],&q.pointers[3],&q.pointers[4],&q.pointers[5],(void***)&q.pointers[0],(void***)&q.pointers[7],(void***)&q.pointers[1],(void***)&q.pointers[2],&ot,&it,&vt,&mt,&mv,&ib);
 if(rc!=CUDSS_STATUS_SUCCESS)return 10+int(rc);int format=0;if(cudssMatrixGetFormat(s->native,&format)!=CUDSS_STATUS_SUCCESS)return 2;
 q.codes[0]=format;q.codes[1]=int(it);q.codes[2]=int(ot);q.codes[3]=int(vt);q.codes[4]=int(mt);q.codes[5]=int(mv);q.codes[6]=int(ib);q.codes[7]=int(ly);
 if(s->format&4){q.sizes[1]=((int32_t*)q.pointers[3])[0];q.sizes[2]=((int32_t*)q.pointers[4])[0];q.sizes[3]=(s->format&2)?((int32_t*)q.pointers[5])[0]:0;q.sizes[4]=(s->format&2)?0:((int32_t*)q.pointers[6])[0];}
#endif
 if(mask&1)std::memcpy(out->sizes,q.sizes,sizeof q.sizes);if(mask&2)std::memcpy(out->pointers,q.pointers,sizeof q.pointers);if(mask&4)std::memcpy(out->codes,q.codes,sizeof q.codes);return 0;
}
extern "C" int mh_set_values(void*h,void*v){std::lock_guard<std::recursive_mutex>g(lock);auto*s=matrix(h);if(!s||!data_pointer(*s,v))return 1;
#ifdef MH_NATIVE_CUDA
 auto rc=(s->format&4)?cudssMatrixSetBatchValues(s->native,(const void*const*)v):cudssMatrixSetValues(s->native,v);if(rc!=CUDSS_STATUS_SUCCESS)return 10+int(rc);
#endif
 s->values=v;return 0;}
extern "C" int mh_set_csr(void*h,void*r,void*c,void*v){std::lock_guard<std::recursive_mutex>g(lock);auto*s=matrix(h);if(!s||!(s->format&2)||!data_pointer(*s,v)||!buffer(r,(s->format&4)?s->batch*sizeof(void*):size_t(s->nr[0]+1)*4)||!buffer(c,(s->format&4)?s->batch*sizeof(void*):4))return 1;
#ifdef MH_NATIVE_CUDA
 auto rc=(s->format&4)?cudssMatrixSetBatchCsrPointers(s->native,(const void*const*)r,nullptr,(const void*const*)c,(const void*const*)v):cudssMatrixSetCsrPointers(s->native,r,nullptr,c,v);if(rc!=CUDSS_STATUS_SUCCESS)return 10+int(rc);
#endif
 s->rows=r;s->columns=c;s->values=v;return 0;}
extern "C" int mh_destroy(void*h){std::lock_guard<std::recursive_mutex>g(lock);auto*s=matrix(h);if(!s)return 1;
#ifdef MH_NATIVE_CUDA
 if(cudssMatrixDestroy(s->native)!=CUDSS_STATUS_SUCCESS)return 2;
#endif
 matrices.erase(h);return 0;}
extern "C" int mh_save(const char*name,const void*data,size_t bytes){const char*root=std::getenv("REWRITE_OUTPUT");if(!root||!name||std::string(name).find('/')!=std::string::npos)return 1;std::ofstream f(std::string(root)+"/"+name+".bin",std::ios::binary);if(bytes)f.write((const char*)data,bytes);return f?0:2;}
extern "C" int mh_snapshot(const char*name,const mh_query*q,void*r,void*c,void*v,int32_t*nr,int32_t*nc,int32_t*nz,int32_t*ld){
 std::lock_guard<std::recursive_mutex>g(lock);if(!q||!name)return 1;std::string prefix(name);bool batch=q->codes[0]&4,csr=q->codes[0]&2;int count=int(q->sizes[0]);if(count<1||count>16)return 1;
 void*expected[]={r,c,v,batch?(void*)nr:nullptr,batch?(void*)nc:nullptr,(batch&&csr)?(void*)nz:nullptr,(batch&&!csr)?(void*)ld:nullptr,nullptr};std::vector<int64_t>meta(q->sizes,q->sizes+5);for(auto code:q->codes)meta.push_back(code);for(int i=0;i<8;++i)meta.push_back(q->pointers[i]==expected[i]);if(!save(prefix+"_meta",meta))return 2;
 std::vector<int32_t>shapes;std::vector<void*>rr(count),cc(count),vv(count);
 if(batch){if(!copy(vv,q->pointers[2],count))return 2;if(csr&&(!copy(rr,q->pointers[0],count)||!copy(cc,q->pointers[1],count)))return 2;}
 else{rr[0]=q->pointers[0];cc[0]=q->pointers[1];vv[0]=q->pointers[2];}
 for(int i=0;i<count;++i){int n=batch?((int32_t*)q->pointers[3])[i]:q->sizes[1],cols=batch?((int32_t*)q->pointers[4])[i]:q->sizes[2],nnz=csr?(batch?((int32_t*)q->pointers[5])[i]:q->sizes[3]):0,leading=csr?0:(batch?((int32_t*)q->pointers[6])[i]:q->sizes[4]);shapes.insert(shapes.end(),{n,cols,nnz,leading});
  std::vector<double>values;auto allocation=allocations.find(vv[i]);if(allocation==allocations.end()||!copy(values,vv[i],allocation->second/8)||!save(prefix+"_b"+std::to_string(i)+"_values",values))return 2;
  if(csr){std::vector<int32_t>rows,columns;if(!copy(rows,rr[i],size_t(n)+1))return 2;int active=rows.back()-q->codes[6];if(active<0||!copy(columns,cc[i],active)||!save(prefix+"_b"+std::to_string(i)+"_rows",rows)||!save(prefix+"_b"+std::to_string(i)+"_columns",columns))return 2;}
 }
 return save(prefix+"_shapes",shapes)?0:2;
}
