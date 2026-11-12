#!/usr/bin/env python3
"""Trace tiled prefix kernels and check mutation and malformed lengths."""
import csv,json,re,struct
from experiment import ROOT,Experiment,digest,write
from image_progress import record
from snapshot import capture
from image_jpeg_prefix_run import source,oracle,packed

PROFILE=ROOT/'migration/rewrite/image-jpeg-prefix-profile.json'
BUILD=ROOT/'migration/reports/image-jpeg-prefix-build.json'
RUNS=ROOT/'migration/reports/image-jpeg-prefix-runs.json'
REPORT=ROOT/'migration/reports/image-jpeg-prefix-trace.json'

def output(path,count):
    return list(struct.unpack('<'+str(count)+'I',path.read_bytes())) if path.is_file() and path.stat().st_size==count*4 else []

def main():
    profile=json.loads(PROFILE.read_text());build=json.loads(BUILD.read_text());runs=json.loads(RUNS.read_text())
    if profile['status']!='FROZEN' or build['status']!='BUILT' or len(runs)!=12 or any(x['status']!='PASSED' for x in runs):
        raise ValueError('current prefix build and twelve exact runs required')
    row=next(x for x in profile['cases'] if x['mode']=='bits' and x['count']==257)
    vals=source(row);expected,total=oracle('bits',vals)
    e=Experiment('I5','parallel-JPEG-prefix-real-GPU-trace-mutation-and-rejection','rocm-trace',
                 sources=[__file__,PROFILE,BUILD,RUNS,ROOT/'rocm/common/image/jpeg_parallel_prefix.hpp',
                          ROOT/'rocm/probes/image/jpeg_parallel_prefix.hip'],parent=build['experiment_id'])
    observed=capture();write(e.path/'backend.observed.json',observed)
    inp=e.path/'bits.bin';inp.write_bytes(packed('bits',vals));out=e.path/'bits-out.bin'
    cmd=['rocprofv3','--kernel-trace','--output-format','csv','--output-directory',str(e.path/'trace'),
         '--',str(ROOT/build['binary']),'bits',str(inp),str(out)]
    rc=e.command(cmd,'trace-bits-257',timeout=300)
    checks=[dict(check='trace-run-exact-Python-output',passed=rc==0 and output(out,257)==expected)]
    traces=list((e.path/'trace').rglob('*kernel_trace.csv'))
    agents=list((e.path/'trace').rglob('*agent_info.csv'))
    checks.append(dict(check='single-trace-and-agent-map',passed=len(traces)==len(agents)==1))
    counts={};pci=set()
    if len(traces)==len(agents)==1:
        lookup={r['Node_Id']:r for r in csv.DictReader(agents[0].open())}
        allowed={d['pci_bdf'] for d in observed['devices'] if d['physical_id']==1}
        for item in csv.DictReader(traces[0].open()):
            stage=next((n for n in ('scan_tile','scan_sums','add_bases') if n in item['Kernel_Name']),None)
            if not stage:continue
            counts[stage]=counts.get(stage,0)+1
            agent=lookup[item['Agent_Id'].split()[-1]];loc=int(agent['Location_Id'])
            address=f"{int(agent['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}"
            pci.add(address)
            checks.append(dict(check=stage+'-physical-GPU1',passed=address in allowed and
                 int(item['End_Timestamp'])>int(item['Start_Timestamp']) and int(item['Grid_Size_X'])>0,
                 pci_bdf=address))
    checks.append(dict(check='all-three-real-parallel-prefix-kernels',passed=counts==
                       {'scan_tile':1,'scan_sums':1,'add_bases':1},counts=counts))
    changed=list(vals);changed[128]=min(4096,changed[128]+1)
    changed_expected,changed_total=oracle('bits',changed)
    altered=e.path/'changed.bin';altered.write_bytes(packed('bits',changed))
    changed_out=e.path/'changed-out.bin'
    mutation_rc=e.command([str(ROOT/build['binary']),'bits',str(altered),str(changed_out)],'changed-bit-length',timeout=300)
    got=output(changed_out,257)
    checks.append(dict(check='changed-input-exact-and-nonempty-effect',passed=mutation_rc==0 and
                       got==changed_expected and changed_expected!=expected and got[:129]==expected[:129] and
                       changed_total==total+1))
    status='PASSED' if all(x['passed'] for x in checks) else 'PROFILER_FAILED'
    result=dict(status=status,checks=checks,kernel_counts=counts,pci_bdfs=sorted(pci),
                baseline_sha256=digest(out) if out.exists() else None,
                mutation_sha256=digest(changed_out) if changed_out.exists() else None,
                experiment_id=e.id)
    write(e.path/'trace-result.json',result)
    result['evidence']=e.finish(status,dict(status=status,checks=checks))
    negative=Experiment('I5','parallel-JPEG-prefix-oversized-block-negative','rocm-GPU-negative',
                        sources=[__file__,PROFILE,BUILD,ROOT/'rocm/probes/image/jpeg_parallel_prefix.hip'],
                        parent=e.id)
    write(negative.path/'backend.observed.json',capture())
    invalid=negative.path/'invalid.bin';invalid.write_bytes(struct.pack('<2H',1,4097))
    invalid_out=negative.path/'invalid-out.bin'
    invalid_rc=negative.command([str(ROOT/build['binary']),'bits',str(invalid),str(invalid_out)],
                                'reject-oversized-JPEG-block',timeout=300)
    stderr=(negative.path/'logs/0001-reject-oversized-JPEG-block.stderr.log').read_text()
    negative_check=dict(check='oversized-block-rejected-without-product',passed=invalid_rc!=0 and
                        not invalid_out.exists() and 'exceeds MAX_BITS' in stderr)
    result['negative_return_code']=invalid_rc
    result['negative_check']=negative_check
    result['negative_evidence']=negative.finish('EXPECTED_REJECTION' if negative_check['passed'] else 'NUMERIC_MISMATCH',
                                                 dict(status='PASSED' if negative_check['passed'] else 'FAILED',
                                                      checks=[negative_check]))
    if not negative_check['passed']:result['status']='FAILED'
    write(REPORT,result)
    record('I5','并行 JPEG prefix 三实际GPU kernel、物理GPU1、变输入重放：'+status+'；超长block无产物拒绝：'+
           ('PASSED' if negative_check['passed'] else 'FAILED')+'；仍为隔离原型。',
           [result['evidence'],result['negative_evidence']])
    print(status,counts,sorted(pci))
    return int(result['status']!='PASSED')

if __name__=='__main__':raise SystemExit(main())
