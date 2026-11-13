#!/usr/bin/env python3
"""Qualify/publish the measured async original-entry subset, retaining full gaps."""
import argparse,copy,json
from experiment import ROOT,Experiment,digest,git,write
from audit import check as audit_check
from image_completion_progress import record
from selected_proofs import anchored_seal,publication,inspect

SAMPLE='nvJPEG/nvJPEG-Encoder-MultipleInstances::nvJPEGEncMultipleInstances.cpp'
REPORT=ROOT/'migration/reports/image-encoder-instances-v2-qualification.json'
KIND='image-JPEG-multiple-instances-async-GPU-subset'

def read(name):return json.loads((ROOT/'migration/reports'/name).read_text())

def sealed(row,member='result.json'):
    directory=ROOT/row['evidence']
    if audit_check(directory):raise ValueError('unsealed evidence '+row['evidence'])
    frozen=json.loads((directory/member).read_text())
    if frozen!={k:v for k,v in row.items() if k!='evidence'}:raise ValueError('report differs from sealed '+row['evidence'])
    return row['evidence']

def coverage_checks(profile,comparison,pipeline,pipeline_trace,prefix,oversize,runtime,preallocation):
    output_cases=[c for c in profile['cases'] if c['output']]
    slot_cases=json.loads((ROOT/'migration/rewrite/image-encoder-pipeline-profile.json').read_text())['cases']
    prefix_cases=json.loads((ROOT/'migration/rewrite/image-checked-prefix-profile.json').read_text())['cases']
    runtime_cases=json.loads((ROOT/'migration/rewrite/image-encoder-runtime-profile.json').read_text())['cases']
    prepared_cases=json.loads((ROOT/'migration/rewrite/image-encoder-preallocation-profile.json').read_text())['cases']
    passed=lambda group:all(r['status']=='PASSED' and r['checks'] and all(c['passed'] for c in r['checks']) for r in group)
    return [
        dict(check='all33-original-entry-JPEG-products-byte-exact-vs-serial-core-independent-BMP',passed=
            [r['case'] for r in comparison]==[c['id'] for c in output_cases] and
            sum(len(r['products']) for r in comparison)==33 and
            all({p['product'] for p in r['products']}=={str(i)+'.jpg' for i in range(c['count'])} and len(r['products'])==c['count'] for r,c in zip(comparison,output_cases)) and passed(comparison)),
        dict(check='fourteen-slot-cases-and-actual-copy-traces',passed=
            [r['case'] for r in pipeline]==[c['id'] for c in slot_cases] and len(slot_cases)==14 and
            [r['case'] for r in pipeline_trace]==['511x509-standard','511x509-optimized','device-only-0','device-only-1'] and passed(pipeline+pipeline_trace)),
        dict(check='sixteen-prefix-cases-and-two-oversize-files',passed=
            [r['case'] for r in prefix]==[c['id'] for c in prefix_cases] and len(prefix_cases)==16 and
            [r['mode'] for r in oversize]==['stuff','bits'] and passed(prefix+oversize)),
        dict(check='all-sixteen-runtime-contracts',passed=
            [r['case'] for r in runtime]==[c['id'] for c in runtime_cases] and len(runtime_cases)==16 and passed(runtime) and
            all(c['rc']!=0 or (len(r['products'])==(c['count'] if c['write'] else 0) and
                {p['name'] for p in r['products']}==({str(i)+'.jpg' for i in range(c['count'])} if c['write'] else set()))
                for r,c in zip(runtime,runtime_cases))),
        dict(check='three-preallocation-traces-and26-products',passed=
            [r['case'] for r in preallocation]==[c['id'] for c in prepared_cases] and len(prepared_cases)==3 and passed(preallocation) and
            all(len(r['products'])==(c['jobs'] if c['download'] else 0) and
                {p['name'] for p in r['products']}==({str(i)+'.jpg' for i in range(c['jobs'])} if c['download'] else set())
                for r,c in zip(preallocation,prepared_cases)))]

def qualify():
    build=read('image-encoder-instances-v2-build.json');runs=read('image-encoder-instances-v2-runs.json')
    trace=read('image-encoder-instances-v2-trace.json');comparison=read('image-encoder-instances-v2-comparison.json')
    pipeline=read('image-encoder-pipeline-runs.json');pipeline_trace=read('image-encoder-pipeline-trace.json')
    prefix=read('image-checked-prefix-runs.json');oversize=read('image-checked-prefix-oversize.json')
    faults=read('image-encoder-pipeline-faults.json');native=read('image-completion-encoder-native-reference.json')
    negatives=read('image-encoder-instances-v2-qualification-negatives.json')
    native_runs=read('image-completion-encoder-native.json')
    runtime=read('image-encoder-runtime-runs.json');preallocation=read('image-encoder-preallocation-runs.json')
    lifecycle=read('image-encoder-prepared-lifecycle.json')
    profile_path=ROOT/'migration/rewrite/image-encoder-instances-v2-profile.json';profile=json.loads(profile_path.read_text())
    refs=[sealed(build,'build.json'),sealed(faults),sealed(native,'reference.json'),sealed(negatives),sealed(lifecycle)]
    native_build=ROOT/native_runs['build_evidence']
    native_build_result=json.loads((native_build/'result.json').read_text())
    if audit_check(native_build) or native_build_result!={k:v for k,v in native_runs.items() if k not in ('build_evidence','cases')}|{'cases':[]}:
        raise ValueError('native build evidence/report mismatch')
    refs.append(native_runs['build_evidence'])
    for group in [runs,trace,comparison,pipeline,pipeline_trace,prefix,oversize,runtime,preallocation]:refs += [sealed(row) for row in group]
    refs += [sealed(row) for row in native_runs['cases']]
    for ref in refs:
        deps=json.loads((ROOT/ref/'source.json').read_text())['dependencies']
        if any(not (ROOT/n).is_file() or digest(ROOT/n)!=h for n,h in deps.items()):
            raise ValueError('stale transitive source: '+ref)
    source=ROOT/'rocm/ported/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp'
    deps=build['dependencies'];current=build['status']=='BUILT' and digest(ROOT/build['binary'])==build['binary_sha256'] and all(digest(ROOT/n)==h for n,h in deps.items())
    checks=[dict(check='actual-original-entry-current-source-and-library-closure',passed=current and str(source.relative_to(ROOT)) in deps),
        dict(check='all-fifteen-frozen-CLI-cases',passed=len(runs)==15 and [r['case'] for r in runs]==[c['id'] for c in profile['cases']] and all(r['status']=='PASSED' and all(c['passed'] for c in r['checks']) for r in runs)),
        dict(check='three-actual-entry-multithread-traces',passed=[r['case'] for r in trace]==['repeat-seven','optimized-444','device-only'] and all(r['status']=='PASSED' and all(c['passed'] for c in r['checks']) for r in trace)),
        dict(check='all-seven-changed-input-jobs-correctly-associated',passed=sum(c['check'].startswith('only-corresponding-input-jobs-change-') and c['passed'] for r in trace for c in r['checks'])==7),
        dict(check='actual-entry-device-only-no-payload-transfer',passed=any(c['check']=='entry-device-only-downloads-metadata-only' and c['passed'] for r in trace for c in r['checks'])),
        dict(check='five-inflight-faults',passed=faults['status']=='PASSED' and all(c['passed'] for c in faults['checks'])),
        dict(check='complete-coverage-control-and17-corruptions-rejected',passed=negatives['status']=='PASSED' and len(negatives['checks'])==18 and all(c['passed'] for c in negatives['checks'])),
        dict(check='prepared-input-owner-and-invalidation',passed=lifecycle['status']=='PASSED' and len(lifecycle['checks'])==2 and all(c['passed'] for c in lifecycle['checks'])),
        dict(check='native-original-seven-cases-and19-independent-decodes-restored',passed=native['status']=='PASSED' and native['product_count']==19 and len(native_runs['cases'])==7 and all(c['passed'] for c in native['checks']))]
    checks+=coverage_checks(profile,comparison,pipeline,pipeline_trace,prefix,oversize,runtime,preallocation)
    reports=[ROOT/'migration/reports/image-encoder-instances-v2-build.json',ROOT/'migration/reports/image-encoder-pipeline-build.json']
    binaries=[dict(binary=b['binary'],sha256=b['binary_sha256'],build_report=str(path.relative_to(ROOT)),build_report_sha256=digest(path)) for b,path in zip((build,read('image-encoder-pipeline-build.json')),reports)]
    checks.append(dict(check='runtime-and-preallocation-bind-both-current-build-reports',passed=all(r.get('binaries')==binaries for r in runtime+preallocation)))
    if not all(c['passed'] for c in checks):raise ValueError([c for c in checks if not c['passed']])
    case_ids=['IMG-01/'+r['case'] for r in runs]+['IMG-01/all33-JPEG-byte-exact']+['IMG-01/trace-'+r['case'] for r in trace]+['IMG-01/changed-input-replay']
    case_ids+=['IMG-01/runtime-'+r['case'] for r in runtime]+['IMG-01/'+r['case'] for r in preallocation]+['IMG-01/prepared-input-lifecycle']
    devices=json.loads((ROOT/trace[0]['evidence']/'backend.observed.json').read_text())['devices']
    e=Experiment('I5',SAMPLE,'composite-subset-qualification',sources=[__file__,source,profile_path,
        ROOT/'migration/rewrite/image-encoder-pipeline-profile.json',ROOT/'migration/rewrite/image-checked-prefix-profile.json',
        ROOT/'migration/rewrite/image-encoder-runtime-profile.json',ROOT/'migration/rewrite/image-encoder-preallocation-profile.json',*[ROOT/n for n in deps]])
    q=dict(kind=KIND,status='PASSED',contract_status='PARTIAL',sample_id=SAMPLE,
        implementation=str(source.relative_to(ROOT)),implementation_sha256=digest(source),source_commit=git('rev-parse','HEAD').strip(),
        case_count=len(case_ids),case_ids=case_ids,checks=checks,devices=devices,dependencies=deps,
        evidence_references=refs,rocm_evidence=trace[0]['evidence'],cuda_evidence=native_runs['cases'][0]['evidence'],
        comparison_mode='ASYNC_GPU_JPEG_EXACT_SERIAL_REGRESSION_AND_NATIVE_BASELINE_OBSERVATION',
        remaining='Full held-out native/CPU pixel equivalence; maximum-dimension/64-bit transform indices; nonprofiled latency/throughput distributions and peak memory; prefix dispatch measurements; committed cold rebuild and final review.')
    write(e.path/'qualification.json',q);q['qualification_id']=e.id
    q['evidence']=e.finish('PASSED',dict(status='PASSED',checks=checks));write(REPORT,q)
    record('IMG-01','正式入口40项子集资格封存：原20项加16组线程/混合尺寸/错误合同、3预分配trace和固定输入生命周期；完整保留集/大索引/性能/冷构建未完成，保持PARTIAL。',[q['evidence']]);print(q['evidence'])

def publish():
    q=json.loads(REPORT.read_text());proof=ROOT/q['evidence'];frozen=json.loads((proof/'qualification.json').read_text())
    if (q['kind']!=KIND or q['contract_status']!='PARTIAL' or q['case_count']!=40 or
        {k:v for k,v in q.items() if k not in ('evidence','qualification_id')}!=frozen or
        not anchored_seal(proof,publication(proof),qualification=True) or
        any(not anchored_seal(ROOT/ref,publication(ROOT/ref)) for ref in q['evidence_references']) or
        any(digest(ROOT/n)!=h for n,h in q['dependencies'].items())):raise ValueError('unpublished or stale qualification')
    catalog=json.loads((ROOT/'migration/samples.yaml').read_text());sample=next(s for s in catalog['samples'] if s['id']==SAMPLE)
    proposed=dict(sample,selected_validation=q)
    checked=inspect(proposed)
    if checked['status']!='PASSED':raise ValueError(checked['errors'])
    missing=['IMG-01/held-out-native-CPU-equivalence','IMG-01/64bit-transform-indices',
             'IMG-01/performance-distributions-peak-memory','IMG-01/prefix-dispatch-measurements','IMG-10/committed-cold-rebuild-final-review']
    sample.update(status='PARTIAL',level='L4',reason_code='VALIDATED_I5_ASYNC_GPU_JPEG_INSTANCES_SUBSET',selected_validation=q,
        actual_library='Project HIP baseline/optimized JPEG color, FDCT, Huffman, checked parallel prefix, pinned buffers and event-driven slots; CPU markers/DHT design',
        backend_library='HIP async full baseline/optimized JPEG + CPU libjpeg-turbo DHT/header design',
        equivalence='GPU_ASYNC_JPEG_WITH_BOUNDED_CPU_THREAD_CALIBRATION',required_cases=q['case_ids']+missing,passed_cases=q['case_ids'],
        reason='原20项子集及新增16组线程/状态/混合尺寸/错误合同通过；3组单图预分配trace证实每slot每run仅一次RGB上传、稳态零扩容及全部请求实际GPU编码，26件产品逐字节回归。固定输入所有权和重新准备通过，准备/编码/端到端计时分开记录。完整保留集、最大尺寸64位索引、无profiler性能分布/峰值内存、prefix路径阈值和冷构建待完成，保持PARTIAL。',
        cuda_baseline='PASSED',cuda_baseline_scope='Unmodified original CMake/C++20; seven bounded native CLI cases,19 independent decoded products on physical5090 GPU1.',
        cuda_baseline_reason='历史构建失败保留；使用原始CMake所需C++20重新构建并运行成功。',
        cuda_comparison='BLOCKED',cuda_comparison_mode='NATIVE_BASELINE_RESTORED_FULL_EQUIVALENCE_PENDING',
        cuda_comparison_reason='原始CUDA构建和七组运行已恢复；AMD新路径的完整保留集CPU/native像素等价门槛尚未签发，不把原生观察当作完整三方验收。',
        active_batch='IMG-01',retry_condition=q['remaining'],next_step='完成IMG-01剩余原始入口合同与冷构建；IMG-02–IMG-10仍待实施。',
        reproduce='\n'.join('HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 /opt/venv/bin/python '+command for command in
            ['tools/moat/image_encoder_instances_v2.py build','tools/moat/image_encoder_instances_v2.py run','tools/moat/image_encoder_instances_v2_trace.py','tools/moat/image_encoder_instances_v2_compare.py']))
    if not any(a.get('qualification_id')==q['qualification_id'] for a in sample['attempts']):sample['attempts'].append(q)
    for ref in [q['evidence'],q['rocm_evidence'],q['cuda_evidence'],'migration/reports/image-completion-IMG-01.md',
                'migration/reports/image-encoder-instances-v2-runs.json','migration/reports/image-encoder-instances-v2-comparison.json']:
        if ref not in sample['evidence']:sample['evidence'].append(ref)
    write(ROOT/'migration/samples.yaml',catalog)
    write(ROOT/'migration/reports/image-encoder-instances-v2-publication.json',dict(status='PUBLISHED_PARTIAL',sample_id=SAMPLE,qualification=q['evidence']))
    record('IMG-01','已将异步编码器40项当前子集资格发布到主表；线程/混合尺寸/错误合同和单图预分配证据补齐，图像整例计数仍13/26。',[q['evidence'],'migration/reports/image-encoder-instances-v2-publication.json'])
    print('PUBLISHED_PARTIAL')

def negative():
    profile=json.loads((ROOT/'migration/rewrite/image-encoder-instances-v2-profile.json').read_text())
    names=['image-encoder-instances-v2-comparison.json','image-encoder-pipeline-runs.json',
           'image-encoder-pipeline-trace.json','image-checked-prefix-runs.json','image-checked-prefix-oversize.json',
           'image-encoder-runtime-runs.json','image-encoder-preallocation-runs.json']
    groups=[read(n) for n in names]
    e=Experiment('I5','async-encoder-qualification-coverage-negatives','CPU-negative',sources=[__file__,*[ROOT/'migration/reports'/n for n in names],
        ROOT/'migration/rewrite/image-encoder-instances-v2-profile.json',ROOT/'migration/rewrite/image-encoder-pipeline-profile.json',ROOT/'migration/rewrite/image-checked-prefix-profile.json',
        ROOT/'migration/rewrite/image-encoder-runtime-profile.json',ROOT/'migration/rewrite/image-encoder-preallocation-profile.json'])
    checks=[dict(check='complete-original-coverage-accepted',passed=all(c['passed'] for c in coverage_checks(profile,*groups)))]
    for index,name in enumerate(names):
        for mutation in ('duplicate-sealed-case','missing-case'):
            changed=copy.deepcopy(groups)
            if mutation=='duplicate-sealed-case':changed[index][-1]=copy.deepcopy(changed[index][0])
            else:changed[index].pop()
            checks.append(dict(check=mutation+'-'+name,passed=not all(c['passed'] for c in coverage_checks(profile,*changed))))
    changed=copy.deepcopy(groups);changed[0][0]['products'].pop()
    checks.append(dict(check='missing-compared-JPEG-rejected',passed=not all(c['passed'] for c in coverage_checks(profile,*changed))))
    changed=copy.deepcopy(groups);changed[-1][0]['products'].pop()
    checks.append(dict(check='missing-prepared-JPEG-rejected',passed=not all(c['passed'] for c in coverage_checks(profile,*changed))))
    changed=copy.deepcopy(groups);changed[-2][0]['products'].pop()
    checks.append(dict(check='missing-runtime-JPEG-rejected',passed=not all(c['passed'] for c in coverage_checks(profile,*changed))))
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(status=status,checks=checks)
    write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'VALIDATOR_GAP',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-instances-v2-qualification-negatives.json',row)
    record('IMG-01','完整冻结ID/逐case产品集合绑定扩展到运行与预分配：17项删减/重复反向检查 '+status+'。',[row['evidence']]);print(status)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['qualify','publish','negative']);args=p.parse_args();globals()[args.action]()
