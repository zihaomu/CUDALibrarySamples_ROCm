#!/usr/bin/env python3
"""Recompute every product of both original programs after deterministic input change."""
import json,numpy as np
from experiment import ROOT,Experiment,digest,write
from image_encoder_math_binding import sealed
from image_watershed_graph_reference import reference
from image_watershed_entry_reference import current_build
from image_watershed_entry_runtime import mapping,INVENTORY,RUNS
from image_completion_progress import record

REPORT=ROOT/'migration/reports/image-watershed-completion-entry-replay.json'

def main():
    build=current_build();samples=json.loads(INVENTORY.read_text())['samples'];runs=json.loads(REPORT.read_text());baseline={r['sample_id']:r for r in json.loads(RUNS.read_text())}
    if len(runs)!=2 or {r['sample_id'] for r in runs}!={s['sample_id'] for s in samples}:raise ValueError('complete two-entry replay required')
    rows=[]
    for sample in samples:
        run=next(r for r in runs if r['sample_id']==sample['sample_id']);proof=sealed(run);family=run['family'];manifest=json.loads((proof/'manifest.json').read_text());raw=ROOT/manifest['raw_artifact_dir'];commands=json.loads((proof/'commands.json').read_text());contract=json.loads((proof/'runtime-contract.json').read_text());source=json.loads((proof/'source.json').read_text());binary=build['binaries'][family]
        if run['status']!='PASSED' or run['action']!='replay' or run['case']!='invert-first' or run['build_evidence']!=build['evidence'] or run['binary_sha256']!=binary['sha256']:raise ValueError('bound current replay required')
        if len(commands)!=1 or commands[0]['argv']!=[str(ROOT/binary['path'])] or commands[0]['cwd']!=str(raw/'work') or commands[0]['return_code']!=0:raise ValueError('actual replay command')
        if manifest['sample_id']!=sample['sample_id'] or manifest['backend']!='rocm-complete-entry-replay' or manifest['experiment_outcome']!='PASSED':raise ValueError('actual entry replay identity')
        for name,sha in build['dependencies'].items():
            if source['dependencies'].get(name)!=sha:raise ValueError('replay compiled source snapshot')
        e=Experiment('I3',sample['sample_id'],'CPU-complete-entry-changed-input-reference',sources=[__file__,REPORT,INVENTORY,RUNS,ROOT/'tools/moat/image_watershed_graph_reference.py',ROOT/'tools/moat/image_watershed_entry_runtime.py',ROOT/'tools/moat/image_watershed_entry_reference.py',*[ROOT/family/'watershedSegmentation/images'/i['name'] for i in sample['inputs']]])
        try:
            checks=[];products=[]
            for index,item in enumerate(sample['inputs']):
                original=(ROOT/family/'watershedSegmentation/images'/item['name']).read_bytes();data=bytes(255-v for v in original) if index==0 else original;actual=raw/'images'/item['name']
                checks.append(dict(check=item['name']+'-exact-preregistered-input-recipe',passed=actual.read_bytes()==data and contract['inputs'][item['name']]==run['input_rows'][item['name']]==dict(bytes=len(data),sha256=digest(actual))))
                expected,_=reference(np.frombuffer(data,np.uint8).reshape(item['height'],item['width']))
                for name,kind in mapping(item,family).items():
                    path=raw/'images'/name;identity=dict(bytes=path.stat().st_size,sha256=digest(path));exact=path.read_bytes()==expected[kind].tobytes()
                    checks.append(dict(check=name+'-independent-CPU-exact',passed=exact and identity==run['outputs'][name]));products.append(dict(name=name,kind=kind,exact=exact,sha256=identity['sha256'],changed=identity!=baseline[sample['sample_id']]['outputs'][name]))
            checks.append(dict(check='complete-original-product-inventory',passed={r['name'] for r in products}==set(sample['products'])==set(run['outputs'])))
            status='PASSED' if all(c['passed'] for c in checks) else 'NUMERIC_MISMATCH';row=dict(status=status,sample_id=sample['sample_id'],family=family,checks=checks,products=products,evidence_references=[run['evidence'],build['evidence']]);write(e.path/'result.json',row);row['evidence']=e.finish(status,dict(status=status,checks=checks));rows.append(row);write(ROOT/'migration/reports/image-watershed-completion-replay-reference.json',rows)
            record('IMG-02',family+'原入口反转首图后全产品独立SCC参考：'+status+'；逐字节核验变化输入与其余未变化图像，防止缓存重放伪成功。',[row['evidence']]);print(family,status,len(products),flush=True)
        except BaseException as error:
            if not e.sealed:e.finish('VALIDATOR_GAP',reason=repr(error))
            raise
    return int(any(r['status']!='PASSED' for r in rows))

if __name__=='__main__':raise SystemExit(main())
