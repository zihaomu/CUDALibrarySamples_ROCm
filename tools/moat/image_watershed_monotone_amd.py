#!/usr/bin/env python3
"""Verify the extra analytic ramps on real HIP, without vendor-dependent tolerance."""
import json
from experiment import ROOT,Experiment,digest,write
from snapshot import capture
from image_completion_progress import record

def main():
    pp=ROOT/'migration/rewrite/image-watershed-monotone-native-profile.json';p=json.loads(pp.read_text());bp=ROOT/'migration/reports/image-watershed-v2-build.json';b=json.loads(bp.read_text());binary=ROOT/b['binary']['path'];folder=ROOT/'migration/fixtures/image-watershed-monotone-native'
    if digest(binary)!=b['binary']['sha256'] or any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()):raise ValueError('current AMD build required')
    e=Experiment('I3','watershed-analytic-monotone-AMD','rocm',sources=[__file__,pp,bp,binary,*[ROOT/n for n in b['dependencies']],folder/'cases.txt',*[ROOT/i['path'] for i in p['inputs']]]);write(e.path/'backend.observed.json',capture());rc=e.command([str(binary),str(folder),str(e.path/'outputs'),'padded'],'analytic-ramp-corpus',timeout=600)
    products={f.name:dict(bytes=f.stat().st_size,sha256=digest(f)) for f in (e.path/'outputs').glob('*') if f.is_file()};checks=[]
    if not rc:
        for item in p['inputs']:
            for suffix,value in [('segments',0),('black',0),('white',0),('contrast',0),('boundaries',255)]:
                actual=(e.path/'outputs'/(item['id']+'.'+suffix)).read_bytes();checks.append(dict(check=item['id']+'-'+suffix,passed=actual==bytes([value])*item['bytes']))
    checks.append(dict(check='complete24-analytic-ramp-products',passed=rc==0 and len(products)==168))
    status='PASSED' if all(c['passed'] for c in checks) else 'NUMERIC_MISMATCH';result=dict(status=status,return_code=rc,checks=checks,products=products,build_evidence=b['evidence'],scope='Five image outputs compared with the independently known all-zero terminal image of each strictly monotone ramp; no native tolerance. Marker evidence remains in the full SCC corpus.');write(e.path/'result.json',result);result['evidence']=e.finish(status,dict(status=status,checks=checks));write(ROOT/'migration/reports/image-watershed-monotone-AMD.json',result)
    record('IMG-02','24个额外解析坡度在实际HIP上对零终点/五图像模式精确验收：'+status+'；没有复制NPP+的非零传播残留。',[result['evidence']]);print(status,result['evidence']);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
