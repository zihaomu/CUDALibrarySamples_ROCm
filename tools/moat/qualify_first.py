#!/usr/bin/env python3
"""Issue composite sample qualifications only after all source/input/semantic gates."""
import argparse,fcntl,json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest,git
from inputs import verify
from audit import check

def load(name):return json.loads((ROOT/'migration/reports'/name).read_text())

REVIEW_PATHS=['rocm','tools/moat','cmake','.agents','AGENTS.md','migration/rewrite/first-eight.json','tests/fixtures/rewrite-first','tests/fixtures/rewrite-native-original']
def review_identity(review):
    commit=review.get('source_commit','')
    if not commit:return False
    try:
        import subprocess
        subprocess.run(['git','merge-base','--is-ancestor',commit,'HEAD'],cwd=ROOT,check=True,capture_output=True)
        listing=git('ls-tree','-r',commit,'--',*REVIEW_PATHS).splitlines()
        current=set(git('ls-tree','-r','--name-only','HEAD','--',*REVIEW_PATHS).splitlines())
        expected={line.split('\t',1)[1]:line.split()[2] for line in listing}
        if set(expected)!=current or git('ls-files','--others','--exclude-standard','--',*REVIEW_PATHS).strip():return False
        # hash-object reads the current bytes, including uncommitted changes.
        p=subprocess.run(['git','hash-object','--stdin-paths'],cwd=ROOT,input='\n'.join(expected)+'\n',capture_output=True,text=True,check=True)
        return p.stdout.splitlines()==list(expected.values())
    except (OSError,ValueError,subprocess.CalledProcessError):return False

def auxiliary(evidence,required_sources,*,parent=None,comparison=None,input_hash=None,expected_outcome='PASSED'):
    directory=ROOT/evidence
    try:
        if check(directory):return False
        source=json.loads((directory/'source.json').read_text())['dependencies']
        if any(source.get(n)!=digest(ROOT/n) for n in required_sources):return False
        manifest=json.loads((directory/'manifest.json').read_text());validation=json.loads((directory/'validation.json').read_text())
        if manifest['experiment_outcome']!=expected_outcome or not validation['checks'] or not all(c.get('passed') is True for c in validation['checks']):return False
        if parent is not None and manifest['parent_experiment_id']!=parent:return False
        if comparison is not None and manifest['comparison_id']!=comparison:return False
        if manifest['experiment_id']!=directory.name:return False
        if input_hash is not None:verify(ROOT/manifest['raw_artifact_dir']/'inputs',input_hash)
        return True
    except (OSError,KeyError,ValueError,TypeError):return False
def collect(profile):
    kind=profile['kind'];checks=[];references=[]
    def gate(name,value,**fields):checks.append(dict(check=name,passed=bool(value),**fields))
    required={'original','changed-values','irregular','layout','repeat','boundary'}
    required |= {'half-max'} if kind=='planar' else {'wave-stress'} if kind=='lu' else {'nonspd-second-minor'} if kind=='posv' else set()
    registered=json.loads((ROOT/'migration/rewrite/first-eight.json').read_text())['profiles']
    gate('frozen-nonempty-complete-case-contract',set(profile['cases'])==required and len(profile['cases'])==len(required) and profile in registered)
    review=load('rewrite-first-review.json');gate('independent-review',review.get('verdict')=='APPROVED' and not [r for r in review['findings'] if r['state']!='RESOLVED'] and review_identity(review))
    records={b:load(f'rewrite-first-{b}.json') for b in ['rocm','cuda']}
    validations={b:load(f'rewrite-first-{b}-validation.json') for b in ['rocm','cuda']}
    build=load('rewrite-first-builds.json')[kind]
    gate('current-compiled-dependencies',all((ROOT/n).is_file() and digest(ROOT/n)==sha for n,sha in build['dependencies'].items()))
    gate('current-binary-identity',digest(ROOT/build['binary'])==build['binary_sha256'])
    gate('current-build-recipe',build.get('build_recipe_sha256')==digest(ROOT/'tools/moat/build_first.py'))
    gate('original-source-identity',digest(ROOT/profile['source'])==profile['original_sha256'])
    for case in profile['cases']:
        key=kind+'/'+case;pair=[]
        for backend in ['rocm','cuda']:
            run=records[backend][key];validation=validations[backend][key]
            gate(backend+'/'+case+'/run',run['return_code']==0)
            gate(backend+'/'+case+'/current-validation',validation['status']=='PASSED' and validation.get('validation_source_sha256')==digest(ROOT/'tools/moat/first_reference.py') and validation['run']['experiment_id']==run['experiment_id'])
            gate(backend+'/'+case+'/sealed-current-oracle',auxiliary(validation['evidence'],['tools/moat/first_reference.py','tools/moat/inputs.py'],parent=run['experiment_id'],comparison=run['comparison_id'],input_hash=run['input_manifest_sha256']))
            fixture=ROOT/'tests/fixtures/rewrite-first'/kind/case
            gate(backend+'/'+case+'/registered-input',digest(fixture/'manifest.json')==run['input_manifest_sha256'])
            verify(ROOT/run['input_snapshot'],run['input_manifest_sha256'])
            for evidence in [run['evidence'],validation['evidence']]:
                gate(backend+'/'+case+'/seal/'+Path(evidence).name,not check(ROOT/evidence));references.append(evidence)
            pair.append(run['comparison_id'])
            if backend=='rocm':
                gate(backend+'/'+case+'/compiled-build',run['build']['experiment_id']==build['experiment_id'])
                observed=json.loads((ROOT/run['evidence']/'backend.observed.json').read_text())
                gate(backend+'/'+case+'/locked-environment',observed['image_id']=='sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03' and observed['rocm_release']=='10.1.0' and bool(observed['devices']) and all(d['physical_id']!=3 for d in observed['devices']))
        gate(case+'/identical-three-way-input',pair[0]==pair[1])
    negative=load('rewrite-first-negative.json');own=[c for c in negative['checks'] if c['check'].startswith('reject-'+kind+'-')]
    needed={'gemm3m':3,'herk3m':4,'syrk3m':4,'planar':4,'igemm':2,'lu':2,'posv':6,'trsm':2}[kind]
    gate('actual-negative-checks',len(own)==needed and all(c['passed'] for c in own));references += [c['evidence'] for c in own]
    for c in own:
        run=records['rocm'].get(kind+'/'+c.get('case',''),{})
        gate(c['check']+'/integrity-and-current-oracle',bool(run) and auxiliary(c['evidence'],['tools/moat/first_negative.py','tools/moat/first_reference.py','tools/moat/inputs.py'],parent=run.get('experiment_id'),comparison=run.get('comparison_id'),input_hash=run.get('input_manifest_sha256')))
    if profile['batch']=='R2':
        runtime=load('rewrite-first-runtime-checks.json');own=[r for r in runtime['tests'] if r['kind']==kind]
        gate('actual-invalid-descriptors',len(own)>=11 and all(r['passed'] for r in own));references += [r['evidence'] for r in own]
        for r in own:gate('runtime/'+r['test']+'/current-build-and-checker',auxiliary(r['evidence'],['tools/moat/first_runtime_checks.py','rocm/device/solver/block_solvers.hpp'],parent=build['experiment_id'],expected_outcome='EXPECTED_REJECTION'))
        native=load('rewrite-native-mathdx-validation.json')[kind]
        gate('native-device-original-CPU-and-HIP',native['status']=='PASSED' and native['rocm']['experiment_id']==records['rocm'][kind+'/original']['experiment_id'])
        gate('native-comparison-sealed-current-reference',auxiliary(native['evidence'],['tools/moat/validate_native_mathdx.py','tools/moat/first_reference.py','tools/moat/inputs.py'],parent=native['native']['experiment_id'],comparison=records['rocm'][kind+'/original']['comparison_id'],input_hash=records['rocm'][kind+'/original']['input_manifest_sha256']))
        gate('native-source-sealed',not check(ROOT/native['native']['evidence']) and native['native']['original_sha256']==digest(ROOT/profile['source']) and native['native']['experiment_id']==load('rewrite-native-mathdx.json')[kind]['experiment_id'])
        references.append(native['evidence'])
    return checks,build,sorted(set(references))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    profiles=json.loads((ROOT/'migration/rewrite/first-eight.json').read_text())['profiles'];results=[]
    if len(profiles)!=8 or {p['kind'] for p in profiles}!={'gemm3m','herk3m','syrk3m','planar','igemm','lu','posv','trsm'} or len({p['sample_id'] for p in profiles})!=8:raise SystemExit('Eight unique frozen sample profiles required')
    for p in profiles:
        checks,build,references=collect(p);passed=all(c['passed'] for c in checks)
        r=dict(sample_id=p['sample_id'],kind=p['kind'],status='PASSED' if passed else 'FAILED',checks=checks,source_commit=git('rev-parse','HEAD').strip(),implementation=build['implementation'],implementation_sha256=build['implementation_sha256'],dependencies=build['dependencies'],case_ids=p['cases'],case_count=len(p['cases']),evidence_references=references)
        if args.apply:
            if not passed:raise SystemExit('Refusing qualification: '+p['kind']+' '+str([c['check'] for c in checks if not c['passed']]))
            for backend,field in [('rocm','rocm_evidence'),('cuda','cuda_evidence')]:r[field]=load(f'rewrite-first-{backend}.json')[p['kind']+'/original']['evidence']
            r['cpu_report']='migration/reports/rewrite-first-rocm-validation.json'
            e=Experiment(p['batch'],p['sample_id'],'composite-qualification',sources=[__file__,ROOT/'tools/moat/first_reference.py',ROOT/'migration/rewrite/first-eight.json',ROOT/'migration/reports/rewrite-first-review.json'])
            write(e.path/'qualification.json',r);r['qualification_id']=e.id;r['evidence']=e.finish('PASSED',dict(status='PASSED',checks=checks))
            sample=load('rewrite-first-rocm.json')[p['kind']+'/original'];r['environment']=json.loads((ROOT/sample['evidence']/'backend.observed.json').read_text());r['devices']=r['environment']['devices'];r['scope']='MOAT rewrite original contract plus registered variants; composite qualification, not one process exit'
        results.append(r)
        print(p['kind'],r['status'],[c['check'] for c in checks if not c['passed']],flush=True)
    write(ROOT/'migration/reports/rewrite-first-qualification.json',dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',qualifications=results))
    if args.apply:
        routes={'gemm3m':'hipBLAS/rocBLAS three real SGEMMs + HIP complex split/merge','herk3m':'hipBLAS/rocBLAS three real SGEMMs + HIP Hermitian triangle epilogue','syrk3m':'hipBLAS/rocBLAS three real SGEMMs + HIP symmetric triangle epilogue','planar':'HIP negative-offset FP16 planar conversion + hipBLAS/rocBLAS FP32 3M + HIP FP16 output','igemm':'HIP COL32/COL4 packing/unpacking + native hipBLAS GemmEx INT8/INT32','lu':'HIP caller-kernel cooperative complex FP32 partial-pivot LU','posv':'HIP caller-kernel cooperative complex FP64 Cholesky and solve','trsm':'HIP caller-kernel cooperative real FP64 right/lower triangular solve'}
        with (ROOT/'migration/.state.lock').open('w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);path=ROOT/'migration/samples.yaml';cat=json.loads(path.read_text())
            for p,r in zip(profiles,results):
                s=next(s for s in cat['samples'] if s['id']==p['sample_id']);cases=['rewrite/'+c for c in p['cases']]+['rewrite/independent-negative-checks']
                if p['batch']=='R2':cases+=['rewrite/native-device-original','rewrite/invalid-descriptors']
                s.update(status='PASSED',level='L4',actual_library=routes[p['kind']],backend_library='rocBLAS' if p['batch']=='R1' else 'project HIP device algorithm',implementation=r['implementation'],selected_validation=r,required_cases=cases,passed_cases=cases,reason_code='VALIDATED_MOAT_REWRITE',reason='原始数据/精度/布局与登记扩展用例通过 AMD、独立 CPU、相同输入 CUDA 验收；真实执行语义、反向检查及独立复审完成。实际路线：'+routes[p['kind']]+'。性能未验收。',cuda_comparison='PASSED',cuda_baseline='PASSED' if p['kind']!='igemm' else 'BLOCKED',cuda_comparison_mode='NATIVE_DEVICE_ORIGINAL_PLUS_COMPATIBLE_CUDA_MATH' if p['batch']=='R2' else 'COMPATIBLE_CUDA_MATH_AND_NATIVE_PACK_MAP' if p['kind']=='igemm' else 'NATIVE_CUBLAS_OR_LT')
                s['attempts'].append(r)
                for evidence in [r['evidence'],'migration/reports/rewrite-first-qualification.json','migration/reports/rewrite-first-negative.json','migration/reports/rewrite-evidence-errata.json']:
                    if evidence not in s['evidence']:s['evidence'].append(evidence)
            write(path,cat)
        task_path=ROOT/'migration/moat/tasks.json';tasks=json.loads(task_path.read_text())
        for t in tasks['tasks']:
            r=next((r for r in results if r['sample_id']==t['sample_id']),None)
            if r:t.update(state='QUALIFIED',qualification_id=r['qualification_id'],experiments=t['experiments']+[r['qualification_id']],current_status='PASSED')
        write(task_path,tasks)
    return int(any(r['status']!='PASSED' for r in results))

if __name__=='__main__':raise SystemExit(main())
