#!/usr/bin/env python3
"""Reconstruct allocation lifetimes, reporting traced coverage explicitly."""
import csv,json,collections
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_encoder_math_binding import sealed

def reconstruct(events):
    live={};totals=collections.Counter();peaks=collections.Counter();allocations=collections.Counter()
    for event in sorted(events,key=lambda v:(v['time'],v['order'])):
        address=event['address']
        if event['allocate']:
            if address in live or event['bytes']<=0:raise ValueError('duplicate/nonpositive allocation')
            live[address]=(event['category'],event['bytes']);totals[event['category']]+=event['bytes'];allocations[event['category']]+=1
        else:
            if address not in live:raise ValueError('unmatched deallocation')
            category,size=live.pop(address)
            if event['bytes'] not in [0,size]:raise ValueError('deallocation size mismatch')
            totals[category]-=size
        for key,value in totals.items():peaks[key]=max(peaks[key],value)
        peaks['all_traced_device']=max(peaks['all_traced_device'],sum(v for k,v in totals.items() if k.startswith('device')))
    return dict(peak_bytes=dict(peaks),retained_at_trace_end_bytes=dict(totals),allocation_counts=dict(allocations),remaining_allocations=len(live))

def main():
    profile=ROOT/'migration/rewrite/image-encoder-performance-profile.json';p=json.loads(profile.read_text())
    reports={s:ROOT/f'migration/reports/image-encoder-memory-{s}.json' for s in ['amd','native']};rows={s:json.loads(v.read_text()) for s,v in reports.items()}
    for s,group in rows.items():
        if [r['case'] for r in group]!=[c['id'] for c in p['cases']] or any(r['status']!='OBSERVED' or not all(c['passed'] for c in r['checks']) for r in group):raise ValueError('complete successful memory traces required: '+s)
    sources=[__file__,profile,*reports.values(),ROOT/'tools/moat/image_encoder_math_binding.py']
    for group in rows.values():
        for row in group:proof=sealed(row);sources += [proof/'result.json',proof/'memory.json',proof/'sealed.json']
    e=Experiment('I5','encoder-peak-allocation-reconstruction','CPU-validation',sources=sources);checks=[];results=[];refs=[]
    try:
        for side,group in rows.items():
            for row in group:
                proof=ROOT/row['evidence'];memory=json.loads((proof/'memory.json').read_text());events=[];details={}
                if side=='amd':
                    tables=memory;allocation=next(v for k,v in tables.items() if 'memory_allocation' in k);agents=next(v['rows'] for k,v in tables.items() if 'agent_info' in k)
                    lookup={a['Node_Id']:a for a in agents};raw=ROOT/json.loads((proof/'manifest.json').read_text())['raw_artifact_dir']
                    api=next((raw/'trace').rglob('*hip_api_trace.csv'));manifest=json.loads((proof/'sealed.json').read_text())['files'];relative=str(api.relative_to(raw))
                    if digest(api)!=manifest[relative]['sha256']:raise ValueError('raw HIP event SHA drift')
                    functions={r['Correlation_Id']:r['Function'] for r in csv.DictReader(api.open())};used=[]
                    for index,a in enumerate(allocation['rows']):
                        allocate=a['Operation']=='MEMORY_ALLOCATION_ALLOCATE'
                        if not allocate and a['Operation']!='MEMORY_ALLOCATION_FREE':raise ValueError('unknown ROCm allocation operation')
                        function=functions.get(a['Correlation_Id']);category=None
                        if allocate:
                            agent=lookup[a['Agent_Id'].split()[-1]]
                            category='device_dynamic' if agent['Agent_Type']=='GPU' else 'host_pinned_API' if function=='hipHostMalloc' else 'host_runtime_pool'
                            used.append(dict(correlation=a['Correlation_Id'],function=function,agent=a['Agent_Id'],category=category))
                        events.append(dict(time=int(a['End_Timestamp']),order=index,address=a['Address'],bytes=int(a['Allocation_Size']),allocate=allocate,category=category))
                    details=dict(HIP_api_table_sha256=digest(api),allocation_correlations=used)
                else:
                    tables=memory['tables'];kinds={a['id']:a['label'] for a in tables['ENUM_CUDA_MEM_KIND']['rows']};operations={a['id']:a['label'] for a in tables['ENUM_CUDA_DEV_MEM_EVENT_OPER']['rows']}
                    mapping={'Device':'device_dynamic','Device Static':'device_static','Pinned':'host_pinned_API','Array':'device_array','Managed':'device_managed','Managed Static':'device_managed_static','Pageable':'host_pageable'}
                    for index,a in enumerate(tables['CUDA_GPU_MEMORY_USAGE_EVENTS']['rows']):
                        operation=operations[a['memoryOperationType']]
                        if operation not in ['Allocation','Deallocation'] or kinds[a['memKind']] not in mapping:raise ValueError('unknown CUDA allocation event')
                        events.append(dict(time=a['start'],order=index,address=(a['globalPid'],a['deviceId'],a['address']),bytes=a['bytes'],allocate=operation=='Allocation',category=mapping[kinds[a['memKind']]]))
                    details=dict(memory_kinds=kinds,operations=operations,memory_pool_events=tables.get('CUDA_GPU_MEMORY_POOL_EVENTS',{}))
                metrics=reconstruct(events);checks.append(dict(check=side+'-'+row['case']+'-complete-lifetimes',passed=metrics['peak_bytes'].get('device_dynamic',0)>0 and metrics['peak_bytes'].get('host_pinned_API',0)>0))
                checks.append(dict(check=side+'-'+row['case']+'-application-dynamic-buffers-retired',passed=metrics['retained_at_trace_end_bytes'].get('device_dynamic',0)==0 and metrics['retained_at_trace_end_bytes'].get('host_pinned_API',0)==0))
                results.append(dict(side=side,case=row['case'],events=len(events),metrics=metrics,details=details,evidence=row['evidence']));refs.append(row['evidence'])
        base=[dict(time=0,order=0,address=1,bytes=64,allocate=True,category='device_dynamic'),dict(time=1,order=1,address=1,bytes=64,allocate=False,category=None)]
        checks.append(dict(check='known-peak-positive',passed=reconstruct(base)['peak_bytes']['all_traced_device']==64))
        for name,events in [('missing-allocation',base[1:]),('duplicate-address',base[:1]*2),('wrong-free-size',[base[0],dict(base[1],bytes=65)])]:
            try:reconstruct(events);rejected=False
            except ValueError:rejected=True
            checks.append(dict(check=name+'-rejected',passed=rejected))
    except Exception as error:checks.append(dict(check='reconstruction-exception',passed=False,error=repr(error)))
    status='PASSED' if len(results)==12 and all(c['passed'] for c in checks) else 'FAILED'
    result=dict(status=status,checks=checks,cases=results,evidence_references=refs,
        coverage='Peak live bytes reconstructed from traced allocator events, not total VRAM residency/reservation. AMD host_pinned_API only events correlated with hipHostMalloc; CPU-agent runtime pools separate. CUDA static device allocations remain context-lived and are separate from retired dynamic buffers. Pool reservation, driver/profiler memory and untraced CPU malloc are not claimed covered. No peak-memory sum across categories is used unless reconstructed at the same timestamps.')
    write(e.path/'result.json',result);result['evidence']=e.finish('PASSED' if status=='PASSED' else 'PROBE_FAILED',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-memory-summary.json',result)
    record('IMG-01','两平台12组分配峰值重建：'+status+'；按地址/分配/释放重建device与pinned生命周期，静态和runtime池单列，不把trace峰值称为全部VRAM占用。',[result['evidence']]);print(status,[c for c in checks if not c['passed']]);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
