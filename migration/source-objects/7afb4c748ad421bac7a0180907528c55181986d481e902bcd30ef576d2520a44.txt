#!/usr/bin/env python3
"""Add original teaching inputs to the existing independently checked M1 drivers.
Run once; marker guards protect later manual edits.
"""
from pathlib import Path
import json,re
from catalog import ROOT
specpath=ROOT/'migration/m1.json';specs=json.loads(specpath.read_text())
def write(sp,s):
 p=ROOT/'rocm'/sp['path']/'sample.cpp';p.write_text(s);sp['original_profile_covered']=True
 if 'original_profile' not in sp['required_cases']:sp['required_cases'].append('original_profile')
def loop_body(s,start):
 i=s.index('){',start)+1;depth=1;j=i+1
 while depth:
  if s[j]=='{':depth+=1
  if s[j]=='}':depth-=1
  j+=1
 return i,j,s[i+1:j-1]
for sp in specs:
 p=ROOT/'rocm'/sp['path']/'sample.cpp';s=p.read_text();path=sp['path']
 if 'ORIGINAL_PROFILE_IMPLEMENTED' in s or path=='cuSOLVER/getrf':continue
 addition=''
 if path.endswith('/axpy'):
  addition='''{std::vector<double> x={1,2,3,4},y={5,6,7,8};double alpha=2.1;Device<double> dx(x),dy(y);CHECK(hipblasDaxpy(h,4,&alpha,dx.p,1,dy.p,1));CHECK(hipStreamSynchronize(stream.p));report("original_profile",dy.get(),std::vector<double>{7.1,10.2,13.3,16.4});}\n'''
  start=s.index('for(int n:');s=s[:start]+addition+s[start:]
 elif path.endswith('/dot'):
  addition='''{std::vector<double> x={1,2,3,4},y={5,6,7,8};Device<double> dx(x),dy(y);double value=0;CHECK(hipblasDdot(h,4,dx.p,1,dy.p,1,&value));CHECK(hipStreamSynchronize(stream.p));report("original_profile",std::vector<double>{value},std::vector<double>{70});}\n'''
  start=s.index('for(int n:');s=s[:start]+addition+s[start:]
 elif path.startswith('cuBLAS/') or path.startswith('cuBLASLt/'):
  start=s.index('for(bool tr:');i,j,body=loop_body(s,start)
  body=body.replace('"transpose"+std::to_string(tr)+"_beta"+std::to_string(beta)','"original_profile"')
  if path.endswith('/gemv'):
   body=body.replace('m=5,n=3,ld=7','m=2,n=2,ld=2').replace('double alpha=1.25','double alpha=1.0')
   body=body.replace('auto a=input<double>(ld*n),x=input<double>(cols,128),y=input<double>(rows,256),ref=y;','std::vector<double>a={1,3,2,4},x={5,6},y(rows,0),ref=y;')
   prefix='{const bool tr=false;const double beta=0.;'
  elif path.startswith('cuBLASLt/'):
   body=body.replace('m=5,n=3,k=7,lda=(tr?k:m)+2,ldb=k+1,ldc=m+3','m=4,n=4,k=4,lda=4,ldb=4,ldc=4').replace('float alpha=1.25f','float alpha=2.f')
   body=body.replace('auto a=input<float>(lda*(tr?m:k)),b=input<float>(ldb*n,512),c=input<float>(ldc*n,1024),ref=c;','std::vector<float>a(16),b(16),c(16);for(int z=0;z<16;z++)a[z]=b[z]=c[z]=float(z);auto ref=c;')
   prefix='{const bool tr=false;const float beta=0.f;'
  else:
   body=body.replace('m=5,n=3,k=7,lda=(tr?k:m)+2,ldb=k+1,ldc=m+3','m=2,n=2,k=2,lda=2,ldb=2,ldc=2').replace('+5,sb=ldb*n+5,sc=ldc*n+5',' ,sb=ldb*n,sc=ldc*n').replace('double alpha=1.25','double alpha=1.')
   body=body.replace('auto a=input<double>(sa*batches),b=input<double>(sb*batches,512),c=input<double>(sc*batches,1024),ref=c;','std::vector<double>a={1,3,2,4},b={5,7,6,8},c(sc*batches,0);if(batches==2){a={1,3,2,4,5,7,6,8};b={5,7,6,8,9,11,10,12};}auto ref=c;')
   prefix='{const bool tr=false;const double beta=0.;'
  s=s[:start]+prefix+body+'}\n'+s[start:]
 elif path.startswith('cuSPARSE/'):
  # Include the original profile as a separate outer iteration, retaining the edge cases.
  s=s.replace('for(int base:{0,1}) {','for(int profile:{0,1}) for(int base:{0,1}) {\n if(profile==0&&base!=0)continue;')
  if '/spsv_' not in path:
   s=s.replace('for(float beta:{0.f,0.5f}){','for(float beta:{0.f,0.5f}){\n if(profile==0&&beta!=0)continue;')
  if '/spmv_' in path:
   s=s.replace('float alpha=1.25f;','float alpha=profile==0?1.f:1.25f;if(profile==0){x={1,2,3,4};y.assign(n,0);ref=y;}')
  elif '/spmm_' in path:
   s=s.replace('int cols=3,ld=6;','int cols=3,ld=profile==0?4:6;')
   s=s.replace('float alpha=1.25f;','float alpha=profile==0?1.f:1.25f;if(profile==0){for(int z=0;z<12;z++)x[z]=float(z+1);y.assign(12,0);ref=y;}')
  else:s=s.replace('float alpha=1;','float alpha=1;if(profile==0){x={1,8,23,52};ref=x;}')
  s=s.replace('report("base"+std::to_string(base)+"_beta"+std::to_string(beta),','report(profile==0?"original_profile":"base"+std::to_string(base)+"_beta"+std::to_string(beta),')
  s=s.replace('report("base"+std::to_string(base),','report(profile==0?"original_profile":"base"+std::to_string(base),')
 elif path=='cuSOLVER/potrfBatched':
  start=s.index('for(auto fill:');addition='''{int n=3;std::vector<double>a={1,2,3,2,5,5,3,5,12,1,2,3,2,4,5,3,5,12},b={1,1,1};Device<double> da(a),db(b);Device<int> info(2);std::vector<double*> ap={da.p,da.p+9};Device<double*> dap(ap);CHECK(hipsolverDnDpotrfBatched(h,HIPBLAS_FILL_MODE_LOWER,n,dap.p,n,info.p,2));CHECK(hipStreamSynchronize(stream.p));report("original_non_spd_info",info.get(),std::vector<int>{0,2},0,0);std::vector<double*> bp={db.p};Device<double*> dbp(bp);CHECK(hipsolverDnDpotrsBatched(h,HIPBLAS_FILL_MODE_LOWER,n,1,dap.p,n,dbp.p,n,info.p,1));CHECK(hipStreamSynchronize(stream.p));report("original_profile",db.get(),std::vector<double>{10.5,-2.5,-1.5});}\n''';s=s[:start]+addition+s[start:];sp['required_cases'].append('original_non_spd_info')
 elif path.startswith('cuFFT/'):
  # Use the exact n=8 teaching input plus the shared-fixture n=8/15 cases.
  s=s.replace('for(int n:{8,15}){','for(int profile:{0,1})for(int n:{8,15}){if(profile==0&&n!=8)continue;')
  if path.endswith('/1d_c2c'):
   s=s.replace('auto raw=input<float>(n*batch*2);','auto raw=input<float>(n*batch*2);if(profile==0)for(int z=0;z<n*batch;z++){raw[2*z]=float(z);raw[2*z+1]=float(-z);}')
  else:s=s.replace('auto x=input<float>(n*batch);','auto x=input<float>(n*batch);if(profile==0)for(int z=0;z<n*batch;z++)x[z]=float(z);')
  s=s.replace('report("forward_n"+std::to_string(n),','report(profile==0?"original_forward":"forward_n"+std::to_string(n),').replace('report("roundtrip_n"+std::to_string(n),','report(profile==0?"original_profile":"roundtrip_n"+std::to_string(n),')
  sp['required_cases'].append('original_forward')
 elif path.startswith('cuRAND/'):
  # Small-n profile validates the actual original host/device calls and exact reproducibility.
  start=s.index(' for(bool host:')
  normal=path.endswith('/normal');generate='hiprandGenerateNormal(gen,dest,12,0.f,1.f)' if normal else 'hiprandGenerateUniform(gen,dest,12)'
  addition=''' {std::vector<double> bounds;for(bool host:{false,true}){std::vector<float> first;for(int repeat=0;repeat<2;repeat++){hiprandGenerator_t gen;CHECK(host?hiprandCreateGeneratorHost(&gen,HIPRAND_RNG_PSEUDO_PHILOX4_32_10):hiprandCreateGenerator(&gen,HIPRAND_RNG_PSEUDO_PHILOX4_32_10));CHECK(hiprandSetStream(gen,stream.p));CHECK(hiprandSetGeneratorOffset(gen,0));CHECK(hiprandSetGeneratorOrdering(gen,HIPRAND_ORDERING_PSEUDO_BEST));CHECK(hiprandSetPseudoRandomGeneratorSeed(gen,1234));Device<float>d(12);std::vector<float>x(12);float*dest=host?x.data():d.p;CHECK(GENERATE);CHECK(hipStreamSynchronize(stream.p));if(!host)x=d.get();CHECK(hiprandDestroyGenerator(gen));for(float v:x)if(!std::isfinite(v) RANGE)throw std::runtime_error("original RNG range");if(repeat==0)first=x;else if(first!=x)throw std::runtime_error("original RNG reproducibility");}bounds.push_back(1.);}report("original_profile",bounds,std::vector<double>{1,1},0,0);}\n'''
  addition=addition.replace('GENERATE',generate).replace('RANGE','' if normal else '||v<=0||v>1');s=s[:start]+addition+s[start:]
 else:continue
 s=s.replace('// ROCm implementation','// ORIGINAL_PROFILE_IMPLEMENTED\n// ROCm implementation',1);write(sp,s)
specpath.write_text(json.dumps(specs,indent=2,ensure_ascii=False)+'\n');print('Required M1 cases:',sum(len(s['required_cases']) for s in specs))
