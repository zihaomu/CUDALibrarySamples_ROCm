#!/usr/bin/env python3
"""Use original CMake recipes for CUDA callbacks, optionally with output-only observation/fixture override."""
import argparse,datetime,json,os,pathlib,subprocess
from catalog import ROOT
from run import command,digest
p=argparse.ArgumentParser();p.add_argument('--observed',action='store_true');p.add_argument('--fixture');args=p.parse_args();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'artifacts'/stamp/('cuda-callback-observed' if args.observed else 'cuda-callback-original');out.mkdir(parents=True);env=os.environ.copy();source=ROOT/('build/cuda-observed-fft' if args.observed else 'cuFFT/lto_callback_window_1d');build=ROOT/'build'/('cuda-observed-fft-build' if args.observed else 'original-cuda-fft-callback');configure=['cmake','-S',str(source),'-B',str(build),'-DCMAKE_CUDA_COMPILER=/usr/local/cuda-13.4/bin/nvcc','-DCUDAToolkit_ROOT=/usr/local/cuda-13.4','-DCMAKE_CUDA_ARCHITECTURES=120'];compile=['cmake','--build',str(build),'-j3'];(out/'commands.json').write_text(json.dumps({'configure':configure,'build':compile},indent=2)+'\n');rc=command(configure,ROOT,out/'configure.log',env,120)
if rc==0:rc=command(compile,ROOT,out/'build.log',env,300)
results=[]
for name in ['r2c_c2r_legacy_callback_example','r2c_c2r_lto_callback_example','r2c_c2r_lto_nvrtc_callback_example']:
 d=out/name;d.mkdir();binary=build/'bin'/name;e=env.copy();e['MIGRATION_OUTPUT_DIR']=str(d)
 if args.fixture:e['MIGRATION_INPUT_FIXTURE']=args.fixture
 code=rc if rc else command([str(binary)],ROOT,d/'run.log',e,120);r={'name':name,'status':'PASSED' if code==0 else 'FAILED','return_code':code,'evidence':str(d.relative_to(ROOT)),'scope':'Original mathematical CUDA calls with fixture override/observation only' if args.observed else 'Unmodified upstream CMake/source','visible_devices':env.get('CUDA_VISIBLE_DEVICES'),'fixture_sha256':digest(pathlib.Path(args.fixture)) if args.fixture else None};(d/'summary.json').write_text(json.dumps(r,indent=2)+'\n');results.append(r);print(r,flush=True)
(ROOT/'migration/reports'/('cuda-callback-observed.json' if args.observed else 'cuda-callback-original.json')).write_text(json.dumps(results,indent=2)+'\n')
