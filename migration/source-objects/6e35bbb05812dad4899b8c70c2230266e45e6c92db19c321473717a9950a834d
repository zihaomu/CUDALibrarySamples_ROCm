#!/usr/bin/env python3
"""Compare every candidate CLI product with the previously qualified encoder."""
import json
from PIL import Image
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from audit import check as audit_check
from snapshot import capture

def main():
    profile=json.loads((ROOT/'migration/rewrite/image-encoder-instances-v2-profile.json').read_text())
    runs=json.loads((ROOT/'migration/reports/image-encoder-instances-v2-runs.json').read_text())
    prior=json.loads((ROOT/'migration/reports/image-encoder-pipeline-build.json').read_text())
    if prior['status']!='BUILT' or digest(ROOT/prior['binary'])!=prior['binary_sha256'] or any(digest(ROOT/n)!=h for n,h in prior['dependencies'].items()):raise ValueError('old qualified encoder identity drift')
    results=[]
    for case in profile['cases']:
        if not case['output']:continue
        run=next(r for r in runs if r['case']==case['id']);proof=ROOT/run['evidence']
        if run['status']!='PASSED' or audit_check(proof):raise ValueError('candidate not sealed/passed')
        e=Experiment('I5','async-original-CLI-byte-regression','rocm-reference',case=case['id'],sources=[__file__,ROOT/'migration/rewrite/image-encoder-instances-v2-profile.json',ROOT/'migration/reports/image-encoder-instances-v2-runs.json',*[ROOT/n for n in prior['dependencies']]],parent=run['experiment_id'])
        write(e.path/'backend.observed.json',capture());checks=[];compared=[];references={}
        for spec in profile['inputs'][:case['source_count']]:
            source=ROOT/spec['path']
            if digest(source)!=spec['sha256']:raise ValueError('frozen input drift')
            raw=e.path/(source.name+'.rgb')
            with Image.open(source) as image:
                image=image.convert('RGB');width,height=image.size;raw.write_bytes(image.tobytes())
            output=e.path/'reference'/source.name
            args=[str(ROOT/prior['binary']),str(raw),str(width),str(height),str(case['quality']),
                  '1' if case['sampling']==0 else '2',str(int('-f' in case['args'])),'0','1',str(output)]
            rc=e.command(args,'serial-GPU-core-independent-BMP-'+source.name)
            checks.append(dict(check='reference-command-'+source.name,passed=rc==0))
            references[source.name]=output/'serial-reference.jpg'
        for product in run['products']:
            new=proof/'products'/product['name'];old=references[product['source']]
            good=new.is_file() and old.is_file() and digest(new)==product['sha256']==digest(old)
            checks.append(dict(check='complete-JPEG-byte-exact-'+product['name'],passed=good))
            compared.append(dict(product=product['name'],exact=good))
        checks.append(dict(check='exact-reference-product-set',passed={str(p.relative_to(e.path/'reference')) for p in (e.path/'reference').rglob('*.jpg')}=={name+'/serial-reference.jpg' for name in references}))
        status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(case=case['id'],status=status,checks=checks,products=compared)
        write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks));results.append(row)
        write(ROOT/'migration/reports/image-encoder-instances-v2-comparison.json',results)
        record('IMG-01','v2 CLI '+case['id']+' 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：'+status+'，'+str(len(compared))+'件。',[row['evidence']]);print(case['id'],status,flush=True)
    return int(any(r['status']!='PASSED' for r in results))

if __name__=='__main__':raise SystemExit(main())
