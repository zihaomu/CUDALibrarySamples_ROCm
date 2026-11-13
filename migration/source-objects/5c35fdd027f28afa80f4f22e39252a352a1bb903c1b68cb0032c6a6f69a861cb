#!/usr/bin/env python3
"""Check every development output against independent graph and native image oracles."""
import argparse,json
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_encoder_math_binding import sealed
from image_watershed_graph_reference import reference,topology
from image_watershed_semantics_reference import canonical

ACTIVE=None

def bound(row,filename='result.json'):
    proof=sealed(row,filename);manifest=json.loads((proof/'manifest.json').read_text());raw=ROOT/manifest['raw_artifact_dir']/'outputs';seal=json.loads((proof/'sealed.json').read_text())['files']
    for name,identity in row['products'].items():
        f=raw/name
        if identity!=seal['outputs/'+name] or f.stat().st_size!=identity['bytes'] or digest(f)!=identity['sha256']:raise ValueError('product identity '+name)
    return raw

def main(mode):
    global ACTIVE
    pp=ROOT/'migration/rewrite/image-watershed-semantics-profile.json';profile=json.loads(pp.read_text());rp=ROOT/f'migration/reports/image-watershed-v2-development-{mode}.json';run=json.loads(rp.read_text());npth=ROOT/'migration/reports/image-watershed-semantics-NPP.json';native=json.loads(npth.read_text())
    e=Experiment('I3','watershed-directed-marker-independent-SCC-'+mode,'CPU-reference',sources=[__file__,pp,rp,npth,ROOT/'tools/moat/image_watershed_graph_reference.py',ROOT/'tools/moat/image_watershed_semantics_reference.py',ROOT/'tools/moat/image_encoder_math_binding.py',*[ROOT/i['path'] for i in profile['inputs']]])
    ACTIVE=e;raw=bound(run,'run.json');nr=bound(native)
    rows=[];checks=[];all_names=[]
    for item in profile['inputs']:
        source=ROOT/item['path']
        if digest(source)!=item['sha256']:raise ValueError('source drift')
        shape=item['height'],item['width'];a=np.fromfile(source,np.uint8).reshape(shape);expected,graph=reference(a);eq={};vendor={}
        for suffix,array in expected.items():
            name=item['id']+'.'+suffix;all_names.append(name);eq[suffix]=(raw/name).read_bytes()==array.tobytes()
        for suffix,m in [('segments',0),('black',1),('white',2),('contrast',3),('boundaries',4)]:
            vendor[suffix]=expected[suffix].tobytes()==(nr/(item['id']+f'-n8-m{m}-r0.segments')).read_bytes()
        topo=topology(expected['labels'],expected['segments']);nl=np.fromfile(nr/(item['id']+'-n8-m0-r0.labels'),'<u4').reshape(shape)
        row=dict(case=item['id'],CPU_exact=eq,native_image_exact=vendor,topology=topo,native_partition_exact=bool(np.array_equal(canonical(expected['labels']),canonical(nl))),SCC_components=graph['seed_components']);rows.append(row)
        checks += [dict(check=item['id']+'-7-CPU-products',passed=all(eq.values())),dict(check=item['id']+'-5-native-image-modes',passed=all(vendor.values())),dict(check=item['id']+'-region-topology',passed=topo['all_regions_connected'] and topo['all_regions_constant_gray'])]
        print(row,flush=True)
    checks.append(dict(check='complete-exact126-products',passed=len(all_names)==126 and set(run['products'])==set(all_names)))
    status='PASSED' if all(x['passed'] for x in checks) else 'NUMERIC_MISMATCH';result=dict(status=status,mode=mode,checks=checks,rows=rows,evidence_references=[run['evidence'],native['evidence']],scope='Isolated component development check; marker algorithm variant is not yet an original-entry qualification.');write(e.path/'reference.json',result);result['evidence']=e.finish(status,dict(status=status,checks=checks));write(ROOT/f'migration/reports/image-watershed-v2-reference-{mode}.json',result)
    record('IMG-02','HIP开发候选'+mode+'经独立SCC凝聚DAG oracle核对126件完整产品、90件原生图像模式及逐区域连通/恒灰：'+status+'；marker变体仍需合同/保留集/完整入口验收。',[result['evidence']]);return int(status!='PASSED')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',default='padded');a=p.parse_args()
    try:result=main(a.mode)
    except Exception as error:
        if ACTIVE is not None and not ACTIVE.sealed:
            ref=ACTIVE.finish('VALIDATOR_GAP',reason=repr(error));record('IMG-02','独立SCC验证器异常已封存：'+repr(error),[ref])
        raise
    raise SystemExit(result)
