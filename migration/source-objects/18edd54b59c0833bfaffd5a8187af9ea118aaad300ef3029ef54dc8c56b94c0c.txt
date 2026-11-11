#!/usr/bin/env python3
"""Build and execute the stage C ABI; CPU comparison runs in a separate environment."""
import json, shutil
from pathlib import Path
from experiment import ROOT, Experiment, write, digest
from snapshot import capture
from image_progress import record

def main():
    folder = ROOT/'rocm/common/image'
    source = folder/'canny_stages.hip'
    header = folder/'canny_stages.h'
    caller = ROOT/'rocm/probes/image/canny_stages.cpp'
    contract = ROOT/'migration/rewrite/image-canny-stages-contract.json'
    case_plan = ROOT/'migration/rewrite/image-canny-stage-cases.json'
    observed = capture()
    e = Experiment('I1', 'Canny-GPU-stages-build', 'rocm-build', sources=[__file__, source, header, caller, contract, case_plan])
    write(e.path/'backend.observed.json', observed)
    core = Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core')
    overlay = ROOT/'build/rocm-sdk-overlay'
    library = e.path/'libimage_stages.so'
    binary = e.path/'canny_stages'
    flags = ['hipcc', '--rocm-path='+str(overlay), '--hip-path='+str(overlay),
             '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),
             '--offload-arch=gfx1201', '-std=c++17', '-O2', '-D__HIP_PLATFORM_AMD__']
    rc = e.command(flags+['-shared', '-fPIC', '-MMD', '-MF', str(e.path/'library.d'),
                         '-x', 'hip', str(source), '-o', str(library)], 'compile-shared-HIP-stages', timeout=300)
    if rc == 0:
        rc = e.command(flags+['-MMD', '-MF', str(e.path/'caller.d'), '-x', 'hip', str(caller),
                             '-L'+str(e.path), '-Wl,-rpath,'+str(e.path), '-limage_stages', '-o', str(binary)],
                       'compile-real-C-ABI-caller', timeout=300)
    if rc == 0: rc = e.command(['ldd', str(binary)], 'actual-caller-links')
    build = dict(status='BUILT' if rc == 0 else 'BUILD_ERROR',
                 sources={str(p.relative_to(ROOT)):digest(p) for p in [source, header, caller, contract]},
                 binary=str(binary.relative_to(ROOT)), library=str(library.relative_to(ROOT)), experiment_id=e.id)
    if rc == 0: build.update(binary_sha256=digest(binary), library_sha256=digest(library))
    write(e.path/'build.json', build)
    build['evidence'] = e.finish('EXECUTED' if rc == 0 else 'BUILD_ERROR')
    write(ROOT/'migration/reports/image-I1-Canny-stages-build.json', build)
    if rc:
        record('I1', '共享HIP Canny阶段构建失败，实际编译日志已保留。', [build['evidence']])
        return rc
    rows=[]
    for case in json.loads(case_plan.read_text())['cases']:
        fixture=ROOT/case['fixture']
        if digest(fixture/'manifest.json')!=case['manifest_sha256']:raise RuntimeError('frozen fixture changed')
        r=Experiment('I1', 'Canny-GPU-stages', 'rocm-run', case=case['case'],
                     sources=[__file__,source,header,caller,contract,case_plan], parent=e.id,
                     comparison_id=case['case']+'/'+digest(fixture/'manifest.json'))
        write(r.path/'backend.observed.json', observed)
        shutil.copytree(fixture, r.path/'inputs')
        out=r.path/'outputs';out.mkdir()
        if digest(binary)!=build['binary_sha256'] or digest(library)!=build['library_sha256']:
            raise RuntimeError('binary changed since build')
        result=r.command([str(binary),str(r.path/'inputs'),str(out)],'actual-HIP-stage-C-ABI',timeout=180)
        row=dict(case=case['case'],return_code=result, build=build,
                 inputs=str((r.path/'inputs').relative_to(ROOT)),outputs=str(out.relative_to(ROOT)),
                 input_manifest_sha256=digest(fixture/'manifest.json'),
                 output_sha256={p.name:digest(p) for p in out.glob('*.bin')}, experiment_id=r.id,
                 scope='Sobel/L2/NMS stages, not complete Canny sample qualification')
        write(r.path/'run.json',row)
        row['evidence']=r.finish('EXECUTED' if result==0 else 'RUNTIME_ERROR')
        rows.append(row);write(ROOT/'migration/reports/image-I1-Canny-stages-runs.json',rows)
        record('I1',case['case']+'：真实HIP阶段C ABI执行'+('成功，等待独立CPU逐元素检查。' if result==0 else '失败，保留日志。'),[row['evidence']])
    return int(any(row['return_code'] for row in rows))

if __name__=='__main__':raise SystemExit(main())
