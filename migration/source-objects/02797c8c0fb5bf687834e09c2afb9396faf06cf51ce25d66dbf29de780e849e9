#!/usr/bin/env python3
"""Actual GPU view rejection and allocation-failure cleanup controls."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,digest,write
from snapshot import capture
from image_completion_progress import record

def main():
    header=ROOT/'rocm/common/image/watershed_v2.hpp';probe=ROOT/'rocm/probes/image/watershed_v2_controls.cpp';contract=ROOT/'migration/rewrite/image-watershed-completion-contract.json'
    e=Experiment('I3','watershed-view-and-allocation-controls','rocm',sources=[__file__,header,probe,contract]);write(e.path/'backend.observed.json',capture());binary=e.path/'controls'
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay'
    flags=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-I'+str(ROOT/'rocm/common'),'-x','hip']
    rc=e.command([*flags,str(probe),'-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(binary)],'build',timeout=300);checks=[]
    if not rc:
        rc=e.command([str(binary)],'actual-view-and-workspace-controls',timeout=180);command=e.commands[-1];lines=(e.path/command['stdout']).read_text().splitlines()
        invalid=[s for s in lines if s.startswith('INVALID ')];failures=[s for s in lines if s.startswith('ALLOCATION_FAILURE ')];recovery=[s for s in lines if s.startswith('RECOVERY ')]
        checks=[dict(check='18-invalid-views-rejected-before-allocation-and-writes',passed=len(invalid)==18 and all('no_allocations=1 unchanged=1' in s for s in invalid)),dict(check='all9-workspace-allocation-failures-leak-free-and-no-caller-writes',passed=len(failures)==9 and all('live=0 unchanged=1' in s for s in failures)),dict(check='same-process-recovery-after-allocation-failures',passed=recovery==['RECOVERY successful=1 live=0 pixels=64'])]
    status='PASSED' if rc==0 and checks and all(c['passed'] for c in checks) else 'SELF_TEST_FAILED';result=dict(status=status,return_code=rc,checks=checks,binary_sha256=digest(binary) if binary.exists() else None);write(e.path/'result.json',result);result['evidence']=e.finish(status,dict(status=status,checks=checks));write(ROOT/'migration/reports/image-watershed-v2-controls.json',result)
    record('IMG-02','实际GPU边界/资源检查：'+status+'，18非法视图、9逐分配故障及同进程恢复；检查拒绝前不分配/不写调用方数据、每个工作区均释放。',[result['evidence']]);print(status,result['evidence']);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
