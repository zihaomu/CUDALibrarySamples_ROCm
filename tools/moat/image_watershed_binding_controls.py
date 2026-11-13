#!/usr/bin/env python3
"""Reject substitution of genuine watershed proofs across vendors and layouts."""
import copy,json
from experiment import ROOT,Experiment,write
from image_completion_progress import record
import image_watershed_completion_binding as binding

def main():
    rp={mode:ROOT/f'migration/reports/image-watershed-completion-AMD-{mode}.json' for mode in ['compact','padded','inplace','no-labels']};np={s:ROOT/f'migration/reports/image-watershed-completion-native-{s}.json' for s in ['NPP','NPPPlus']};runs={m:json.loads(f.read_text()) for m,f in rp.items()};natives={s:json.loads(f.read_text()) for s,f in np.items()};build=json.loads(binding.BUILD.read_text())
    old=ROOT/'migration/reports/evidence/rewrite/I3/watershed-directed-marker-candidate-build/20261113T065626.880462Z-I3-rocm-build-86fc22b374';old_build=json.loads((old/'build.json').read_text());old_build['evidence']=str(old.relative_to(ROOT))
    e=Experiment('I3','watershed-contract-platform-layout-build-binding-controls','CPU-controls',sources=[__file__,ROOT/'tools/moat/image_watershed_completion_binding.py',ROOT/'tools/moat/image_watershed_v2_reference.py',ROOT/'tools/moat/image_encoder_math_binding.py',binding.CONTRACT,binding.SPEC,binding.BUILD,*rp.values(),*np.values(),old/'build.json']);checks=[]
    def positive(name,call):
        try:call();checks.append(dict(check=name,passed=True))
        except (ValueError,OSError,KeyError) as error:checks.append(dict(check=name,passed=False,reason=str(error)))
    def negative(name,call,reason):
        try:call();checks.append(dict(check=name,passed=False,reason='accepted wrong identity'))
        except (ValueError,OSError,KeyError) as error:checks.append(dict(check=name,passed=reason in str(error),reason=str(error)))
    positive('frozen-contract-and-independent-specification',binding.contract);positive('current-build',lambda:binding.build(build))
    for mode,row in runs.items():positive('actual-AMD-'+mode,lambda row=row,mode=mode:binding.amd(row,mode,build))
    for vendor,row in natives.items():positive('actual-native-'+vendor,lambda row=row,vendor=vendor:binding.native(row,vendor))
    negative('valid-NPP-proof-cannot-replace-NPPPlus',lambda:binding.native(natives['NPP'],'NPPPlus'),'vendor mismatch')
    negative('valid-NPPPlus-proof-cannot-replace-NPP',lambda:binding.native(natives['NPPPlus'],'NPP'),'vendor mismatch')
    for actual,requested in [('compact','padded'),('inplace','compact'),('no-labels','inplace')]:negative('valid-'+actual+'-cannot-replace-'+requested,lambda actual=actual,requested=requested:binding.amd(runs[actual],requested,build),'key/layout/vendor mismatch')
    bad=copy.deepcopy(runs['padded']);bad['contract_sha256']='0'*64;negative('old-contract-digest',lambda:binding.amd(bad,'padded',build),'contract digest mismatch')
    negative('genuine-prior-build-cannot-replace-current-build',lambda:binding.amd(runs['padded'],'padded',old_build),'run build/binary mismatch')
    mutated=copy.deepcopy(runs['padded']);mutated['binary_sha256']='0'*64;negative('binary-SHA-receipt-mutation-fails-seal',lambda:binding.amd(mutated,'padded',build),'sealed record identity')
    status='PASSED' if all(c['passed'] for c in checks) else 'SELF_TEST_FAILED';result=dict(status=status,checks=checks,evidence_references=[build['evidence'],*[r['evidence'] for r in runs.values()],*[r['evidence'] for r in natives.values()]],scope='Genuine wrong-vendor/layout/build substitution plus corrupted contract/binary metadata. Only immutable receipts are read; none are rewritten.');write(e.path/'result.json',result);result['evidence']=e.finish(status,dict(status=status,checks=checks));write(ROOT/'migration/reports/image-watershed-binding-controls.json',result)
    record('IMG-02','独立复审P1修复后的身份控制：'+status+'；冻结规范、四布局、两vendor、实际命令/环境/源码/二进制均绑定，真实跨vendor/布局/旧构建替换及合同/SHA篡改分别拒绝。',[result['evidence']]);print(status,checks);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
