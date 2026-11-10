#!/usr/bin/env python3
"""Record a clean local clone and locked-container GPU reproduction."""
import json,os,shutil
from experiment import ROOT,Experiment,write,git

def main():
    head=git('rev-parse','HEAD').strip();e=Experiment('R8','clean-checkout-all-new-original-profiles','host-orchestrator',sources=[__file__,ROOT/'tools/moat/clean_replay.py'],hypothesis='A fresh committed checkout rebuilds M1 and all 21 new original profiles without historical artifacts')
    clone=ROOT.parent/('replay-'+e.id);rc=e.command(['git','clone','--no-local','--no-hardlinks',str(ROOT),str(clone)],'fresh-clone',timeout=180)
    if rc==0:rc=e.command(['git','checkout','--detach',head],'fixed-commit',cwd=clone)
    if rc==0:rc=e.command([str(ROOT.parent.parent/'rocm10-launch.sh'),'python3','tools/moat/clean_replay.py'],'locked-GPU-replay',cwd=clone,env=dict(HIP_VISIBLE_DEVICES='2'),timeout=900)
    replay=clone/'build/clean-replay';record=json.loads((replay/'result.json').read_text()) if (replay/'result.json').exists() else {}
    if replay.exists():
        shutil.copytree(replay,e.path/'replay')
    binding_report=clone/'migration/reports/rewrite-sparse-binding-build.json'
    if binding_report.exists():
        build=json.loads(binding_report.read_text());source=clone/build['evidence']
        # Keep the nested original seal as a named payload. The parent seal
        # commits every copied byte and owns its relocated raw fallback paths.
        if source.exists():
            destination=e.path/'fresh-fortran-build';shutil.copytree(source,destination)
            if (destination/'sealed.json').exists():(destination/'sealed.json').rename(destination/'original-build-seal.json')
            write(e.path/'fresh-fortran-build-result.json',build)
    lock_path=clone/'migration/environments/project.lock.json';lock=json.loads(lock_path.read_text()) if lock_path.exists() else {}
    observed=record.get('environment',{});devices=observed.get('devices',[])
    environment_ok=observed.get('image_id')==lock.get('foundation_image_id') and observed.get('rocm_release')==lock.get('rocm_release') and bool(devices) and all(d['physical_id']!=3 for d in devices)
    checks=[dict(check='fresh-clone-and-locked-replay-commands',passed=rc==0),dict(check='clean-fixed-source',passed=record.get('initial_clean') is True and record.get('source_commit')==head),dict(check='exact-project-environment-lock',passed=environment_ok),dict(check='16-M1-plus-21-new-original-profiles',passed=record.get('status')=='PASSED' and record.get('m1_tests')==16 and record.get('new_original_profiles')==21 and record.get('historical_artifacts_reused') is False)]
    valid=dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks)
    evidence=e.finish('PASSED' if valid['status']=='PASSED' else 'SELF_TEST_FAILED',valid,reason=None if valid['status']=='PASSED' else 'Clean-checkout replay failed; inspect preserved logs')
    write(ROOT/'migration/reports/rewrite-clean-checkout.json',dict(**valid,evidence=evidence,clone=str(clone),source_commit=head,replay=record));print(valid['status'],evidence);return int(valid['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
