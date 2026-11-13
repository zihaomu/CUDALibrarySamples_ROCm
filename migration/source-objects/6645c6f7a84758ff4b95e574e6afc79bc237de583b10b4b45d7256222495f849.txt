#!/usr/bin/env python3
"""Require the real byte, topology, adjacency and seal validators to reject faults."""
import copy,json
import numpy as np
from experiment import ROOT,Experiment,write
from image_completion_progress import record
from image_watershed_graph_reference import reference,topology,output_checks
from image_watershed_region_metrics import adjacency
from image_watershed_v2_reference import bound

def main():
    pp=ROOT/'migration/rewrite/image-watershed-completion-contract.json';p=json.loads(pp.read_text());rp=ROOT/'migration/reports/image-watershed-completion-AMD-padded.json';run=json.loads(rp.read_text());npth=ROOT/'migration/reports/image-watershed-completion-native-NPP.json';native=json.loads(npth.read_text());folder=bound(run);bound(native)
    item=next(i for i in p['inputs'] if i['id'].startswith('heldout-noise-256-'));a=np.fromfile(ROOT/item['path'],np.uint8).reshape(item['height'],item['width']);expected,_=reference(a);base={s:(folder/(item['id']+'.'+s)).read_bytes() for s in expected}
    e=Experiment('I3','watershed-validator-negative-controls','CPU-controls',sources=[__file__,pp,rp,npth,ROOT/item['path'],ROOT/'tools/moat/image_watershed_graph_reference.py',ROOT/'tools/moat/image_watershed_region_metrics.py',ROOT/'tools/moat/image_watershed_v2_reference.py',ROOT/'tools/moat/image_encoder_math_binding.py'])
    checks=[dict(check='actual-GPU-positive-control-all-seven-products',passed=all(output_checks(expected,base).values()))]
    def reject(name,modified):checks.append(dict(check=name,passed=not all(output_checks(expected,modified).values())))
    labels=expected['labels'];unique,counts=np.unique(labels,return_counts=True)
    for name,change in [('one-label-image',lambda v:v.fill(0)),('merge-distinct-regions',lambda v:v.__setitem__(v==unique[1],unique[0])),('split-one-region',lambda v:v.__setitem__((0,0),int(unique.max())+1)),('drop-small-region',lambda v:v.__setitem__(v==unique[np.argmin(counts)],unique[np.argmax(counts)])),('unconverged-marker-result',lambda v:v.__setitem__(slice(None),np.arange(v.size,dtype=np.uint32).reshape(v.shape)))]:
        v=labels.copy();change(v);m=base.copy();m['labels']=v.tobytes();reject(name,m)
    m=base.copy();v=expected['compact'].copy();v[v==1]=0;m['compact']=v.tobytes();reject('nonbijective-compact',m)
    for name,suffix in [('alter-one-gray-pixel','segments'),('alter-one-boundary-pixel','boundaries')]:
        m=base.copy();v=bytearray(m[suffix]);v[0]^=1;m[suffix]=bytes(v);reject(name,m)
    m=base.copy();m.pop('white');reject('missing-product',m);m=base.copy();m['black']+=b'\x00';reject('trailing-bytes',m)
    separate,_=reference(np.array([[0,255,255,255,0]],np.uint8));bad=separate['labels'].copy();bad[bad==bad[0,-1]]=bad[0,0];bad_topo=topology(bad,separate['segments'])
    checks.append(dict(check='reuse-label-on-disconnected-regions',passed=not bad_topo['all_regions_connected']))
    first=np.array([[0,0],[1,0]],np.uint32);second=np.array([[0,0],[1,1]],np.uint32)
    def old_mask(v):
        edge=np.zeros(v.shape,bool);edge[1:]|=v[1:]!=v[:-1];edge[:,1:]|=v[:,1:]!=v[:,:-1];return edge
    edges=adjacency(first,second);checks.append(dict(check='OR-mask-hides-horizontal-vs-vertical-edges',passed=np.array_equal(old_mask(first),old_mask(second)) and edges['agreement']<1))
    for name,modify in [('wrong-native-product-SHA',lambda r:r['products'][next(iter(r['products']))].__setitem__('sha256','0'*64)),('missing-seal',lambda r:r.__setitem__('evidence',str((e.path/'missing-seal').relative_to(ROOT))))]:
        bad=copy.deepcopy(native);modify(bad);rejected=False
        try:bound(bad)
        except (ValueError,OSError,KeyError):rejected=True
        checks.append(dict(check=name,passed=rejected))
    required=set(p['negative_controls']);observed={c['check'] for c in checks};checks.append(dict(check='complete-frozen14-negative-control-classes',passed=required<=observed))
    status='PASSED' if all(c['passed'] for c in checks) else 'SELF_TEST_FAILED';result=dict(status=status,checks=checks,evidence_references=[run['evidence'],native['evidence']],scope='Fault injection into the actual byte/region/adjacency/receipt validation functions; production evidence and outputs are never edited.');write(e.path/'result.json',result);result['evidence']=e.finish(status,dict(status=status,checks=checks));write(ROOT/'migration/reports/image-watershed-validator-controls.json',result)
    record('IMG-02','Watershed真实验证函数反向检查：'+status+'，覆盖冻结14类错误及实际GPU产品正控；含小区域丢失、非连通同标签、OR掩码掩盖逐边差异和seal/SHA伪造。',[result['evidence']]);print(status,checks);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
