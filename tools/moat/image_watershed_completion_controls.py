#!/usr/bin/env python3
"""Reject incomplete publication, broadened reference exemptions and warm/cold swaps."""
import copy,json
from pathlib import Path
from experiment import ROOT,Experiment,write
from image_completion_progress import record
from qualify_image_watershed_completion import shapes,complete_matrix,SAMPLES,KIND,MODES,read,CONTROL_SPECS,control_identity,review_identity,cpu_products,replay_products
from image_watershed_cold_binding import validate,bound,inside,inventory,COUNTS
from image_watershed_completion_binding import CONTRACT

def main():
    cold=read('image-watershed-completion-cold.json');root=Path(cold['clone']);commit=cold['source_commit'];matrices=[read('image-watershed-completion-reference-amended-'+m+'.json') for m in MODES];ids=[r['id'] for r in json.loads(CONTRACT.read_text())['inputs']]
    input_reports=['image-encoder-completion-review.json','image-watershed-completion-entries-reference.json','image-watershed-completion-replay-reference.json','image-watershed-completion-entry-replay.json','image-watershed-completion-entry-trace.json','image-watershed-completion-entries-build.json',*list(CONTROL_SPECS)[:-1]]
    e=Experiment('I3','watershed-complete-publication-and-cold-binding-controls','CPU-controls',sources=[__file__,CONTRACT,ROOT/'migration/rewrite/image-watershed-profile.json',ROOT/'tools/moat/qualify_image_watershed_completion.py',ROOT/'tools/moat/image_watershed_cold_binding.py',*[ROOT/'migration/reports'/n for n in input_reports],*[ROOT/f'migration/reports/image-watershed-completion-reference-amended-{m}.json' for m in MODES]])
    checks=[]
    def reject(name,call):
        try:call();rejected=False
        except (ValueError,KeyError,FileNotFoundError):rejected=True
        checks.append(dict(check=name,passed=rejected))
    try:
        reports={n:json.loads((root/'migration/reports'/n).read_text()) for n in COUNTS};write(e.path/'cold-report-inputs.json',dict(clone=str(root),source_commit=commit,reports=reports))
        actual=validate(root,commit,reports);checks.append(dict(check='actual-twenty-one-cold-children-positive',passed=actual['status']=='PASSED'))
        trace=reports['image-watershed-completion-entry-trace.json'][0]
        hot=copy.deepcopy(read('image-watershed-completion-entry-trace.json')[0]);hot['evidence']=str(ROOT/hot['evidence']);hot['output_dir']=str(ROOT/hot['output_dir'])
        reject('warm-trace-absolute-path-substitution-rejected',lambda:bound(root,hot,'result.json',commit))
        reject('relative-directory-traversal-rejected',lambda:inside(root,'../outside'))
        wrong=copy.deepcopy(trace);wrong['output_dir']=str(ROOT/read('image-watershed-completion-entry-trace.json')[0]['output_dir'])
        reject('warm-output-under-cold-proof-rejected',lambda:bound(root,wrong,'result.json',commit))
        wrong=copy.deepcopy(trace);wrong['build_evidence']=read('image-watershed-completion-entries-build.json')['evidence']
        reject('wrong-cold-build-reference-rejected',lambda:bound(root,wrong,'result.json',commit))
        wrong=copy.deepcopy(trace);wrong['binary_sha256']='0'*64
        reject('wrong-cold-executable-SHA-rejected',lambda:bound(root,wrong,'result.json',commit))
        reject('wrong-cold-source-commit-rejected',lambda:bound(root,trace,'result.json','0'*40))
        children=actual['selected_child_ids'];reject('missing-selected-cold-child-rejected',lambda:inventory(children[:-1],children));reject('duplicated-selected-cold-child-rejected',lambda:inventory(children[:-1]+[children[0]],children));reject('missing-actual-cold-child-rejected',lambda:inventory(children,children[:-1]));reject('unexpected-actual-cold-child-rejected',lambda:inventory(children,children+['unexpected']))
        good=[dict(sample_id=s,kind=KIND,contract_status='COMPLETE') for s in sorted(SAMPLES)];checks.append(dict(check='two-complete-original-entry-publication-shapes-positive',passed=shapes(good)))
        for name in ['one-entry','duplicate-entry','partial-contract','old-partial-kind']:
            changed=copy.deepcopy(good)
            if name=='one-entry':changed.pop()
            elif name=='duplicate-entry':changed[1]=changed[0]
            elif name=='partial-contract':changed[0]['contract_status']='PARTIAL'
            else:changed[0]['kind']='watershed-file-subset'
            checks.append(dict(check='reject-'+name,passed=not shapes(changed)))
        checks.append(dict(check='actual-four-complete-sixty-input-reference-matrices-positive',passed=all(complete_matrix(r,m,ids) for r,m in zip(matrices,MODES))))
        for name in ['wrong-layout','missing-input','duplicate-input','fourth-exception','hidden-native-failure','CPU-failure','split-disconnected-region']:
            changed=copy.deepcopy(matrices[0])
            if name=='wrong-layout':changed['mode']='compact'
            elif name=='missing-input':changed['rows'].pop()
            elif name=='duplicate-input':changed['rows'][-1]=changed['rows'][0]
            elif name=='fourth-exception':changed['rows'][0]['native']['NPPPlus'].update(comparison_status='NATIVE_MISMATCH',accepted_under_reference_amendment=True)
            elif name=='hidden-native-failure':next(r for r in changed['rows'] if r['case']=='heldout-ramp-x')['native']['NPPPlus']['comparison_status']='EXACT'
            elif name=='CPU-failure':changed['rows'][0]['CPU_exact']['segments']=False
            else:changed['rows'][0]['topology']['all_regions_connected']=False
            checks.append(dict(check='reject-matrix-'+name,passed=not complete_matrix(changed,'padded',ids)))
        checks.append(dict(check='real-JPEG-review-cannot-approve-watershed',passed=not review_identity(read('image-encoder-completion-review.json'))))
        suites=list(CONTROL_SPECS)[:-1];checks.append(dict(check='actual-four-distinct-control-suite-identities-positive',passed=all(control_identity(read(n),n) for n in suites)))
        for name in CONTROL_SPECS:
            if name=='image-watershed-amendment-controls.json':continue
            checks.append(dict(check='real-amendment-control-cannot-replace-'+name,passed=not control_identity(read('image-watershed-amendment-controls.json'),name)))
        for missing in ('labels','compact','boundaries','native-mode-name'):
            changed=copy.deepcopy(matrices[0])
            if missing=='native-mode-name':v=changed['rows'][0]['native']['NPP']['image_exact'];v['invented-mode']=v.pop('segments-r0')
            else:del changed['rows'][0]['CPU_exact'][missing]
            checks.append(dict(check='reject-missing-or-misnamed-required-'+missing,passed=not complete_matrix(changed,'padded',ids)))
        samples=json.loads((ROOT/'migration/rewrite/image-watershed-profile.json').read_text())['samples'];sample=samples[0];cpu=next(r for r in read('image-watershed-completion-entries-reference.json') if r['sample_id']==sample['sample_id']);replay=next(r for r in read('image-watershed-completion-replay-reference.json') if r['sample_id']==sample['sample_id']);run=next(r for r in read('image-watershed-completion-entry-replay.json') if r['sample_id']==sample['sample_id'])
        for name in ('duplicate-CPU-input','missing-CPU-product','wrong-native-image-name'):
            changed=copy.deepcopy(cpu)
            if name=='duplicate-CPU-input':changed['rows'][-1]=changed['rows'][0]
            elif name=='missing-CPU-product':changed['rows'][0]['products'].pop(next(iter(changed['rows'][0]['products'])))
            else:v=changed['rows'][0]['native_images_exact'];v['invented-mode']=v.pop('segments')
            checks.append(dict(check='reject-original-'+name,passed=not cpu_products(changed,sample)))
        for name in ('duplicate-product','wrong-kind','wrong-SHA'):
            changed=copy.deepcopy(replay)
            if name=='duplicate-product':changed['products'][-1]=changed['products'][0]
            elif name=='wrong-kind':changed['products'][0]['kind']='invented-kind'
            else:changed['products'][0]['sha256']='0'*64
            checks.append(dict(check='reject-replay-'+name,passed=not replay_products(changed,sample,run)))
    except Exception as error:checks.append(dict(check='controls-exception',passed=False,error=repr(error)))
    status='PASSED' if checks and all(c['passed'] for c in checks) else 'VALIDATOR_GAP';row=dict(status=status,checks=checks,scope='Actual fixed checkout reports and sealed child sources inspected anew; rejected mutations are in-memory only. No GPU rerun or new numerical result claimed.',cold_clone=str(root),cold_source_commit=commit)
    write(e.path/'result.json',row);row['evidence']=e.finish(status,dict(status=status,checks=checks));write(ROOT/'migration/reports/image-watershed-completion-controls.json',row);record('IMG-02','完整资格/冷检出身份反向检查：'+status+'；热运行替换、越界路径、错构建/二进制/提交、缺失或重复子实验及扩大原生例外均检查。',[row['evidence']]);print(status,len(checks),[c for c in checks if not c['passed']]);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
