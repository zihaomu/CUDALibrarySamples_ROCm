#!/usr/bin/env python3
"""Rebuild and replay original profiles inside a fresh checkout, without old binaries."""
import json,os,shutil,subprocess,sys,time
from pathlib import Path
from experiment import ROOT,write,digest
from snapshot import capture

def main():
    work=ROOT/'build/clean-replay';work.mkdir(parents=True,exist_ok=False);commands=[];cases=[]
    initial=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)
    if initial:raise RuntimeError('Fresh checkout is dirty before replay: '+initial)
    def run(argv,name,cwd=ROOT,env=None):
        started=time.time();stdout=work/(name+'.stdout.log');stderr=work/(name+'.stderr.log')
        with stdout.open('w') as o,stderr.open('w') as e:
            result=subprocess.run(list(map(str,argv)),cwd=cwd,env=dict(os.environ,**(env or {})),stdout=o,stderr=e,timeout=480)
        commands.append(dict(argv=list(map(str,argv)),cwd=str(cwd),env=env or {},return_code=result.returncode,seconds=time.time()-started,stdout=str(stdout.relative_to(ROOT)),stderr=str(stderr.relative_to(ROOT))))
        if result.returncode:raise RuntimeError(name+' exit '+str(result.returncode))
        return stdout
    result=dict(status='RUNNING',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),initial_clean=True,environment=capture(),commands=commands,cases=cases,
        scope='Fresh M1 plus all 21 newly qualified original AMD profiles and independent CPU checks; historical raw outputs/native CUDA binaries are not copied or regenerated')
    try:
        run(['python3','tools/migration/bootstrap_sdk.py'],'bootstrap-overlay')
        run(['cmake','-S','rocm','-B','build/clean-cmake','-DCMAKE_BUILD_TYPE=Release'],'configure')
        run(['cmake','--build','build/clean-cmake','-j4'],'build-M1')
        first=json.loads((ROOT/'migration/rewrite/first-eight.json').read_text())['profiles']
        extensions=json.loads((ROOT/'migration/rewrite/extensions.json').read_text())['profiles']
        targets=['rewrite_'+p['kind'] for p in first]+['rewrite_ext_'+p['kind'] for p in extensions]+['rewrite_sparse_bindings']
        run(['cmake','--build','build/clean-cmake','--target']+targets+['-j4'],'build-rewrites')
        testlog=run(['ctest','--test-dir','build/clean-cmake','--output-on-failure','--parallel','1'],'CTest')
        if '100% tests passed, 0 tests failed out of 16' not in testlog.read_text():raise RuntimeError('CTest denominator')
        import first_reference,svd_reference,sparse24_reference,sparse_binding_reference,ncc_reference,crc32_reference
        def binary_case(kind,sample,src,binary,validator):
            out=work/('output-'+kind);out.mkdir();env=dict(REWRITE_INPUT=str(src),REWRITE_OUTPUT=str(out));log=run([binary],'run-'+kind,env=env)
            checked=validator(out);write(work/('validation-'+kind+'.json'),checked)
            if checked['status']!='PASSED' or not checked.get('checks') or not all(c['passed'] for c in checked['checks']):raise RuntimeError('CPU oracle '+kind)
            cases.append(dict(sample_id=sample,kind=kind,case='original',status='PASSED',binary_sha256=digest(binary),input_manifest_sha256=digest(src/'manifest.json'),checks=checked['checks']))
        for p in first:
            kind=p['kind'];src=ROOT/'tests/fixtures/rewrite-first'/kind/'original';binary=ROOT/'build/clean-cmake'/('rewrite_'+kind+'.bin')
            binary_case(kind,p['sample_id'],src,binary,lambda out,k=kind,s=src:first_reference.validate(k,'original',out,inputs=s))
        for p in extensions:
            kind=p['kind'];binary=ROOT/'build/clean-cmake'/('rewrite_ext_'+kind+'.bin');out=work/('output-'+kind)
            if kind in ['svd','sparse24','sparse24_advanced']:
                src=ROOT/'tests/fixtures/rewrite-extensions'/kind/'original';validator=(lambda o,s=src:svd_reference.validate(s,o)) if kind=='svd' else (lambda o,s=src:sparse24_reference.validate(s,o))
                binary_case(kind,p['sample_id'],src,binary,validator)
            elif kind=='crc32':
                src=ROOT/'tests/fixtures/rewrite-extensions/crc32/original';out.mkdir();mf=json.loads((src/'manifest.json').read_text())
                run([binary]+mf['argv'],'run-crc32',cwd=src,env=dict(REWRITE_OUTPUT=str(out)));checked=crc32_reference.validate(src,out);write(work/'validation-crc32.json',checked)
                if checked['status']!='PASSED':raise RuntimeError('CRC oracle')
                cases.append(dict(sample_id=p['sample_id'],kind=kind,case='original',status='PASSED',binary_sha256=digest(binary),checks=checked['checks']))
            elif kind=='ncc':
                out.mkdir();cwd=work/'ncc-work';cwd.mkdir();(work/'images').mkdir();shutil.copyfile(ROOT/'NPP/templateMatching/images/CircuitBoard_2048x1024_8u.raw',work/'images/CircuitBoard_2048x1024_8u.raw')
                log=run([binary],'run-ncc',cwd=cwd,env=dict(REWRITE_OUTPUT=str(out)));shutil.copyfile(cwd/'match_result.pgm',out/'match_result.pgm');checked=ncc_reference.validate(out,log);write(work/'validation-ncc.json',checked)
                if checked['status']!='PASSED':raise RuntimeError('NCC oracle')
                cases.append(dict(sample_id=p['sample_id'],kind=kind,case='original',status='PASSED',binary_sha256=digest(binary),checks=checked['checks']))
        bindings=json.loads((ROOT/'migration/rewrite/sparse-bindings.json').read_text())['profiles'];build=json.loads((ROOT/'migration/reports/rewrite-sparse-binding-build.json').read_text())
        for p in bindings:
            binary=ROOT/next(b['binary'] for b in build['binaries'] if b['sample_id']==p['sample_id']);src=ROOT/p['fixture_root']/'original';kind=p['language']+'-'+p['kind']
            binary_case(kind,p['sample_id'],src,binary,lambda out,s=src:sparse_binding_reference.validate(s,out))
        expected={p['sample_id'] for p in first+extensions+bindings}
        if len(cases)!=21 or {c['sample_id'] for c in cases}!=expected:raise RuntimeError('21-profile denominator')
        result.update(status='PASSED',m1_tests=16,new_original_profiles=len(cases),historical_artifacts_reused=False)
    except Exception as error:
        result.update(status='FAILED',error=str(error))
    finally:
        write(work/'result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['commands','cases','environment']}))
    return int(result['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
