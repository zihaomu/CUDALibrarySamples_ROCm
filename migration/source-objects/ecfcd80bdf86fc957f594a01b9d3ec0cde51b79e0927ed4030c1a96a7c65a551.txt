#!/usr/bin/env python3
"""Check candidate minimum-workspace geometry and read-only device preflight."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

PROFILE=ROOT/'migration/rewrite/image-encoder-capacity-profile.json'
SOURCE=ROOT/'rocm/probes/image/jpeg_frame_capacity.hip'

def expected(case,available):
    if not case['valid']:return dict(valid=False)
    w,h,s=case['width'],case['height'],case['sampling'];pixels=[];coefficients=[]
    for c in range(3):
        scale=s if c else 1;pw=(w+scale-1)//scale;ph=(h+scale-1)//scale
        pixels.append(pw*ph);coefficients.append(((pw+7)//8)*((ph+7)//8)*64)
    blocks=((w+8*s-1)//(8*s))*((h+8*s-1)//(8*s))*(6 if s==2 else 3)
    minimum=w*h*3+sum(pixels)+2*sum(coefficients)+blocks*651+((blocks+255)//256)*8+6792+(4100 if case['optimized'] else 0)
    safe=not case['optimized'] or 63*blocks<=0xffffffff
    return dict(valid=True,minimum_bytes=minimum,blocks=blocks,histogram_safe=safe,pixels=pixels,coefficients=coefficients,
        fits=[safe and minimum<=available,False,False,safe,safe,safe,safe],actual_capacity_rejected=not(safe and minimum<=available))

def main():
    from snapshot import capture
    from image_completion_inventory import closure
    p=json.loads(PROFILE.read_text());deps,missing=closure(SOURCE)
    if missing:raise ValueError(missing)
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay'
    e=Experiment('I5','JPEG-device-capacity-preflight','rocm-metadata-probe',sources=[__file__,PROFILE,*[ROOT/n for n in deps]])
    observed=capture();write(e.path/'backend.observed.json',observed);binary=e.path/'probe';source=e.path/'geometries.txt'
    source.write_text(''.join(f"{c['width']} {c['height']} {c['sampling']} {int(c['optimized'])}\n" for c in p['cases']))
    rc=e.command(['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),
        '--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-I'+str(ROOT/'rocm/common'),'-x','hip',str(SOURCE),'-o',str(binary),
        '-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64'],'build-capacity-preflight')
    rc=rc or e.command([str(binary),str(source)],'read-capacity-and-check-geometry')
    checks=[dict(check='build-and-probe',passed=rc==0)];data={};comparisons=[]
    try:
        data=json.loads((e.path/'logs/0002-read-capacity-and-check-geometry.stdout.log').read_text())
        checks.append(dict(check='all29-frozen-geometries',passed=len(data['rows'])==len(p['cases'])==29))
        domain,bus,tail=data['pci'].split(':');device,function=tail.split('.')
        pci=f'{int(domain,16):04x}:{int(bus,16):02x}:{int(device,16):02x}.{int(function,16)}'
        checks.append(dict(check='actual-readonly-device-query-on-GPU1',passed=pci in {d['pci_bdf'] for d in observed['devices'] if d['physical_id']==1} and 0<data['available_bytes']<=data['total_bytes']))
        for case,row in zip(p['cases'],data['rows']):
            reference=expected(case,data['available_bytes']);checks.append(dict(check=case['id'],passed=row==reference));comparisons.append(dict(case=case['id'],actual=row,reference=reference))
    except Exception as error:checks.append(dict(check='validation-exception',passed=False,error=repr(error)))
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(status=status,checks=checks,observed=data,comparisons=comparisons,
        binary_sha256=digest(binary) if binary.exists() else None,scope='Host geometry and actual GPU memory metadata; no image workspace allocation and no full-GPU-image claim.',experiment_id=e.id)
    write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-capacity.json',row)
    record('IMG-01','29组工作区几何/阈值/复用与真实GPU容量预检：'+status+'；未进行巨大分配，最低工作区和动态分配区别保留。',[row['evidence']]);print(status);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
