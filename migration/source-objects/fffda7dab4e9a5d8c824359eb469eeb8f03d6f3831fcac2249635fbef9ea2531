#!/usr/bin/env python3
"""Bind integrated original-entry outputs to independently validated arithmetic."""
import argparse,json,shutil
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_encoder_math_binding import sealed
from image_encoder_quality_run import arguments

def main(matrix):
    from snapshot import capture
    names={'fresh':('image-encoder-math-variant-v2-profile.json','image-encoder-math-amd.json','image-encoder-math-cpu.json'),
           'development':('image-encoder-quality-profile.json','image-encoder-math-history-development-amd.json','image-encoder-math-history-development-cpu.json'),
           'heldout':('image-encoder-quality-holdout-v2-profile.json','image-encoder-math-history-heldout-amd.json','image-encoder-math-history-heldout-cpu.json')}
    pn,rn,qn=names[matrix];profile=ROOT/'migration/rewrite'/pn;runs_path=ROOT/'migration/reports'/rn;quality_path=ROOT/'migration/reports'/qn
    p=json.loads(profile.read_text());runs=json.loads(runs_path.read_text());quality=json.loads(quality_path.read_text())
    expected=[c['id'] for c in p['cases']]
    if len(expected)!=80 or [r['case'] for r in runs]!=expected or [r['case'] for r in quality]!=expected:raise ValueError('complete 80 cases required')
    for row in runs+quality:
        sealed(row)
        if row['status']!='PASSED' or not all(c['passed'] for c in row['checks']):raise ValueError('independent candidate quality did not pass')
    bp=ROOT/'migration/reports/image-encoder-instances-v2-build.json';b=json.loads(bp.read_text());sealed(b,'build.json')
    if b['status']!='BUILT' or digest(ROOT/b['binary'])!=b['binary_sha256'] or any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()):raise ValueError('stale production build')
    refs={b['evidence']};extra=[]
    if matrix=='fresh':
        binding_path=ROOT/'migration/reports/image-encoder-math-binding.json';binding=json.loads(binding_path.read_text());sealed(binding)
        if binding['status']!='PASSED':raise ValueError('fresh oracle binding required')
        refs.add(binding['evidence']);extra.append(binding_path)
    e=Experiment('I5','encoder-integrated-mathematics-'+matrix,'rocm-original',sources=[__file__,ROOT/'tools/moat/image_encoder_quality_run.py',ROOT/'tools/moat/image_encoder_math_binding.py',profile,runs_path,quality_path,bp,*extra,*[ROOT/i['path'] for i in p['inputs']],*[ROOT/n for n in b['dependencies']]])
    write(e.path/'backend.observed.json',capture());checks=[];results=[]
    try:
        inputs=e.path/'inputs';inputs.mkdir()
        for item in p['inputs']:
            source=ROOT/item['path']
            if digest(source)!=item['sha256']:raise ValueError('frozen BMP drift')
            folder=inputs/item['id'];folder.mkdir();shutil.copyfile(source,folder/'image.bmp')
        for case,run,comparison in zip(p['cases'],runs,quality):
            product=run['products'][0];oracle=ROOT/product['path']
            if digest(oracle)!=product['sha256'] or oracle.stat().st_size!=product['bytes']:raise ValueError('validated isolated JPEG drift')
            output=e.path/'products'/case['id'];output.mkdir(parents=True)
            rc=e.command(arguments(case,ROOT/b['binary'],inputs/case['input'],output),'integrated-'+case['id'],timeout=300)
            actual=output/'0.jpg';passed=rc==0 and {f.name for f in output.iterdir()}=={'0.jpg'} and actual.stat().st_size==product['bytes'] and digest(actual)==product['sha256']
            checks.append(dict(check=case['id'],passed=passed));refs.update([run['evidence'],comparison['evidence'],*comparison['evidence_references']])
            results.append(dict(case=case['id'],status='PASSED' if passed else 'FAILED',JPEG_sha256=digest(actual) if actual.exists() else None,independent_quality_evidence=comparison['evidence'],isolated_run_evidence=run['evidence']))
            print(matrix,case['id'],results[-1]['status'],flush=True)
            if not passed:break
    except Exception as error:checks.append(dict(check='production-validation-exception',passed=False,error=repr(error)))
    status='PASSED' if len(results)==80 and all(c['passed'] for c in checks) else 'FAILED';row=dict(status=status,checks=checks,cases=results,binary_sha256=b['binary_sha256'],dependencies=b['dependencies'],evidence_references=sorted(refs),
        scope='Integrated original-entry JPEGs byte-exact against independently mathematically qualified isolated products. Output identity transfers those numerical results; performance and full entry qualification remain separate.')
    write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks));write(ROOT/f'migration/reports/image-encoder-math-production-{matrix}.json',row)
    record('IMG-01','正式整合入口数学回归 '+matrix+'：'+status+'，'+str(len(results))+'/80产品完整字节与已独立验收候选一致；当前源码/原命令及数学证据引用绑定。',[row['evidence']]);print(status);return int(status!='PASSED')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('matrix',choices=['fresh','development','heldout']);args=parser.parse_args();raise SystemExit(main(args.matrix))
