#!/usr/bin/env python3
"""Recheck actual sealed CUDA recipe, receipt and complete Hough PPM difference."""
import ast,hashlib,json,re,shlex
from pathlib import Path
import numpy as np
from experiment import ROOT,digest
from image_hough_reference import LINE,TRUTH

def receipt_code():
    tree=ast.parse((ROOT/'tools/moat/image_regions_native.py').read_text())
    matches=[n.value.value for n in ast.walk(tree) if isinstance(n,ast.Assign)
             and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets)
             and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str)]
    if len(matches)!=1:raise ValueError('one fixed native execution receipt recipe')
    return matches[0]

def lines(text):return [(int(float(rho)),int(float(theta))) for theta,rho in LINE.findall(text)]

def validate(original,project,comparison):
    nd=ROOT/original['evidence'];pd=ROOT/project['evidence']
    commands=json.loads((nd/'commands.json').read_text())
    logged=(nd/commands[4]['stdout']).read_text();receipt=json.loads(logged.splitlines()[0])
    config=original['config'];remote=original['remote'];source=original['source']
    expected_phases=['prepare-private-full-original','upload-unmodified-sources-and-exact-inputs',
                     'extract-private-original','compile-complete-unmodified-original',
                     'actual-complete-native-default-with-source-input-library-GPU-receipt',
                     'collect-all-inputs-products-and-original-workflow-files']
    compile=shlex.split(commands[3]['argv'][-1]);execute=shlex.split(commands[4]['argv'][-1])
    expected_compile=['/usr/local/cuda-13.4/bin/nvcc','-O2','-std=c++17','-arch=sm_120',
                      '-lnppif','-lnppig','-lnppicc','-lnppc',remote+'/houghLines.cpp',
                      '-o',remote+'/original']
    expected_execute=['env','CUDA_VISIBLE_DEVICES=1','python3','-c',receipt_code(),
                      json.dumps(config,separators=(',',':'))]
    nfile=nd/'outputs/work/hough_result.ppm';pfile=ROOT/json.loads((pd/'manifest.json').read_text())['raw_artifact_dir']/'outputs/hough_result.ppm'
    nbytes,pbytes=nfile.read_bytes(),pfile.read_bytes();header=b'P6\n1024 768\n255\n'
    if not nbytes.startswith(header) or not pbytes.startswith(header) or len(nbytes)!=len(pbytes):raise ValueError('native/project complete PPM shape')
    n=np.frombuffer(nbytes[len(header):],np.uint8).reshape(768,1024,3)
    p=np.frombuffer(pbytes[len(header):],np.uint8).reshape(768,1024,3)
    nr=np.all(n==[255,40,40],axis=2);pr=np.all(p==[255,40,40],axis=2)
    inter=int(np.count_nonzero(nr&pr));union=int(np.count_nonzero(nr|pr))
    nl=lines(logged);pl=lines((pd/'logs/0001-execute-complete-Hough-entry.stdout.log').read_text())
    libs=receipt['libraries']
    result=dict(native_lines=nl,project_lines=pl,native_line_count=len(nl),project_line_count=len(pl),
                differing_RGB_pixels=int(np.count_nonzero(np.any(n!=p,axis=2))),
                red_line_IoU=inter/union if union else 1.,native_red_pixels=int(np.count_nonzero(nr)),
                project_red_pixels=int(np.count_nonzero(pr)),native_ppm_sha256=digest(nfile),
                project_ppm_sha256=digest(pfile))
    checks=[
        dict(check='sealed-native-source-run-and-actual-CUDA-command-recipe',passed=
             json.loads((nd/'run.json').read_text())=={k:v for k,v in original.items() if k!='evidence'}
             and source=='NPP/houghLines/houghLines.cpp' and digest(ROOT/source)==original['source_sha256']==config['source_sha256']==receipt['source_sha256']
             and config==dict(remote=remote,source='houghLines.cpp',source_sha256=original['source_sha256'],headers={},inputs={})
             and [c['phase'] for c in commands]==expected_phases and len(commands)==6
             and all(c['return_code']==0 and c['cwd']==str(ROOT) for c in commands)
             and commands[3]['argv'][:2]==commands[4]['argv'][:2]==['ssh','nvidia-5090x2']
             and compile==expected_compile and execute==expected_execute),
        dict(check='actual-5090-binary-NPP-library-and-device-receipt',passed=
             original['status']=='EXECUTED' and original['build_return_code']==original['return_code']==original['collection_return_code']==0
             and receipt['physical_device_index']==1 and receipt['CUDA_VISIBLE_DEVICES']=='1' and '5090' in receipt['device']
             and re.fullmatch('[0-9a-f]{64}',receipt['binary_sha256']) is not None
             and any('libnppif.so' in name for name in libs) and any('libnppc.so' in name for name in libs)
             and all(v['bytes']>0 and re.fullmatch('[0-9a-f]{64}',v['sha256']) for v in libs.values())
             and all(name in receipt['loader'] for name in ['libnppif.so','libnppc.so'])),
        dict(check='complete-native-and-project-PPM-file-identities',passed=
             result['native_ppm_sha256']==original['files']['work/hough_result.ppm']['sha256']
             and len(nbytes)==original['files']['work/hough_result.ppm']['bytes']
             and result['project_ppm_sha256']==project['ppm_sha256']
             and len(pbytes)==project['ppm_bytes']),
        dict(check='ten-actual-lines-and-five-truth-geometries',passed=
             len(nl)==len(pl)==10 and all(any(abs(r-r0)<=3 and abs(t-t0)<=1 for r,t in rows)
                                          for rows in (nl,pl) for r0,t0 in TRUTH)),
        dict(check='recomputed-full-pixel-difference-equals-comparison-proof',passed=
             all(comparison[k]==json.loads(json.dumps(v)) for k,v in result.items()) and comparison['status']=='PASSED'
             and comparison['native_evidence']==original['evidence']
             and comparison['project_evidence']==project['evidence'])]
    return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,metrics=result)
