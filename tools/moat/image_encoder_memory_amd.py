#!/usr/bin/env python3
"""Collect ROCm allocation events separately from unprofiled wall times."""
import csv,json
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_encoder_math_binding import sealed

def main():
    from snapshot import capture
    profile=ROOT/'migration/rewrite/image-encoder-performance-profile.json';p=json.loads(profile.read_text())
    report=ROOT/'migration/reports/image-encoder-performance-amd.json';timings=json.loads(report.read_text())
    bp=ROOT/'migration/reports/image-encoder-instances-v2-build.json';build=json.loads(bp.read_text());sealed(build,'build.json')
    if [r['case'] for r in timings]!=[c['id'] for c in p['cases']] or any(digest(ROOT/n)!=h for n,h in build['dependencies'].items()):raise ValueError('current complete timing/build required')
    rows=[]
    for case,timing in zip(p['cases'],timings):
        proof=sealed(timing);commands=json.loads((proof/'commands.json').read_text());log=(proof/commands[0]['stdout']).read_text().splitlines()
        identity=json.loads(next(x.removeprefix('TIMED_IDENTITY ') for x in log if x.startswith('TIMED_IDENTITY ')));config=identity['config'];args=list(config['args'])
        if args[0]!=str(ROOT/build['binary']) or timing['binary_sha256']!=build['binary_sha256'] or any(digest(path)!=sha for path,sha in config['identities'].items()):raise ValueError('actual profiled input/binary identity drift')
        e=Experiment('I5','encoder-AMD-peak-allocation-trace','rocm-profiler',case=case['id'],sources=[__file__,profile,report,bp,proof/'result.json',proof/'commands.json',proof/commands[0]['stdout'],*[ROOT/n for n in build['dependencies']]])
        observed=capture();write(e.path/'backend.observed.json',observed)
        if '-o' in args:
            output=e.path/'products';output.mkdir();args[args.index('-o')+1]=str(output)
        rc=e.command(['rocprofv3','--hip-trace','--kernel-trace','--memory-copy-trace','--memory-allocation-trace','--output-format','csv','--output-directory',str(e.path/'trace'),'--',*args],'original-entry-allocation-profile',timeout=600)
        checks=[dict(check='actual-ROCm-profile',passed=rc==0)];inventory={}
        try:
            tables={}
            for path in sorted((e.path/'trace').rglob('*.csv')):
                entries=list(csv.DictReader(path.open()));name=path.name.split('_',1)[-1]
                tables[path.name]=dict(path=str(path.relative_to(ROOT)),sha256=digest(path),bytes=path.stat().st_size,columns=list(entries[0]) if entries else [],rows=entries)
                inventory[path.name]=dict(rows=len(entries),columns=tables[path.name]['columns'])
            allocations=[v for k,v in tables.items() if 'memory_allocation' in k]
            checks.append(dict(check='allocation-events-present',passed=len(allocations)==1 and bool(allocations[0]['rows'])))
            agents=[v for k,v in tables.items() if 'agent_info' in k];kernels=[v for k,v in tables.items() if 'kernel_trace' in k]
            if len(agents)!=1 or len(kernels)!=1:raise ValueError('unique kernel/agent tables required')
            lookup={r['Node_Id']:r for r in agents[0]['rows']};allowed={d['pci_bdf'] for d in observed['devices'] if d['physical_id']==1}
            valid=bool(kernels[0]['rows'])
            for event in kernels[0]['rows']:
                agent=lookup[event['Agent_Id'].split()[-1]];loc=int(agent['Location_Id']);address=f"{int(agent['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}"
                valid &= address in allowed and int(event['End_Timestamp'])>int(event['Start_Timestamp'])
            checks.append(dict(check='actual-kernels-on-physical-GPU1',passed=bool(valid)))
            # Keep all allocation events and agent metadata in a small portable
            # JSON even when the full kernel trace exceeds the archive size cap.
            memory={k:v for k,v in tables.items() if 'memory_allocation' in k or 'agent_info' in k}
            write(e.path/'memory.json',memory)
        except Exception as error:checks.append(dict(check='allocation-profile-exception',passed=False,error=repr(error)))
        status='OBSERVED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(case=case['id'],status=status,checks=checks,tables=inventory,binary_sha256=build['binary_sha256'],evidence_references=[timing['evidence'],build['evidence']],scope='Allocation events and actual device identity; peak reconstruction separate, no profiled throughput used.')
        write(e.path/'result.json',row);row['evidence']=e.finish('OBSERVED' if status=='OBSERVED' else 'PROBE_FAILED',dict(status=status,checks=checks));rows.append(row);write(ROOT/'migration/reports/image-encoder-memory-amd.json',rows)
        record('IMG-01','AMD独立分配trace '+case['id']+'：'+status+'；实际GPU1、完整分配事件及kernel/拷贝原始表，峰值另行重建。',[row['evidence']]);print(case['id'],status,inventory,flush=True)
        if status!='OBSERVED':return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
