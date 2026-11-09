#!/usr/bin/env python3
"""Build original-profile ports independently, retaining every result.

Builds may overlap on CPU; GPU runs are serial. Successful execution alone never
becomes a migration PASSED result. Later validators attach independent evidence.
"""
import argparse,concurrent.futures,datetime,fcntl,hashlib,json,os,pathlib,re,shutil,subprocess,time
from catalog import ROOT
from run import command,digest
from progress import checkpoint
FAMILY_LIBS={'cuBLAS':['hipblas'],'cuBLASLt':['hipblaslt'],'cuSPARSE':['hipsparse'],'cuSOLVER':['hipsolver'],'cuFFT':['hipfft'],'cuRAND':['hiprand'],'cuSPARSELt':['hipsparselt','hipsparse'], 'cuDSS':['rocsolver','rocsparse','rocblas'], 'cuSOLVERSp2cuDSS':['rocsolver','rocsparse'], 'cuTENSOR':['hiptensor'], 'cuTENSORMg':['hiptensor','rccl'], 'cuTENSORMp':['hiptensor','rccl'], 'cuBLASMp':['hipblas','rccl'], 'cuSOLVERMp':['hipsolver','hipblas','rccl'], 'cuFFTMp':['rocfft'], 'NPP':['rpp'], 'NPP+':['rpp'], 'nvJPEG':['rocjpeg','rpp'], 'nvJPEG2000':[], 'nvTIFF':[], 'nvCOMP':['hipcomp'], 'nvMatmulHeuristics':['hipblaslt','origami'], 'cuPQC':[], 'cuEST':[], 'MathDx/cuBLASDx':[], 'MathDx/cuFFTDx':[], 'MathDx/cuRANDDx':['hiprand'], 'MathDx/cuSolverDx':[], 'MathDx/libmathdx':['hiprtc'], 'MathDx/nvCOMPDx':['hipcomp']}

def update(source,result,backend):
 lock=ROOT/'migration/.state.lock'
 with lock.open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX);path=ROOT/'migration/samples.yaml';cat=json.loads(path.read_text());s=next(s for s in cat['samples'] if s['source']==source)
  field='original_port' if backend=='rocm' else 'original_cuda';s[field]=result
  if backend=='rocm':
   s['attempts'].append(result);s['evidence'].append(result['evidence']);s['original_implementation']=result['implementation']
   if s['status'] not in {'PASSED'} and not s.get('passed_cases'):
    s.update(status='PARTIAL' if result['return_code']==0 else 'FAILED',level=result['level'],reason_code='INDEPENDENT_VALIDATION_PENDING' if result['return_code']==0 else result['reason_code'],reason=result['reason'],actual_library=result['actual_library'],backend_library=result['backend_library'],implementation=result['implementation'])
  else:s['cuda_baseline']='PASSED' if result['return_code']==0 else 'FAILED'
  path.write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n')

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--families',nargs='+',default=list(FAMILY_LIBS));parser.add_argument('--backend',choices=['rocm','cuda'],default='rocm');parser.add_argument('--filter',default='');parser.add_argument('--jobs',type=int,default=3);parser.add_argument('--timeout',type=int,default=60);parser.add_argument('--retry-failed',action='store_true');parser.add_argument('--observed',action='store_true');args=parser.parse_args()
 cat=json.loads((ROOT/'migration/samples.yaml').read_text());samples=[s for s in cat['samples'] if (not args.retry_failed or s.get('original_port' if args.backend=='rocm' else 'original_cuda',{}).get('return_code',1)!=0) and s['family'] in args.families and args.filter in s['source'] and pathlib.Path(s['source']).suffix in {'.c','.cpp','.cu'}]
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'artifacts'/stamp/('original-'+args.backend);out.mkdir(parents=True)
 env=os.environ.copy();overlay=ROOT/'build/rocm-sdk-overlay';native=pathlib.Path('/opt/rocm/core-10.1');site=pathlib.Path('/opt/venv/lib/python3.13/site-packages');core=site/'_rocm_sdk_core';libs=site/'_rocm_sdk_libraries';cuda=pathlib.Path('/usr/local/cuda-13.4');cuda_mode=args.backend=='cuda'
 if not cuda_mode and env.get('DEEPINFER_ROCM_RELEASE')!='10.1.0':raise RuntimeError('locked ROCm 10.1.0 required')
 cuda_links={'cuBLAS':['cublas'],'cuBLASLt':['cublasLt'],'cuSPARSE':['cusparse','cublas'],'cuSOLVER':['cusolver','cublas'],'cuFFT':['cufft'],'cuRAND':['curand'],'cuSPARSELt':['cusparseLt'],'cuTENSOR':['cutensor'],'cuTENSORMg':['cutensorMg'],'cuTENSORMp':['cutensorMp'],'cuDSS':['cudss'],'cuSOLVERSp2cuDSS':['cudss','cusolver'],'cuBLASMp':['cublasMp'],'cuSOLVERMp':['cusolverMp'],'cuFFTMp':['cufftMp'],'NPP':['nppc','nppif','nppig'],'NPP+':[],'nvJPEG':['nvjpeg'],'nvJPEG2000':['nvjpeg2k'],'nvTIFF':['nvtiff'],'nvCOMP':['nvcomp'],'nvMatmulHeuristics':['nvMatmulHeuristics'],'cuEST':['cuest'],'cuPQC':[],'MathDx/cuBLASDx':[],'MathDx/cuFFTDx':[],'MathDx/cuSolverDx':[],'MathDx/cuRANDDx':[],'MathDx/libmathdx':['mathdx','nvrtc'],'MathDx/nvCOMPDx':[]}
 identity={'backend':args.backend,'image_id':env.get('DEEPINFER_IMAGE_ID'),'rocm_release':env.get('DEEPINFER_ROCM_RELEASE'),'visible_devices':env.get('HIP_VISIBLE_DEVICES',env.get('CUDA_VISIBLE_DEVICES')),'upstream_commit':cat['upstream_commit'],'stage':'original profile build/run, validation separate'}
 if not cuda_mode:
  from device_guard import allowed_devices
  identity['devices']=allowed_devices()
 (out/'environment.json').write_text(json.dumps(identity,indent=2)+'\n')
 audit_path=ROOT/'migration/build-audit.json';declarations=json.loads(audit_path.read_text()).get('declarations',[]) if audit_path.exists() else []
 def build(sample):
  source=(ROOT/'build/cuda-observed'/sample['source'] if args.observed and (ROOT/'build/cuda-observed'/sample['source']).exists() else ROOT/sample['source']) if cuda_mode else ROOT/'rocm/ported'/sample['source'];family=sample['family'];d=out/(sample['source'].replace('/','_'));d.mkdir();binary=d/'sample';requires_kernel=(family in {'cuFFT','cuBLASLt','cuSPARSELt','NPP','NPP+'} or family.startswith('MathDx/')) or '__global__' in source.read_text(errors='replace') or '__device__' in source.read_text(errors='replace');sources=[source]
  for binding in sample.get('build_bindings',[]):
   for declaration in declarations:
    if declaration['build']==binding['build'] and declaration['target_expression']==binding['target_expression']:
     for path in declaration['sources']:
      observed_source=ROOT/'build/cuda-observed'/path
      p=((observed_source if args.observed and observed_source.exists() else ROOT/path) if cuda_mode else ROOT/'rocm/ported'/path)
      if p.suffix in {'.cpp','.cu','.c'} and p.exists() and p!=source and not re.search(r'\b(?:int|void)\s+main\s*\(',p.read_text(errors='replace')):sources.append(p)
   # Recover linked implementation files for e.g. cuBLASLt main.cpp.
   if family=='cuBLASLt':
    for p in source.parent.glob('*.cu'):sources.append(p)
  sources=list(dict.fromkeys(sources));base=(ROOT/'build/cuda-observed' if args.observed else ROOT) if cuda_mode else ROOT/'rocm/ported';includes=[source.parent,base/family/'utils',base/'cuBLASLt/Common',ROOT/'rocm/common']
  if cuda_mode:
   compiler=str(cuda/'bin/nvcc');cmd=[compiler,'-x','cu','-std=c++17','-O2','-arch=sm_120'];includes += [cuda/'include'];links=['-L'+str(cuda/'lib64'),'-Xlinker=-rpath='+str(cuda/'lib64')]+['-l'+x for x in cuda_links[family]]
  else:
   compiler=shutil.which('hipcc' if requires_kernel else 'amdclang++');cmd=[compiler,'-std=c++17','-O2','-D__HIP_PLATFORM_AMD__'];includes += [core/'include',native/'include',ROOT/'build/deps/hipCOMP-core/include',ROOT/'build/project-sdk/include']+[native/'include'/n for n in ['hipblas','hipblaslt','hipsparse','hipsolver','hipfft','hiprand','hipsparselt']];links=['-L'+str(overlay/'lib'),'-L'+str(ROOT/'build/hipcomp/lib'),'-L'+str(ROOT/'build/project-sdk/lib'),'-Wl,-rpath,'+str(ROOT/'build/hipcomp/lib'),'-Wl,-rpath,'+str(ROOT/'build/project-sdk/lib'),'-Wl,-rpath,'+str(libs/'lib'),'-Wl,-rpath,'+str(core/'lib')]+['-l'+x for x in FAMILY_LIBS[family]+(['hipblas'] if family in {'cuSOLVER','cuSPARSE'} else [])]+['-lamdhip64']
   if not requires_kernel:cmd+=['-x','c++']
   if requires_kernel:cmd+=['--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-x','hip']
  source_hash=digest(source)
  cmd += [str(p) for p in sources]+['-o',str(binary)]+['-I'+str(p) for p in includes]+links
  (d/'commands.json').write_text(json.dumps({'cwd':str(ROOT),'build':cmd,'run':[str(binary)]},indent=2)+'\n');rc=command(cmd,ROOT,d/'build.log',env,180)
  if digest(source)!=source_hash:
   rc=75;log=d/'build.log';log.write_text(log.read_text()+'\nSOURCE_CHANGED_DURING_BUILD\n')
  return sample,d,binary,rc,source,source_hash
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
  futures=[pool.submit(build,s) for s in samples]
  for idx,future in enumerate(futures,1):
   sample,d,binary,rc,source,source_hash=future.result();level='L1';reason_code='BUILD_ERROR';stage='build'
   if rc==0:
    level='L2';stage='run';run_env=env.copy();run_env['MIGRATION_OUTPUT_DIR']=str(d);rc=command([str(binary)],source.parent,d/'run.log',run_env,args.timeout)
    if rc==0 and re.search(r'ERROR:.*failed|test FAILED|Aborted|terminate called',(d/'run.log').read_text(errors='replace'),re.I):rc=70
    if rc==0:level='L3';reason_code='INDEPENDENT_VALIDATION_PENDING'
    else:reason_code='TIMEOUT' if rc==124 else 'RUNTIME_ERROR'
   log=(d/('build.log' if stage=='build' else 'run.log')).read_text(errors='replace');errors=[x.strip() for x in log.splitlines() if re.search(r'error:|status=|failed|error [0-9]|undefined reference',x,re.I)];reason=('原始教学输入构建运行通过；独立正确性验证待完成' if rc==0 else f'{stage} 失败：'+('；'.join(errors[:2])[:650] or log[-450:].replace('\n',' ')))
   names=cuda_links[sample['family']] if cuda_mode else FAMILY_LIBS[sample['family']];result={'sample_id':sample['id'],'scope':'original_profile','backend':args.backend,'status':'EXECUTED' if rc==0 else 'FAILED','level':level,'return_code':rc,'reason_code':reason_code,'reason':reason,'attempted_libraries':names,'actual_library':'+'.join(names) if level in {'L2','L3'} else None,'backend_library':{'cuBLAS':'rocBLAS','cuBLASLt':'hipBLASLt','cuSPARSE':'rocSPARSE','cuSOLVER':'rocSOLVER','cuFFT':'rocFFT','cuRAND':'rocRAND','cuSPARSELt':'hipSPARSELt','cuTENSOR':'hipTensor','nvCOMP':'hipCOMP'}.get(sample['family'],'候选后端，尚待 API 改写验证'),'implementation':str(source.relative_to(ROOT)),'implementation_sha256':source_hash,'source_sha256':sample['source_sha256'],'evidence':str(d.relative_to(ROOT)),'environment':str((out/'environment.json').relative_to(ROOT)),'devices':identity.get('devices'),'qualified_physical_devices':not cuda_mode}
   if cuda_mode:result['backend_library']='CUDA vendor library; see attempted_libraries and link command'
   (d/'summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');update(sample['source'],result,args.backend);results.append(result);print(f'{idx}/{len(samples)} {sample["source"]}: {stage} rc={rc}',flush=True)
   if idx%25==0:
    checkpoint('批量原始 profile '+args.backend+f' {idx}/{len(samples)}',f'本轮已有 {sum(r["return_code"]==0 for r in results)} 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。','继续处理剩余样例','进行中')
   (out/'summary.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
  checkpoint('S15 '+args.backend+' 原始 profile 批次完成',f'{len(results)} 项中 {sum(r["return_code"]==0 for r in results)} 项构建运行通过，证据 {out.relative_to(ROOT)}；失败原因逐例入清单，尚待独立数值检查','修复共同问题并完成原始行为验收')
 report=ROOT/'migration/reports'/('original-'+args.backend+'-latest.json');old=json.loads(report.read_text()).get('results',[]) if report.exists() else [];merged={v['sample_id']:v for v in old};merged.update({v['sample_id']:v for v in results});report.write_text(json.dumps({'run_id':stamp,'results':list(merged.values())},indent=2,ensure_ascii=False)+'\n')
 print('Evidence:',out,flush=True)
if __name__=='__main__':main()
