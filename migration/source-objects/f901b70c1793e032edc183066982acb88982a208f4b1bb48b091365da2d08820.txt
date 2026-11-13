#!/usr/bin/env python3
"""Bind transform and strict CPU oracle proofs to actual candidate builds."""
import copy,json
from experiment import ROOT,Experiment,digest,write
from audit import check as audit_check
from image_completion_progress import record

BUILD=ROOT/'migration/reports/image-encoder-math-candidate-build.json'

def sealed(row,filename='result.json'):
    path=ROOT/row['evidence']
    if audit_check(path) or json.loads((path/filename).read_text())!={k:v for k,v in row.items() if k!='evidence'}:raise ValueError('sealed record identity')
    return path

def current(build):
    path=sealed(build,'build.json')
    if build['status']!='BUILT' or any(digest(ROOT/n)!=h for n,h in build['dependencies'].items()):raise ValueError('candidate build dependencies')
    for binary in [build,build['probe']]:
        if digest(ROOT/binary['binary'])!=binary['binary_sha256']:raise ValueError('candidate binary SHA')
    return path

def probe_binding(row,build,case,item):
    path=sealed(row);source=json.loads((path/'source.json').read_text());commands=json.loads((path/'commands.json').read_text())
    if row['status']!='PASSED' or not all(c['passed'] for c in row['checks']) or row['binary_sha256']!=build['probe']['binary_sha256'] or row['input']!=item:raise ValueError('probe binary/input identity')
    if source['dependencies'].get(str(BUILD.relative_to(ROOT)))!=digest(BUILD) or any(source['dependencies'].get(n)!=h for n,h in build['dependencies'].items()):raise ValueError('probe compiled source/build receipt')
    if len(commands)!=1:raise ValueError('exact probe command')
    command=commands[0];argv=command['argv']
    if command['return_code']!=0 or len(argv)!=7 or argv[0]!=str(ROOT/build['probe']['binary']) or argv[2:6]!=[str(item['width']),str(item['height']),str(case['sampling']),str(case['quality'])]:raise ValueError('actual probe path/arguments')
    if digest(__import__('pathlib').Path(argv[1]))!=item['rgb_sha256']:raise ValueError('actual raw RGB input identity')
    return path

def cpu_binding(reference):
    path=sealed(reference)
    if reference['status']!='PASSED' or not all(c['passed'] for c in reference['checks']):raise ValueError('strict CPU oracle checks')
    if digest(ROOT/reference['binary'])!=reference['binary_sha256'] or digest(ROOT/reference['library'])!=reference['library_sha256']:raise ValueError('strict CPU actual binary/library')
    commands=json.loads((path/'commands.json').read_text())
    if len(commands)!=1 or commands[0]['return_code']!=0 or str(ROOT/reference['binary']) not in commands[0]['argv']:raise ValueError('CPU build command')
    return path

def main():
    profile=ROOT/'migration/rewrite/image-encoder-math-variant-v2-profile.json';p=json.loads(profile.read_text())
    report=ROOT/'migration/reports/image-encoder-math-cpu.json';rows=json.loads(report.read_text())
    probe_report=ROOT/'migration/reports/image-encoder-math-probe.json';probes=json.loads(probe_report.read_text());lookup={r['case']:r for r in probes}
    amd_report=ROOT/'migration/reports/image-encoder-math-amd.json';amd=json.loads(amd_report.read_text())
    reference_report=ROOT/'migration/reports/image-encoder-math-reference-build.json';reference=json.loads(reference_report.read_text());build=json.loads(BUILD.read_text())
    if [r['case'] for r in rows]!=[c['id'] for c in p['cases']] or [r['case'] for r in amd]!=[c['id'] for c in p['cases']] or len(rows)!=80:raise ValueError('complete 80-case quality matrix required')
    current(build);cpu_binding(reference);bound=[];checks=[];references={build['evidence'],reference['evidence']}
    e=Experiment('I5','encoder-mathematical-evidence-binding','CPU-validation',sources=[__file__,profile,report,probe_report,amd_report,reference_report,BUILD,*[ROOT/n for n in build['dependencies']]])
    try:
        for case,row,run in zip(p['cases'],rows,amd):
            item=next(i for i in p['inputs'] if i['id']==case['input']);probe=lookup[case['id'].rsplit('-opt',1)[0]+'-opt0']
            proof=sealed(row);runproof=sealed(run);probe_binding(probe,build,case,item)
            if row['status']!='PASSED' or not all(c['passed'] for c in row['checks']):raise ValueError('numerical quality case failed')
            if run['binary_sha256']!=build['binary_sha256'] or run['build_report_sha256']!=digest(BUILD):raise ValueError('actual entry build identity')
            commands=json.loads((runproof/'commands.json').read_text())
            if len(commands)!=1 or commands[0]['argv'][0]!=str(ROOT/build['binary']) or commands[0]['return_code']!=0:raise ValueError('actual entry command')
            source=json.loads((proof/'source.json').read_text())
            if source['dependencies'].get(str(reference_report.relative_to(ROOT)))!=digest(reference_report) or source['dependencies'].get(str(probe_report.relative_to(ROOT)))!=digest(probe_report):raise ValueError('actual mathematical oracle receipt')
            refs=set(row['evidence_references'])|{row['evidence'],probe['evidence'],reference['evidence'],build['evidence']};references.update(refs)
            bound.append(dict(case=case['id'],status='PASSED',evidence_references=sorted(refs),candidate_binary_sha256=build['binary_sha256'],probe_binary_sha256=build['probe']['binary_sha256'],strict_CPU_binary_sha256=reference['binary_sha256']))
            checks.append(dict(check='complete-identity-'+case['id'],passed=True))
        case=p['cases'][0];item=next(i for i in p['inputs'] if i['id']==case['input']);probe=lookup[case['id']]
        for name in ['probe-sha','probe-input','build-sha','build-path']:
            altered=copy.deepcopy(probe);other=copy.deepcopy(build)
            if name=='probe-sha':altered['binary_sha256']='0'*64
            elif name=='probe-input':altered['input']['rgb_sha256']='0'*64
            elif name=='build-sha':other['probe']['binary_sha256']='0'*64
            else:other['probe']['binary']=other['binary']
            try:probe_binding(altered,other,case,item);rejected=False
            except (ValueError,KeyError):rejected=True
            checks.append(dict(check='reject-'+name,passed=rejected))
    except Exception as error:checks.append(dict(check='binding-exception',passed=False,error=repr(error)))
    status='PASSED' if len(bound)==80 and checks and all(c['passed'] for c in checks) else 'FAILED'
    result=dict(status=status,checks=checks,cases=bound,evidence_references=sorted(references),scope='Supplemental build/probe/strict CPU binding of unchanged numerical results; no rerun or changed mathematics claimed.')
    write(e.path/'result.json',result);result['evidence']=e.finish('PASSED' if status=='PASSED' else 'VALIDATOR_GAP',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-math-binding.json',result)
    record('IMG-01','数学证明完整构建/探针/CPU参考绑定：'+status+'；补齐引用并加入4项错身份反向检查，不覆盖先前数值记录。',[result['evidence']]);print(status,[c for c in checks if not c['passed']]);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
