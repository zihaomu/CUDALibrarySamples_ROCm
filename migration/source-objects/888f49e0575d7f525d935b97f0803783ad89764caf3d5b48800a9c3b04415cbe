#!/usr/bin/env python3
"""Seal immutable watershed requirements independently from implementation revisions."""
import json
from experiment import ROOT,Experiment,write,digest
from image_completion_progress import record

def main():
    path=ROOT/'migration/rewrite/image-watershed-completion-contract.json';row=json.loads(path.read_text());previous=row.pop('evidence');spec=ROOT/'migration/rewrite/image-watershed-completion-spec-v1.json'
    if spec.exists():raise ValueError('independent specification already sealed')
    write(spec,row)
    e=Experiment('I3','watershed-immutable-specification-binding','CPU-contract',sources=[__file__,spec,ROOT/'tools/moat/image_watershed_completion_contract.py',ROOT/'migration/fixtures/image-watershed-completion/cases.txt',*[ROOT/i['path'] for i in row['inputs']],ROOT/'NPP/watershedSegmentation/watershedSegmentation.cpp',ROOT/'NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp'])
    write(e.path/'contract.json',row);write(e.path/'binding-change.json',dict(previous_contract_evidence=previous,reason='The initial freeze included implementation-header and progress-report snapshots as dependencies. Separate the unchanged mathematical requirements and raw input identities from code revisions; no acceptance, scope, inputs or thresholds change. This binding occurs before any new heldout AMD/native execution.',spec_sha256=digest(spec)))
    row['evidence']=e.finish('OBSERVED');write(path,row)
    record('IMG-02','将已冻结规范独立封存：算法/验收条款及60输入SHA完全不变，移除初次合同对可变实现头文件、进度报告的依赖。保留初次freeze，后续代码修订不改动规范；保留集尚未执行。',[row['evidence']]);print(row['evidence'])

if __name__=='__main__':main()
