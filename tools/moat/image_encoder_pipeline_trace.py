#!/usr/bin/env python3
"""Trace candidate-only JPEG slots; serial reference is a separate process."""
import csv,json,re
from pathlib import Path
from collections import Counter
from experiment import ROOT,Experiment,digest,write
from snapshot import capture
from image_completion_progress import record

def main():
    profile=json.loads((ROOT/'migration/rewrite/image-encoder-pipeline-profile.json').read_text())
    build=json.loads((ROOT/'migration/reports/image-encoder-pipeline-build.json').read_text())
    runs=json.loads((ROOT/'migration/reports/image-encoder-pipeline-runs.json').read_text())
    if build['status']!='BUILT' or digest(ROOT/build['binary'])!=build['binary_sha256'] or any(digest(ROOT/n)!=h for n,h in build['dependencies'].items()):raise ValueError('stale build')
    results=[]
    audit_source=ROOT/'rocm/probes/image/jpeg_copy_audit.cpp'
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core')
    build_audit=Experiment('I5','async-JPEG-copy-argument-observer','rocm-build',sources=[__file__,audit_source])
    audit_library=build_audit.path/'copy_audit.so'
    audit_rc=build_audit.command(['c++','-std=c++17','-shared','-fPIC','-O2','-D__HIP_PLATFORM_AMD__','-I'+str(core/'include'),str(audit_source),'-o',str(audit_library),'-ldl'],'build-copy-observer')
    audit_ref=build_audit.finish('EXECUTED' if audit_rc==0 else 'BUILD_ERROR')
    record('IMG-01','实际HIP copy参数观察器构建：'+('BUILT' if audit_rc==0 else 'FAILED')+'；用于覆盖ROCm把小传输实现为kernel的路径。',[audit_ref])
    if audit_rc:return 1
    for case_id in ['511x509-standard','511x509-optimized','device-only-0','device-only-1']:
        case=next(c for c in profile['cases'] if c['id']==case_id);original=next(r for r in runs if r['case']==case_id)
        e=Experiment('I5','async-JPEG-slot-trace','rocm-trace',case=case_id,sources=[__file__,audit_source,audit_library,ROOT/'migration/reports/image-encoder-pipeline-runs.json',*[ROOT/n for n in build['dependencies']]],parent=original['experiment_id'])
        observed=capture();write(e.path/'backend.observed.json',observed);out=e.path/'products'
        args=[str(ROOT/build['binary']),str(ROOT/case['path']),str(case['width']),str(case['height']),str(case['quality']),str(case['sampling']),str(int(case['optimized'])),'6',str(int(case['download'])),str(out)]
        rc=e.command(['rocprofv3','--kernel-trace','--hip-trace','--memory-copy-trace','--output-format','csv','--output-directory',str(e.path/'trace'),'--','env','LD_PRELOAD='+str(audit_library),*args],'trace-candidate-only-JPEG-slots',timeout=300)
        checks=[dict(check='profiler-success',passed=rc==0)];info={}
        try:
            traces=list((e.path/'trace').rglob('*kernel_trace.csv'));agents=list((e.path/'trace').rglob('*agent_info.csv'));copies=list((e.path/'trace').rglob('*memory_copy_trace.csv'))
            checks.append(dict(check='one-kernel-agent-and-optional-DMA-copy-table',passed=len(traces)==len(agents)==1 and len(copies)<=1))
            if len(traces)==len(agents)==1:
                rows=list(csv.DictReader(traces[0].open()));lookup={r['Node_Id']:r for r in csv.DictReader(agents[0].open())}
                streams={r['Stream_Id'] for r in rows if 'image_jpeg_checked_prefix::' in r['Kernel_Name']}
                active=[r for r in rows if r['Stream_Id'] in streams]
                application=[r for r in active if not r['Kernel_Name'].startswith('__amd_rocclr_')]
                runtime=[r for r in active if r['Kernel_Name'].startswith('__amd_rocclr_')]
                allowed={d['pci_bdf'] for d in observed['devices'] if d['physical_id']==1};real=True;pci=set()
                for row in active:
                    agent=lookup[row['Agent_Id'].split()[-1]];loc=int(agent['Location_Id']);address=f"{int(agent['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}"
                    pci.add(address);real &= address in allowed and int(row['End_Timestamp'])>int(row['Start_Timestamp']) and int(row['Grid_Size_X'])>0
                expected=102 if case['optimized'] else 96
                checks.append(dict(check='six-images-two-streams-all-pipeline-kernels-on-GPU1',passed=len(streams)==2 and len(application)==expected and len(active)==len(rows) and real and bool(active),kernel_count=len(application),expected=expected))
                overlap=sum(a['Stream_Id']!=b['Stream_Id'] and max(int(a['Start_Timestamp']),int(b['Start_Timestamp']))<min(int(a['End_Timestamp']),int(b['End_Timestamp'])) for i,a in enumerate(application) for b in application[i+1:])
                info=dict(streams=sorted(streams),pci=sorted(pci),kernel_count=len(application),runtime_kernel_count=len(runtime),overlapping_kernel_pairs=overlap,kernels=dict(Counter(r['Kernel_Name'] for r in active)))
                if copies:
                    memory=list(csv.DictReader(copies[0].open()));info['memory_copy_columns']=list(memory[0]) if memory else [];info['memory_copy_rows']=memory
            log=(e.path/'logs/0001-trace-candidate-only-JPEG-slots.stderr.log').read_text()
            observed_copies=[dict(kind=int(k),bytes=int(n),stream=s,rc=int(rc)) for k,n,s,rc in re.findall(r'JPEG_COPY_AUDIT kind=(\d+) bytes=(\d+) stream=(\S+) rc=(\d+)',log)]
            d2h=[r['bytes'] for r in observed_copies if r['kind']==2]
            expected_sizes=[8]*12+([4096,4]*6 if case['optimized'] else [])
            if case['download']:
                for path in sorted(out.glob('*.jpg')):
                    data=path.read_bytes();pos=2
                    while pos+4<=len(data):
                        marker=data[pos+1];length=int.from_bytes(data[pos+2:pos+4],'big');pos+=2+length
                        if marker==0xda:break
                    expected_sizes.append(len(data)-pos-2)
            checks.append(dict(check='actual-D2H-is-exact-metadata-plus-only-requested-payload',passed=bool(observed_copies) and all(r['rc']==0 for r in observed_copies) and sorted(d2h)==sorted(expected_sizes),observed_sizes=d2h,expected_sizes=expected_sizes))
            info['copy_argument_receipts']=observed_copies
            checks.append(dict(check='exact-traced-product-set',passed={p.name for p in out.glob('*.jpg')}==set(original['products'])))
            for name,value in original['products'].items():
                path=out/name;checks.append(dict(check='traced-product-exact-'+name,passed=path.is_file() and digest(path)==value['sha256']))
        except Exception as error:checks.append(dict(check='trace-validation-exception',passed=False,error=repr(error)))
        status='PASSED' if all(x['passed'] for x in checks) else 'FAILED'
        value=dict(case=case_id,status=status,checks=checks,observed=info,scope='Component trace; overlap measured. Device-only copy rows retained for exact metadata-versus-payload analysis.',experiment_id=e.id)
        write(e.path/'result.json',value);value['evidence']=e.finish('PASSED' if status=='PASSED' else 'PROFILER_FAILED',dict(status=status,checks=checks))
        results.append(value);write(ROOT/'migration/reports/image-encoder-pipeline-trace.json',results)
        record('IMG-01','候选独立进程trace '+case_id+'：'+status+'，实际kernel '+str(info.get('kernel_count'))+'，跨stream重叠对数 '+str(info.get('overlapping_kernel_pairs'))+'；copy表保存以核对设备模式。',[value['evidence']]);print(case_id,status,info.get('overlapping_kernel_pairs'),flush=True)
    return int(any(x['status']!='PASSED' for x in results))

if __name__=='__main__':raise SystemExit(main())
