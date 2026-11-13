#!/usr/bin/env python3
"""Trace actual multi-threaded entrypoint and replay changed source images."""
import csv,json,re,shutil
from experiment import ROOT,Experiment,digest,write
from snapshot import capture
from image_completion_progress import record

def main():
    p=json.loads((ROOT/'migration/rewrite/image-encoder-instances-v2-profile.json').read_text())
    b=json.loads((ROOT/'migration/reports/image-encoder-instances-v2-build.json').read_text())
    runs=json.loads((ROOT/'migration/reports/image-encoder-instances-v2-runs.json').read_text())
    if b['status']!='BUILT' or digest(ROOT/b['binary'])!=b['binary_sha256'] or any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()):raise ValueError('stale actual-entry build')
    prior=json.loads((ROOT/'migration/reports/image-encoder-pipeline-trace.json').read_text())[0]
    deps=json.loads((ROOT/prior['evidence']/'source.json').read_text())['dependencies']
    audit_name=next(n for n in deps if n.endswith('/copy_audit.so'));audit=ROOT/audit_name
    if digest(audit)!=deps[audit_name]:raise ValueError('copy observer drift')
    results=[];input_dir=(ROOT/p['inputs'][0]['path']).parent
    for name,count,opt,download in [('repeat-seven',7,False,True),('optimized-444',3,True,True),('device-only',3,False,False)]:
        run=next(r for r in runs if r['case']==name)
        e=Experiment('I5','async-original-entry-multithread-trace','rocm-trace',case=name,sources=[__file__,audit,ROOT/'migration/reports/image-encoder-instances-v2-runs.json',*[ROOT/n for n in b['dependencies']]],parent=run['experiment_id'])
        observed=capture();write(e.path/'backend.observed.json',observed);out=e.path/'outputs';out.mkdir()
        args=[str(ROOT/b['binary']),'-i',str(input_dir),'-j','2','-s','4' if count==7 else '2','-n',str(count),'-b','gpu','-q','90' if opt else '75' if count==7 else '80']
        if opt:args+=['-f','-p']
        if download:args+=['-o',str(out)]
        rc=e.command(['rocprofv3','--kernel-trace','--hip-trace','--output-format','csv','--output-directory',str(e.path/'trace'),'--','env','LD_PRELOAD='+str(audit),*args],'actual-original-entry-trace',timeout=300)
        checks=[dict(check='profile-command',passed=rc==0)];info={}
        try:
            traces=list((e.path/'trace').rglob('*kernel_trace.csv'));agents=list((e.path/'trace').rglob('*agent_info.csv'))
            if len(traces)!=1 or len(agents)!=1:raise ValueError('one trace and agent table required')
            rows=list(csv.DictReader(traces[0].open()));lookup={r['Node_Id']:r for r in csv.DictReader(agents[0].open())}
            app=[r for r in rows if not r['Kernel_Name'].startswith('__amd_rocclr_')]
            streams={r['Stream_Id'] for r in app};expected=count*(17 if opt else 16)
            checks.append(dict(check='all-image-algorithm-kernels-and-multiple-streams',passed=len(app)==expected and len(streams)>=2,actual=len(app),expected=expected,streams=sorted(streams)))
            allowed={d['pci_bdf'] for d in observed['devices'] if d['physical_id']==1};actual_pci=set();real=True
            for row in rows:
                agent=lookup[row['Agent_Id'].split()[-1]];loc=int(agent['Location_Id']);address=f"{int(agent['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}"
                actual_pci.add(address);real &= address in allowed and int(row['End_Timestamp'])>int(row['Start_Timestamp']) and int(row['Grid_Size_X'])>0
            checks.append(dict(check='all-actual-kernels-on-allowed-GPU1',passed=bool(rows) and real,pci=sorted(actual_pci)))
            checks.append(dict(check='exact-traced-product-set',passed={x.name for x in out.iterdir()}=={x['name'] for x in run['products']}))
            for product in run['products']:checks.append(dict(check='traced-JPEG-exact-'+product['name'],passed=digest(out/product['name'])==product['sha256']))
            log=(e.path/'logs/0001-actual-original-entry-trace.stderr.log').read_text()
            copies=[dict(kind=int(k),bytes=int(n),stream=s,rc=int(rc)) for k,n,s,rc in re.findall(r'JPEG_COPY_AUDIT kind=(\d+) bytes=(\d+) stream=(\S+) rc=(\d+)',log)]
            if not download:checks.append(dict(check='entry-device-only-downloads-metadata-only',passed=bool(copies) and [r['bytes'] for r in copies if r['kind']==2]==[8]*(count*2) and all(r['rc']==0 for r in copies)))
            info=dict(kernel_count=len(app),runtime_kernel_count=len(rows)-len(app),stream_ids=sorted(streams),copies=copies)
            if name=='repeat-seven':
                changed=e.path/'changed-input';shutil.copytree(input_dir,changed);path=changed/(ROOT/p['inputs'][0]['path']).name
                data=bytearray(path.read_bytes());offset=int.from_bytes(data[10:14],'little');data[offset:]=bytes(255-v for v in data[offset:]);path.write_bytes(data)
                replay=e.path/'changed-output';replay.mkdir();changed_args=args.copy();changed_args[changed_args.index('-i')+1]=str(changed);changed_args[changed_args.index('-o')+1]=str(replay)
                replay_rc=e.command(changed_args,'changed-first-BMP-seven-job-replay')
                checks.append(dict(check='changed-input-command-and-output-set',passed=replay_rc==0 and {x.name for x in replay.iterdir()}=={str(i)+'.jpg' for i in range(7)}))
                for i in range(7):
                    different=digest(out/(str(i)+'.jpg'))!=digest(replay/(str(i)+'.jpg'))
                    checks.append(dict(check='only-corresponding-input-jobs-change-'+str(i),passed=different==(i%3==0)))
                info['changed_input_sha256']=digest(path)
        except Exception as error:checks.append(dict(check='trace-validation-exception',passed=False,error=repr(error)))
        status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';result=dict(case=name,status=status,checks=checks,observed=info,experiment_id=e.id)
        write(e.path/'result.json',result);result['evidence']=e.finish('PASSED' if status=='PASSED' else 'PROFILER_FAILED',dict(status=status,checks=checks));results.append(result)
        write(ROOT/'migration/reports/image-encoder-instances-v2-trace.json',results)
        record('IMG-01','正式入口trace '+name+'：'+status+'；多线程实际kernel/stream、设备模式和首图变化重放逐项记录。',[result['evidence']]);print(name,status,flush=True)
    return int(any(r['status']!='PASSED' for r in results))

if __name__=='__main__':raise SystemExit(main())
