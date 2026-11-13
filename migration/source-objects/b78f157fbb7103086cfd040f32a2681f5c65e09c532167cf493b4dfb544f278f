#!/usr/bin/env python3
"""Prove the NPPPlus reference amendment cannot become a general tolerance waiver."""
import copy,hashlib,json
import numpy as np
from experiment import ROOT,Experiment,write
from image_completion_progress import record
from image_watershed_graph_reference import reference
import image_watershed_completion_binding as binding
import image_watershed_reference_amendment as amendment

def main():
    contract=binding.contract();a=amendment.load();strict=json.loads(amendment.STRICT.read_text());items={r['id']:r for r in contract['inputs']};observed={r['case']:r for r in strict['rows']}
    sources=[__file__,amendment.PATH,amendment.STRICT,amendment.DIAG,binding.CONTRACT,binding.SPEC,ROOT/'tools/moat/image_watershed_reference_amendment.py',ROOT/'tools/moat/image_watershed_graph_reference.py',ROOT/'tools/moat/image_watershed_completion_binding.py',ROOT/'tools/moat/image_encoder_math_binding.py',*[ROOT/items[n]['path'] for n in amendment.IDS]]
    e=Experiment('I3','watershed-native-reference-amendment-controls','CPU-controls',sources=sources);checks=[]
    for name in amendment.IDS:
        item=items[name];image=np.fromfile(ROOT/item['path'],np.uint8).reshape(item['height'],item['width']);expected,_=reference(image);row=observed[name]
        checks.append(dict(check=name+'-actual-identified-analytic-CPU-NPP-positive',passed=amendment.permits(a,item,'NPPPlus',image,expected,all(row['CPU_exact'].values()),all(row['native']['NPP']['image_exact'].values()))))
    item=items[amendment.IDS[0]];image=np.fromfile(ROOT/item['path'],np.uint8).reshape(item['height'],item['width']);expected,_=reference(image)
    def reject_payload(name,modified):
        rejected=False
        try:amendment.validate_payload(modified,contract)
        except ValueError:rejected=True
        checks.append(dict(check=name,passed=rejected))
    modified=copy.deepcopy(a);fourth=copy.deepcopy(modified['exceptions'][0]);fourth['id']='heldout-constant-127';modified['exceptions'].append(fourth);reject_payload('fourth-exception-rejected',modified)
    modified=copy.deepcopy(a);modified['exceptions'][0]['library_version']='13.2.0';reject_payload('other-NPPPlus-version-rejected',modified)
    modified=copy.deepcopy(a);modified['exceptions'][0]['modes'].append('unknown-mode');reject_payload('additional-output-mode-rejected',modified)
    modified=copy.deepcopy(a);modified['exceptions'][0]['width']+=1;reject_payload('exception-dimension-change-rejected',modified)
    replaced=image.copy();replaced[0,0]^=1;checks.append(dict(check='same-name-replaced-input-rejected',passed=not amendment.permits(a,item,'NPPPlus',replaced,expected,True,True)))
    unknown=dict(item,id='heldout-constant-127');checks.append(dict(check='unlisted-input-not-implicitly-exempt',passed=not amendment.permits(a,unknown,'NPPPlus',image,expected,True,True)))
    checks.append(dict(check='second-native-NPP-failure-rejected',passed=not amendment.permits(a,item,'NPPPlus',image,expected,True,False)))
    checks.append(dict(check='independent-CPU-failure-rejected',passed=not amendment.permits(a,item,'NPPPlus',image,expected,False,True)))
    checks.append(dict(check='NPP-itself-cannot-use-exception',passed=not amendment.permits(a,item,'NPP',image,expected,True,True)))
    wrong={k:v.copy() for k,v in expected.items()};wrong['segments'][0,0]=1;checks.append(dict(check='nonzero-project-output-rejected-even-if-upstream-booleans-forged',passed=not amendment.permits(a,item,'NPPPlus',image,wrong,True,True)))
    plateau=np.full_like(image,128);modified=copy.deepcopy(a);fake=dict(item,sha256=hashlib.sha256(plateau.tobytes()).hexdigest());modified['exceptions'][0]['sha256']=fake['sha256']
    checks.append(dict(check='false-analytic-invariant-rejected-even-with-synthetic-matching-hash',passed=not amendment.analytic_zero(plateau) and not amendment.permits(modified,fake,'NPPPlus',plateau,expected,True,True)))
    status='PASSED' if all(c['passed'] for c in checks) else 'SELF_TEST_FAILED';result=dict(status=status,checks=checks,evidence_references=[a['evidence'],strict['evidence']],scope='Only the three byte-identified NPPPlus12.4 cases may use the analytic reference amendment. Synthetic guard faults never modify sealed contracts or inputs.');write(e.path/'result.json',result);result['evidence']=e.finish(status,dict(status=status,checks=checks));write(ROOT/'migration/reports/image-watershed-amendment-controls.json',result)
    record('IMG-02','三个NPP+参考例外的边界控制：'+status+'；第四例外、同名换内容、维度/版本/模式扩张、解析条件不成立、CPU或第二原生失败及错误项目像素均拒绝。',[result['evidence']]);print(status,checks);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
