#!/usr/bin/env python3
"""Qualify both complete watershed entries with explicit marker/reference variants."""
import argparse,json,subprocess
from experiment import ROOT,Experiment,digest,write
from audit import check as audit
from image_encoder_math_binding import sealed
from image_completion_inventory import closure
from image_completion_progress import record
from image_watershed_entry_reference import current_build,current_run
from image_watershed_completion_entries import INVENTORY,PORTS
from image_watershed_entry_runtime import mapping
import image_watershed_completion_binding as binding
import image_watershed_reference_amendment as amendment
from selected_proofs import inspect

REPORT=ROOT/'migration/reports/image-watershed-completion-qualifications.json'
KIND='image-watershed-complete-GPU-directed-root-graph'
SAMPLES={f+'/watershedSegmentation::'+p.rsplit('/',1)[1] for f,p in PORTS.items()}
MODES=('padded','compact','inplace','no-labels')
NEGATIVES=('missing-first','missing-last','truncated-first','blocked-output')
MEMBERS=('result.json','build.json','run.json','contract.json','amendment.json')
CONTROL_SPECS={
 'image-watershed-v2-controls.json':('watershed-view-and-allocation-controls','rocm','image_watershed_v2_controls.py',3),
 'image-watershed-binding-controls.json':('watershed-contract-platform-layout-build-binding-controls','CPU-controls','image_watershed_binding_controls.py',16),
 'image-watershed-validator-controls.json':('watershed-validator-negative-controls','CPU-controls','image_watershed_validator_controls.py',16),
 'image-watershed-amendment-controls.json':('watershed-native-reference-amendment-controls','CPU-controls','image_watershed_amendment_controls.py',14),
 'image-watershed-completion-controls.json':('watershed-complete-publication-and-cold-binding-controls','CPU-controls','image_watershed_completion_controls.py',40)}
REVIEW_SCOPE=('GPU-core-and-original-entry-integration','independent-SCC-native-reference-and-amendment','runtime-trace-replay-IO-errors','cold-source-build-command-output-binding','complete-qualification-publication-and-negative-controls')
REVIEW_FILES=['rocm/common/image/'+n for n in ('watershed.h','watershed.hip','watershed_v2.hpp','watershed_sample.hpp')]+list(PORTS.values())+['tools/moat/'+n for n in ('qualify_image_watershed_completion.py','image_watershed_completion_controls.py','image_watershed_cold_binding.py','image_watershed_completion_cold.py','image_watershed_entry_runtime.py','image_watershed_replay_reference.py','image_watershed_entry_reference.py','image_watershed_completion_reference.py','image_watershed_completion_binding.py','image_watershed_reference_amendment.py','image_watershed_monotone_reference.py')]

def read(name):return json.loads((ROOT/'migration/reports'/name).read_text())
def passed(row):return row.get('status')=='PASSED' and bool(row.get('checks')) and all(c.get('passed') is True for c in row['checks'])
def shapes(rows):return len(rows)==2 and {r.get('sample_id') for r in rows}==SAMPLES and all(r.get('kind')==KIND and r.get('contract_status')=='COMPLETE' for r in rows)

def proof_identity(row,sample,backend):
    proof=sealed(row);manifest=json.loads((proof/'manifest.json').read_text())
    return manifest['sample_id']==sample and manifest['backend']==backend and manifest['experiment_outcome']=='PASSED'

def control_identity(row,name):
    sample,backend,script,count=CONTROL_SPECS[name]
    if not passed(row) or len(row['checks'])!=count or len({c['check'] for c in row['checks']})!=count:return False
    if not proof_identity(row,sample,backend):return False
    source=json.loads((ROOT/row['evidence']/'source.json').read_text())
    return source['dependencies'].get('tools/moat/'+script)==digest(ROOT/'tools/moat'/script)

def review_identity(row):
    if not passed(row) or row.get('verdict')!='Approve' or row.get('kind')!='watershed-completion-final-review' or row.get('sample_ids')!=sorted(SAMPLES) or row.get('review_scope')!=list(REVIEW_SCOPE):return False
    expected={n:digest(ROOT/n) for n in REVIEW_FILES}
    if row.get('reviewed_dependencies')!=expected or not proof_identity(row,'watershed-completion-independent-final-review','review'):return False
    source=json.loads((ROOT/row['evidence']/'source.json').read_text())
    return all(source['dependencies'].get(n)==sha for n,sha in expected.items())

def cpu_products(row,sample):
    if not passed(row) or row.get('sample_id')!=sample['sample_id'] or len(row.get('rows',[]))!=len(sample['inputs']):return False
    inputs={i['name']:i for i in sample['inputs']};observed=[r['input'] for r in row['rows']]
    if len(set(observed))!=len(observed) or set(observed)!=set(inputs):return False
    family=sample['sample_id'].split('/')[0]
    return all(set(r['products'])==set(mapping(inputs[r['input']],family)) and all(v is True for v in r['products'].values()) and set(r['native_images_exact'])=={'segments','boundaries','contrast'} and all(v is True for v in r['native_images_exact'].values()) for r in row['rows'])

def replay_products(row,sample,run):
    if not passed(row) or not passed(run) or row.get('sample_id')!=sample['sample_id'] or run.get('sample_id')!=sample['sample_id']:return False
    names=[r['name'] for r in row.get('products',[])]
    if len(set(names))!=len(names) or set(names)!=set(sample['products']) or set(run['outputs'])!=set(names):return False
    expected={n:k for i in sample['inputs'] for n,k in mapping(i,sample['sample_id'].split('/')[0]).items()}
    return all(r['exact'] is True and r['kind']==expected[r['name']] and r['sha256']==run['outputs'][r['name']]['sha256'] for r in row['products'])

def complete_matrix(row,mode,ids):
    if not passed(row) or row.get('mode')!=mode or row.get('amended') is not True or row.get('contract_sha256')!=digest(binding.CONTRACT):return False
    if len(row.get('rows',[]))!=len(ids) or [r['case'] for r in row['rows']]!=ids:return False
    cpu_keys={'inventory','segments','black','white','contrast','boundaries'} | ({'labels','compact'} if mode!='no-labels' else set())
    native_keys={kind+'-r'+str(repeat) for kind in amendment.MODES for repeat in (0,1)}|{'contrast-null-marker','boundaries-null-marker'}
    for case in row['rows']:
        if set(case['CPU_exact'])!=cpu_keys or not all(v is True for v in case['CPU_exact'].values()):return False
        if case['topology']['all_regions_connected'] is not True or case['topology']['all_regions_constant_gray'] is not True:return False
        if set(case['native'])!={'NPP','NPPPlus'}:return False
        for vendor,native in case['native'].items():
            exception=vendor=='NPPPlus' and case['case'] in amendment.IDS
            if native['comparison_status']!=('NATIVE_MISMATCH' if exception else 'EXACT') or native['accepted_under_reference_amendment'] is not exception:return False
            if set(native['image_exact'])!=native_keys or not all(type(v) is bool for v in native['image_exact'].values()) or all(native['image_exact'].values())==exception:return False
    return True

def references(rows):
    refs=set()
    for row in rows:
        folder=ROOT/row['evidence'];member=next((m for m in MEMBERS if (folder/m).exists() and json.loads((folder/m).read_text())=={k:v for k,v in row.items() if k!='evidence'}),None)
        if member is None:raise ValueError('result has no exact sealed identity: '+row['evidence'])
        sealed(row,member);refs.add(row['evidence'])
    pending=list(refs)
    while pending:
        ref=pending.pop();folder=ROOT/ref
        if audit(folder):raise ValueError('invalid proof '+ref)
        for n,h in json.loads((folder/'source.json').read_text())['dependencies'].items():
            if not (ROOT/n).is_file() or digest(ROOT/n)!=h:raise ValueError('stale proof '+ref+': '+n)
        for member in MEMBERS:
            path=folder/member
            if not path.exists():continue
            value=json.loads(path.read_text())
            for child in value.get('evidence_references',[]):
                if child not in refs:refs.add(child);pending.append(child)
    return sorted(refs)

def qualify():
    contract=binding.contract();alteration=amendment.load();b=current_build();samples=json.loads(INVENTORY.read_text())['samples'];ids=[i['id'] for i in contract['inputs']]
    matrices=[read('image-watershed-completion-reference-amended-'+m+'.json') for m in MODES]
    cpu=read('image-watershed-completion-entries-reference.json');runs=read('image-watershed-completion-entries-runs.json');traces=read('image-watershed-completion-entry-trace.json');replays=read('image-watershed-completion-replay-reference.json');replay_runs=read('image-watershed-completion-entry-replay.json');negative=read('image-watershed-completion-entry-negative.json')
    control_names=list(CONTROL_SPECS)
    controls=[read(n) for n in control_names];diagnostic=read('image-watershed-monotone-reference.json');cold=read('image-watershed-completion-cold.json');review=read('image-watershed-completion-review.json')
    checks=[dict(check='complete-sixty-input-four-layout-matrices-and-narrow-native-exceptions',passed=all(complete_matrix(r,m,ids) for r,m in zip(matrices,MODES))),dict(check='all-five-exact-independent-negative-control-suite-identities',passed=all(control_identity(r,n) for r,n in zip(controls,control_names)) and len({r['evidence'] for r in controls})==5),dict(check='twenty-four-bound-analytic-native-diagnostic-inputs',passed=passed(diagnostic) and len(diagnostic['rows'])==24),dict(check='independent-current-watershed-review-approved',passed=review_identity(review)),dict(check='complete-fixed-commit-rebuild',passed=passed(cold) and len(cold['children'])==21 and cold['product_reproductions']==1642 and any(c['check']=='every-selected-result-bound-to-actual-cold-seal-command-build-output-and-unique-child-set' and c['passed'] is True for c in cold['checks']))]
    for name,group in [('CPU',cpu),('runs',runs),('traces',traces),('replay-CPU',replays),('replay-runs',replay_runs)]:checks.append(dict(check='two-unique-original-entries-'+name,passed=len(group)==2 and {r['sample_id'] for r in group}==SAMPLES))
    checks.append(dict(check='eight-unique-actual-entry-IO-errors',passed=len(negative)==8 and {(r['sample_id'],r['case']) for r in negative}=={(s,c) for s in SAMPLES for c in NEGATIVES} and all(passed(r) and r['return_code']==1 for r in negative)))
    if not all(c['passed'] for c in checks):raise ValueError([c for c in checks if not c['passed']])
    if subprocess.run(['git','merge-base','--is-ancestor',cold['source_commit'],'HEAD'],cwd=ROOT).returncode:raise ValueError('cold commit not in current history')
    for path,sha in b['dependencies'].items():
        import hashlib
        if hashlib.sha256(subprocess.check_output(['git','show',cold['source_commit']+':'+path],cwd=ROOT)).hexdigest()!=sha:raise ValueError('current source not cold rebuilt')
    common=references([contract,alteration,b,*matrices,*controls,diagnostic,cold,review]);result=[]
    for sample in samples:
        sid=sample['sample_id'];family=sid.split('/')[0]
        run=next(r for r in runs if r['sample_id']==sid);current_run(run,sample,b)
        cp=next(r for r in cpu if r['sample_id']==sid);trace=next(r for r in traces if r['sample_id']==sid);replay=next(r for r in replays if r['sample_id']==sid);rr=next(r for r in replay_runs if r['sample_id']==sid);neg=[r for r in negative if r['sample_id']==sid]
        local=checks+[dict(check='all-original-file-products-independent-CPU-and-native',passed=cpu_products(cp,sample) and proof_identity(cp,sid,'CPU-complete-original-entry-reference')),dict(check='actual-original-entry-kernel-trace-and-output-bytes',passed=passed(trace) and trace['action']=='trace' and trace['build_evidence']==b['evidence'] and trace['binary_sha256']==b['binaries'][family]['sha256'] and trace['outputs']==run['outputs']),dict(check='changed-input-complete-independent-CPU-products',passed=replay_products(replay,sample,rr) and proof_identity(replay,sid,'CPU-complete-entry-changed-input-reference'))]
        if not all(c['passed'] for c in local):raise ValueError('entry gates '+sid)
        source=ROOT/PORTS[family];deps,missing=closure(source)
        if missing:raise ValueError('unresolved includes')
        # The C ABI implementation is a separate translation unit, not a header
        # include of the original program; include its compiled closure explicitly.
        deps.update(b['dependencies'])
        case_ids=['IMG-02/'+m+'/'+i for m in MODES for i in ids]+['IMG-02/analytic/'+r['case'] for r in diagnostic['rows']]
        case_ids += ['IMG-02/'+kind+'/'+i['name'] for kind in ['original','changed-input'] for i in sample['inputs']]+['IMG-02/IO/'+c for c in NEGATIVES]+['IMG-02/control/'+n for n in control_names]+['IMG-02/actual-entry-GPU-trace','IMG-02/fixed-commit-cold-rebuild']
        refs=sorted(set(common+references([run,cp,trace,replay,rr,*neg])))
        e=Experiment('I3',sid,'complete-original-watershed-qualification',sources=[__file__,binding.CONTRACT,binding.SPEC,amendment.PATH,*[ROOT/n for n in deps]])
        devices=json.loads((ROOT/run['evidence']/'backend.observed.json').read_text())['devices']
        q=dict(kind=KIND,status='PASSED',contract_status='COMPLETE',sample_id=sid,implementation=str(source.relative_to(ROOT)),implementation_sha256=digest(source),source_commit=cold['source_commit'],case_count=len(case_ids),case_ids=case_ids,checks=local,devices=devices,dependencies=deps,evidence_references=refs,rocm_evidence=run['evidence'],cuda_evidence=read('image-watershed-completion-native-'+('NPPPlus' if family=='NPP+' else 'NPP')+'.json')['evidence'],comparison_mode='ALGORITHM_VARIANT_EXACT_INDEPENDENT_SCC_WITH_EXPLICIT_NATIVE_REFERENCE_AMENDMENT',limitations=['Linux/gfx1201/ROCm10.1 only; no unmeasured platform qualification.','Marker partitions follow the frozen directed terminal-root reachability algorithm, not merely a renumbering of proprietary native labels. Full native region/adjacency diagnostics remain published.','NPP image modes match all60 corpus inputs exactly. NPPPlus12.4.0 matches57/60; three locked monotone inputs retain NATIVE_MISMATCH with analytic/CPU/NPP exact checks and immutable amendment.','All original images and all22 original file products pass required CPU and native image-mode checks.','No speedup or performance parity claim; convergence and file I/O are included in the actual original programs.'])
        write(e.path/'qualification.json',q);q['qualification_id']=e.id;q['evidence']=e.finish('PASSED',dict(status='PASSED',checks=local));result.append(q);write(REPORT,result)
    record('IMG-02','两原入口完整Watershed资格已生成，待Git封存后发布；保留marker算法变体与三项NPP+原生差异，不标为原生全精确。',[r['evidence'] for r in result]);print([(r['sample_id'],r['case_count']) for r in result])

def publish():
    rows=json.loads(REPORT.read_text());data=json.loads((ROOT/'migration/samples.yaml').read_text())
    if not shapes(rows):raise ValueError('two complete stable watershed entries required')
    for q in rows:
        s=next(s for s in data['samples'] if s['id']==q['sample_id']);verdict=inspect(dict(s,selected_validation=q))
        if verdict['status']!='PASSED':raise ValueError(verdict['errors'])
        s.update(status='PASSED',level='L4',reason_code='VALIDATED_MOAT_REWRITE',selected_validation=q,required_cases=q['case_ids'],passed_cases=q['case_ids'],equivalence='ALGORITHM_VARIANT',active_batch='IMG-02',actual_library='Project HIP strict-descent watershed, directed terminal-root graph markers, GPU compact labels and grayscale boundary modes',backend_library='Project HIP',reason='完整原入口、22文件产品、60输入四布局、独立SCC CPU及两种原生对照、GPU trace、变化重放/IO异常与固定提交冷构建通过。marker按声明算法变体；NPP+12.4.0三个固定坡度保持NATIVE_MISMATCH，其余57输入及NPP全部60输入图像模式精确。详见完整资格及差异修订。',retry_condition='Requalify when source, oracle, frozen contract, SDK or required platform changes.',next_step='继续IMG-03–IMG-10的JPEG/JPEG2000与全图像回归。',cuda_comparison='PASSED',cuda_comparison_mode=q['comparison_mode'],cuda_comparison_reason='完整原图图像模式精确；marker分区为公开算法变体，NPP+三个固定长坡度保留原生不一致记录。')
        s['attempts'].append(q)
        for ref in [q['evidence'],'migration/reports/image-completion-IMG-02.md','migration/rewrite/image-watershed-native-reference-amendment.json']:
            if ref not in s['evidence']:s['evidence'].append(ref)
    write(ROOT/'migration/samples.yaml',data);record('IMG-02','两原始Watershed样例已由固定Git资格发布为整例通过；图像16/26。完整支持按声明算法变体成立，原生分区差异及三个NPP+坡度失败仍单独公开。',[str(REPORT.relative_to(ROOT))],state='COMPLETED');print('PUBLISHED two complete watershed entries')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['qualify','publish']);globals()[p.parse_args().action]()
