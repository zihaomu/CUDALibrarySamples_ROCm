#!/usr/bin/env python3
"""Audit an image implementation checkpoint without promoting original samples."""
import json, sys
from experiment import ROOT, Experiment, write
from image_progress import record

def main():
    e=Experiment('I1','image-foundation-checkpoint','host-validation',sources=[__file__,ROOT/'tools/moat/audit.py',ROOT/'tools/migration/support_log_index.py'])
    # Earlier direct unittest invocation lacked PYTHONPATH and failed during import;
    # it ran no tests. Preserve that observation and the corrected command below.
    e.event('prior-host-invocation-observation',command='python3 -m unittest tools/moat/test_selected_proofs.py tools/moat/test_experiment.py',
            outcome='IMPORT_ERROR_BEFORE_TESTS',diagnostic="ModuleNotFoundError: No module named 'experiment'",return_code=1)
    commands=[(['env','PYTHONPATH='+str(ROOT/'tools/moat'),sys.executable,'-m','unittest','test_selected_proofs','test_experiment'],'existing-proof-and-recorder-regression'),
              ([sys.executable,str(ROOT/'tools/moat/audit.py')],'immutable-evidence-audit'),
              (['git','diff','--exit-code','d4046c61d598cc4aaffac0992a2768d16b60d6b8','--','NPP','NPP+','nvJPEG','nvJPEG2000','migration/samples.yaml','README.md','migration/reports/operator-support.json'],'originals-and-support-counts-unchanged'),
              (['cmp',str(ROOT/'migration/image-libraries-plan.md'),str(ROOT.parent/'doc/cuda_samples_on_rocm_image_libraries_plan.md')],'plan-mirror-identical')]
    checks=[]
    for command,phase in commands:
        rc=e.command(command,phase,timeout=600)
        checks.append(dict(check=phase,passed=rc==0,return_code=rc))
    validation=dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,
                    scope='Development checkpoint only; I0/I1 remain in progress and no original sample receives qualification.')
    ref=e.finish('PASSED' if validation['status']=='PASSED' else 'CONTRACT_AUDIT_FAILED',validation)
    write(ROOT/'migration/reports/image-checkpoint-validation.json',dict(**validation,evidence=ref))
    record('I1','图像基础实现检查点：'+validation['status']+'；既有资格/记录器回归、证据封存审计、原始源码与支持计数不变、计划镜像一致分别检查。',[ref])
    print(json.dumps(validation))
    return int(validation['status']!='PASSED')

if __name__=='__main__':raise SystemExit(main())
