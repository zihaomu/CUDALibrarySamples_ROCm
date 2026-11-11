#!/usr/bin/env python3
"""Build a lossless task and backend index from the existing support catalog."""
import collections
import json
from pathlib import Path
import re
import shutil
import sys
from experiment import ROOT, write, digest
sys.path.insert(0,str(ROOT/'tools/migration'))
from catalog import CANDIDATES

TARGETS = [
 ('R1','gemm3m','cuBLAS/Level-3/gemm3m/cublas_gemm3m_example.cu'),
 ('R1','herk3m','cuBLAS/Extensions/Cherk3mEx/cublas_Cherk3mEx_example.cu'),
 ('R1','syrk3m','cuBLAS/Extensions/Csyrk3mEx/cublas_Csyrk3mEx_example.cu'),
 ('R1','planar','cuBLASLt/LtPlanarComplex/main.cpp'),
 ('R1','igemm','cuBLASLt/LtIgemmTensor/main.cpp'),
 ('R2','lu','MathDx/cuSolverDx/01_Linear_Solve/getrf_partial_pivot_block.cu'),
 ('R2','posv','MathDx/cuSolverDx/00_Introduction/posv_batched_block.cu'),
 ('R2','trsm','MathDx/cuSolverDx/07_BLAS/trsm_batched_block.cu')]


def phase(s):
    source=s['source']
    if s['status']=='PASSED':return 'R8'
    if s['reason_code']=='BINDING_OR_FRONTEND_MIGRATION_REQUIRED':return 'R5'
    if s['status']=='PARTIAL':return 'R3'
    if s['status']=='UNSUPPORTED':return 'R7'
    for batch,_,path in TARGETS:
        if source==path:return batch
    if s['family'] in ['cuBLAS','cuBLASLt','cuSOLVER','cuSPARSE','cuTENSOR',
                       'cuSOLVERSp2cuDSS','nvMatmulHeuristics','NPP','NPP+','nvCOMP','cuDSS']:
        return 'R4'
    return 'R6'


def main():
    from bootstrap import validate_existing
    lock_path=ROOT/'migration/moat/lock.json'
    if lock_path.exists():validate_existing(ROOT)
    task_path=ROOT/'migration/moat/tasks.json'
    prior=json.loads(task_path.read_text()) if task_path.exists() else {}
    previous={r['sample_id']:r for r in prior.get('tasks',[])}
    spec_path=ROOT/'migration/rewrite/first-eight.json'
    old_spec=json.loads(spec_path.read_text()) if spec_path.exists() else {}
    prior_profiles={p['sample_id']:p for p in old_spec.get('profiles',[])}
    cat=json.loads((ROOT/'migration/samples.yaml').read_text())
    samples=cat['samples']; tasks=[]; routes=[]
    names=['hipBLASLt','hipSPARSELt','hipBLAS','rocBLAS','hipSOLVER','rocSOLVER',
           'hipSPARSE','rocSPARSE','hipFFT','rocFFT','hipTensor','rocRAND',
           'hipRAND','RCCL','rocJPEG','hipCOMP','RPP','MPI','HIP','libjpeg','liblz4','Snappy','ProjectMatrixHelpers']
    libraries={name:dict(id=name,version=None,status='CANDIDATE',qualified_samples=[],
                         observation_scope='Existing catalog only; per-run dependencies recorded separately')
               for name in names}
    library_path=ROOT/'migration/libraries.json'
    old_libraries=json.loads(library_path.read_text()) if library_path.exists() else {}
    for row in old_libraries.get('libraries',[]):
        libraries[row['id']]=dict(libraries.get(row['id'],{}),**row)
    # This is a current index, not an append-only qualification history. In
    # particular, withdrawn qualifications must disappear from library counts.
    for row in libraries.values():
        row['qualified_samples']=[]
    for s in samples:
        task=dict(sample_id=s['id'],source=s['source'],family=s['family'],
            primary_phase=phase(s),baseline_status=s['status'],state='OWED' if s['status']!='PASSED' else 'HISTORICAL_QUALIFIED',
            reason_code=s['reason_code'],reason=s['reason'],retry_condition=s.get('retry_condition'),
            implementation=s.get('implementation'),selected_validation=s.get('selected_validation'),
            required_cases=s['required_cases'],prerequisites=[],experiments=[])
        if s['id'] in previous:
            task.update(previous[s['id']])
        task.update(current_status=s['status'],current_reason=s['reason'],implementation=s.get('implementation'),
                    selected_validation=s.get('selected_validation'),active_batch=s.get('active_batch'),required_cases=s['required_cases'])
        if s['status']=='PASSED' and task['state'] in ['OWED','HISTORICAL_QUALIFIED','QUALIFIED']:
            task['state']='QUALIFIED' if s['reason_code']=='VALIDATED_MOAT_REWRITE' else 'HISTORICAL_QUALIFIED'
        elif task['state'] in ['QUALIFIED','HISTORICAL_QUALIFIED']:
            task['state']='OWED'
        tasks.append(task)
        actual=s.get('actual_library') or ''
        components=[n for n in names if re.search(r'(?<![A-Za-z])'+re.escape(n)+r'(?![A-Za-z])',actual,re.I)]
        for n in components:
            if s['status']=='PASSED' and s['id'] not in libraries[n]['qualified_samples']:libraries[n]['qualified_samples'].append(s['id'])
        routes.append(dict(sample_id=s['id'],route_id=s['id']+'::catalog',
            actual_library=s.get('actual_library'),backend_library=s.get('backend_library'),
            candidate_libraries=s['candidate_libraries'],components=components,
            implementation=s.get('implementation'),method=s.get('equivalence'),
            status=s['status'],scope=s['reason'],evidence=s['evidence'],
            cpu_stage_review='EXPLICIT_HOST_DESCRIPTOR_WITH_HIP_USER_STORAGE' if 'ProjectMatrixHelpers' in actual else 'REQUIRES_EXPLICIT_PER_ROUTE_REVIEW' if 'CPU' in actual else 'NOT_IN_DECLARED_LIBRARY_STRING'))
    for lib in libraries.values():
        if lib['qualified_samples']:lib['status']='HISTORICALLY_QUALIFIED_SCOPED'
        elif lib.get('status')=='HISTORICALLY_QUALIFIED_SCOPED':lib['status']='OBSERVED_NOT_CURRENTLY_QUALIFIED'
    write(ROOT/'migration/libraries.json',dict(schema_version=1,libraries=list(libraries.values()),
        modules={k:dict(candidates=v) for k,v in CANDIDATES.items()}))
    write(ROOT/'migration/backend-routes.json',dict(schema_version=1,routes=routes))
    write(ROOT/'migration/moat/tasks.json',dict(schema_version=1,
        baseline_catalog_sha256=prior.get('baseline_catalog_sha256',digest(ROOT/'migration/samples.yaml')),tasks=tasks,
        phase_counts=dict(collections.Counter(x['primary_phase'] for x in tasks))))
    specs=[]
    for batch,kind,source in TARGETS:
        s=next(x for x in samples if x['source']==source)
        profile=dict(batch=batch,kind=kind,source=source,sample_id=s['id'],
            original_sha256=digest(ROOT/source),
            cases=['original','changed-values','irregular','layout','repeat','boundary'],
            state='PLANNED',numeric_rule='Integer exact; floating scaled error/residual; original half overflow explicitly checked')
        profile.update(prior_profiles.get(s['id'],{}));specs.append(profile)
    write(ROOT/'migration/rewrite/first-eight.json',dict(old_spec,schema_version=1,profiles=specs))
    control=ROOT.parent/'MOAT_CUDALibrarySamples_ROCm'
    skill=control/'.claude/skills/cuda-to-rocm/SKILL.md'
    if not lock_path.exists():write(lock_path,dict(schema_version=1,
        control_checkout='../MOAT_CUDALibrarySamples_ROCm',
        upstream_url='https://github.com/AMD-Ecosystem/moat',
        upstream_commit='7b5082cc516c61b91038295346adbe8a1b5d8315',
        skill='.claude/skills/cuda-to-rocm/SKILL.md',skill_sha256=digest(skill),
        state_library_sha256=digest(control/'utils/moatlib.py'),
        project='CUDALibrarySamples_ROCm',implementation_branch='rocm',
        required_profile='linux-gfx1201-rocm10.1',
        unverified_platforms=['wave64','windows'],
        state_sync='local bare origin; no writes to AMD-Ecosystem upstream'))
    print(json.dumps(dict(samples=len(tasks),pending=sum(x['baseline_status']!='PASSED' for x in tasks),
        modules=len(CANDIDATES),phases=collections.Counter(x['primary_phase'] for x in tasks))))


if __name__=='__main__':main()
