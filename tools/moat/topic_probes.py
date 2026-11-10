#!/usr/bin/env python3
"""Concrete capability probes for R4/R6; no source entrypoint is promoted here."""
import argparse,json,sys,time,importlib.util,importlib.metadata,re
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
p=argparse.ArgumentParser();p.add_argument('--distributed',action='store_true');args=p.parse_args();core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');native=Path('/opt/rocm/core-10.1');libs=[native/'lib',core.parent/'_rocm_sdk_libraries/lib',core/'lib'];observed=capture();records=[]
def compile_command(source,binary,links):return ['amdclang++','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__',str(source),'-I'+str(ROOT/'rocm/common'),'-I'+str(core/'include'),'-I'+str(native/'include'),'-o',str(binary)]+['-L'+str(p) for p in libs]+['-Wl,-rpath,'+str(p) for p in libs]+['-l'+name for name in links]
if args.distributed:
 e=Experiment('R6','distributed-two-physical-GPU-foundation','rocm-capability-probe',sources=[__file__,ROOT/'rocm/probes/rccl_gemm.cpp',ROOT/'rocm/common/check.hpp']);write(e.path/'backend.observed.json',observed);devices=observed['devices'];checks=[dict(check='two-distinct-safe-physical-GPUs',passed=len(devices)==2 and len({d['physical_id'] for d in devices})==2 and all(d['physical_id']!=3 for d in devices))]
 # Correctness probe has a few dozen tensor elements; no timing is qualified.
 # Record occupancy and avoid a heavily occupied card or low free memory.
 time.sleep(2)
 import ctypes
 hip=ctypes.CDLL(str(core/'lib/libamdhip64.so.7'));availability=[]
 for d in devices:
  hip.hipSetDevice(d['logical_id']);free=ctypes.c_size_t();total=ctypes.c_size_t();rc=hip.hipMemGetInfo(ctypes.byref(free),ctypes.byref(total));busy_file=Path('/sys/bus/pci/devices')/d['pci_bdf']/'gpu_busy_percent';busy=int(busy_file.read_text()) if busy_file.exists() else None;availability.append(dict(device=d,free=free.value,total=total.value,busy_percent=busy,return_code=rc))
 write(e.path/'availability.json',availability)
 if not all(c['passed'] for c in checks) or any(a['return_code'] or a['free']<.9*a['total'] or a['busy_percent'] is None or a['busy_percent']>10 for a in availability):
  r=dict(status='ENV_BLOCKED',scope='Tiny functional two-GPU probe; no timing claims',availability=availability);r['evidence']=e.finish('ENV_BLOCKED',reason='Need two safe physical GPUs with sufficient free memory and low occupancy');write(ROOT/'migration/reports/rewrite-R6-distributed-probe.json',r);print(r['status']);raise SystemExit(0)
 binary=e.path/'rccl-foundation';rc=e.command(compile_command(ROOT/'rocm/probes/rccl_gemm.cpp',binary,['rccl','hipblas','amdhip64']),'build-two-GPU-probe');run=rc or e.command([str(binary)],'actual-two-device-GEMM-AllGather');checks.append(dict(check='actual-two-device-local-GEMM-and-AllGather',passed=run==0));r=dict(status='PASSED_CAPABILITY' if all(c['passed'] for c in checks) else 'FAILED_CAPABILITY',checks=checks,devices=devices,scope='Tiny single-process two-device local GEMM + AllGather only; no MPI descriptor/submatrix/dtype/multi-node or timing qualification');write(e.path/'capability.json',r);r['evidence']=e.finish('PASSED' if all(c['passed'] for c in checks) else 'PROBE_FAILED',dict(checks=checks));write(ROOT/'migration/reports/rewrite-R6-distributed-probe.json',r);print(r['status']);raise SystemExit(0)
for name,source,links,inputs in [
 ('runtime-AMD-codegen','rocm/probes/rewrite_jit_foundation.cpp',['hiprtc','amdhip64'],[None]),
 ('JPEG-parser-format-boundary','rocm/probes/rewrite_codec_formats.cpp',['rocjpeg','amdhip64'],['nvJPEG2000/nvJPEG2000-Decoder/images/2k_image_lossless/2k_lossless.jp2','nvTIFF/images/bali_notiles.tif'])]:
 e=Experiment('R6',name,'rocm-capability-probe',sources=[__file__,ROOT/source,ROOT/'rocm/common/check.hpp']);write(e.path/'backend.observed.json',observed);binary=e.path/'probe';rc=e.command(compile_command(ROOT/source,binary,links),'build');runs=[]
 if rc==0:
  input_identity={item:dict(sha256=digest(ROOT/item),bytes=(ROOT/item).stat().st_size) for item in inputs if item};write(e.path/'input-identity.json',input_identity)
  for item in inputs:runs.append(dict(input=item,input_identity=input_identity.get(item),return_code=e.command([str(binary)]+([str(ROOT/item)] if item else []),'probe-'+('JIT' if item is None else Path(item).suffix[1:]))))
 checks=[dict(check=name,passed=rc==0 and bool(runs) and all(r['return_code']==0 for r in runs))];r=dict(name=name,status='PASSED_CAPABILITY' if all(c['passed'] for c in checks) else 'FAILED_CAPABILITY',checks=checks,runs=runs,scope='HIPRTC real generation/load/launch' if name.startswith('runtime') else 'Real rocJPEG stream parser rejects JP2/TIFF; does not evaluate hipCIM or qualify a codec implementation');write(e.path/'capability.json',r);r['evidence']=e.finish('PASSED' if all(c['passed'] for c in checks) else 'PROBE_FAILED',dict(checks=checks));records.append(r);write(ROOT/'migration/reports/rewrite-R6-foundation-probes.json',dict(profiles=records));print(name,r['status'],flush=True)
# Probe installed AMD header/library and Python surfaces without inventing a GPU backend.
e=Experiment('R4-R6','installed-SDK-surfaces','rocm-capability-probe',sources=[__file__]);write(e.path/'backend.observed.json',observed);headers=['cuest.h','cupqc.hpp','cuhash.hpp','cublasdx.hpp','cufftdx.hpp','curanddx.hpp','cusolverdx.hpp','nvcompdx.hpp','libcublasdx.h','libcufftdx.h','libnvcompdx.h','nvjpeg2k.h','nvtiff.h'];header_rows=[]
for header in headers:
 source=e.path/(header.replace('.','_')+'.cpp');source.write_text('#include <'+header+'>\n');rc=e.command(['amdclang++','-D__HIP_PLATFORM_AMD__','-std=c++17','-fsyntax-only','-I'+str(core/'include'),'-I'+str(native/'include'),str(source)],'original-header-'+header.replace('.','_'));header_rows.append(dict(header=header,return_code=rc,scope='Original vendor include availability in the locked AMD SDK; absence is not algorithm impossibility'))
library_rows=[]
patterns=['irs','gels','gesvd','geev','csrqr','csrrf','cascaded','zstd','deflate','gdeflate','bitcomp','ans','lz4','snappy','hough','watershed','label','contour','hiprtc','hipcim','cuest']
paths=[core.parent/'_rocm_sdk_libraries/lib'/name for name in ['libhipsolver.so.1','librocsolver.so.0','libhipsparse.so.1','libhipsparselt.so.0','librocjpeg.so.1','librccl.so.1']]+[ROOT/'build/hipcomp/lib/libhipcomp.so']
for library in paths:
 if not library.is_file():library_rows.append(dict(path=str(library),status='NOT_INSTALLED_AT_PROBED_PATH'));continue
 rc=e.command(['nm','-D',str(library)],'symbols-'+library.name,timeout=60);text=(e.path/e.commands[-1]['stdout']).read_text();matches=[line for line in text.splitlines() if any(pattern in line.lower() for pattern in patterns)];library_rows.append(dict(path=str(library),sha256=digest(library),return_code=rc,symbols=matches,scope='Symbol availability only; actual GPU execution must be verified per sample'))
modules={}
for name in ['cucim','cupy','cuest','gauxc','libintx']:
 try:modules[name]=dict(available=importlib.util.find_spec(name) is not None)
 except Exception as error:modules[name]=dict(available=False,reason=str(error))
data=dict(headers=header_rows,libraries=library_rows,python_modules=modules,environment=observed,scope='Installed capabilities and prerequisites only; no whole-source sample pass inferred');write(e.path/'surfaces.json',data);data['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/rewrite-R4-R6-SDK-surfaces.json',data);print(data['evidence'])
