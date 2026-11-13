#!/usr/bin/env python3
"""Unprofiled original-entry wall-time distributions on AMD and native CUDA."""
import argparse,hashlib,json,math,shlex,shutil,statistics,sys,tarfile
from pathlib import Path
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_encoder_math_binding import sealed

PROFILE=ROOT/'migration/rewrite/image-encoder-performance-profile.json'
HOST='nvidia-5090x2'
TARGET_RUN='''import os,subprocess,tempfile,time
def target_run(args):
    # File-backed capture avoids pipe deadlocks while wait4 reaps this PID only.
    with tempfile.TemporaryFile(mode='w+b') as out, tempfile.TemporaryFile(mode='w+b') as err:
        start=time.perf_counter_ns()
        p=subprocess.Popen(args,stdout=out,stderr=err)
        pid,status,usage=os.wait4(p.pid,0)
        elapsed=(time.perf_counter_ns()-start)/1e6
        assert pid==p.pid
        p.returncode=os.waitstatus_to_exitcode(status)
        out.seek(0);err.seek(0)
        return dict(return_code=p.returncode,process_elapsed_ms=elapsed,encoder_process_max_RSS_KiB=usage.ru_maxrss),out.read().decode(),err.read().decode()
'''
TIMED_RUN=TARGET_RUN+'''import hashlib,json,pathlib,sys
c=json.loads(sys.argv[1]);sha=lambda p:hashlib.file_digest(pathlib.Path(p).open('rb'),'sha256').hexdigest()
for p,h in c['identities'].items():assert sha(p)==h,(p,'identity drift')
ldd=subprocess.check_output(['ldd',c['args'][0]],text=True);libs={}
for line in ldd.splitlines():
 w=line.split()
 if '=>' in w and len(w)>2 and w[2].startswith('/'):
  p=pathlib.Path(w[2]).resolve();libs[str(p)]=sha(p)
identity=dict(config=c,libraries=libs,ldd=ldd,CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),HIP_VISIBLE_DEVICES=os.environ.get('HIP_VISIBLE_DEVICES'))
if c['side']=='native':identity['gpu']=subprocess.check_output(['nvidia-smi','--id=1','--query-gpu=name,uuid,pci.bus_id,driver_version','--format=csv,noheader'],text=True).strip()
if c['output']:pathlib.Path(c['output']).mkdir(parents=True)
print('TIMED_IDENTITY '+json.dumps(identity),flush=True)
result,out,err=target_run(c['args'])
sys.stdout.write(out);sys.stderr.write(err)
products={x.name:dict(sha256=sha(x),bytes=x.stat().st_size) for x in pathlib.Path(c['output']).iterdir()} if c['output'] else {}
print('TIMED_RESULT '+json.dumps(dict(**result,products=products)),flush=True)
sys.exit(result['return_code'])
'''

def inputs(profile):
    from image_encoder_large import fixture
    folder=ROOT/'build/image-encoder-performance-inputs';values={}
    for name,item in profile['inputs'].items():
        directory=folder/name;directory.mkdir(parents=True,exist_ok=True);dest=directory/'image.bmp'
        if name=='large':
            rgb,bmp=fixture(item['case']);identity=item['case']['bmp_sha256']
            if hashlib.sha256(rgb.tobytes()).hexdigest()!=item['case']['sha256'] or hashlib.sha256(bmp).hexdigest()!=identity:raise ValueError('large generator drift')
            dest.write_bytes(bmp)
        else:
            identity=item['sha256'];source=ROOT/item['path']
            if digest(source)!=identity:raise ValueError('frozen BMP drift')
            shutil.copyfile(source,dest)
        values[name]=dict(path=str(dest.relative_to(ROOT)),sha256=identity)
    return values

def arguments(case,binary,source,output):
    args=[str(binary),'-i',str(source),'-n',str(case['jobs']),'-j',str(case['threads']),'-s',str(case['states']),'-r','1','-b','gpu','-q',str(case['quality'])]
    if case['sampling']==1:args+=['-p']
    if case['optimized']:args+=['-f']
    if case['mode']=='download':args+=['-d']
    if case['mode']=='write':args+=['-o',str(output)]
    return args

def main(side):
    p=json.loads(PROFILE.read_text());fixtures=inputs(p)
    deps=[PROFILE,ROOT/'tools/moat/image_encoder_large.py',ROOT/'migration/rewrite/image-encoder-large-profile.json',ROOT/'tools/moat/image_encoder_math_binding.py']
    if side=='amd':
        from snapshot import capture
        bp=ROOT/'migration/reports/image-encoder-instances-v2-build.json';b=json.loads(bp.read_text());sealed(b,'build.json')
        if b['status']!='BUILT' or any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()) or digest(ROOT/b['binary'])!=b['binary_sha256']:raise ValueError('current production binary required')
        binary=str(ROOT/b['binary']);binary_sha=b['binary_sha256'];deps += [bp,*[ROOT/n for n in b['dependencies']]];root=None;extra_identity={}
    else:
        bp=ROOT/'migration/reports/image-completion-encoder-native.json';b=json.loads(bp.read_text());original=ROOT/b['source'];sealed(b['cases'][0])
        proof=ROOT/b['cases'][0]['evidence'];commands=json.loads((proof/'commands.json').read_text());receipt=json.loads((proof/commands[0]['stdout']).read_text().splitlines()[0])
        binary=b['remote']+'/build/nvJPEGEncMultipleInstances';binary_sha=receipt['binary_sha256'];extra_identity={b['remote']+'/source/'+original.name:b['source_sha256']}
        if digest(original)!=b['source_sha256']:raise ValueError('native original source drift')
        deps += [bp,original,original.parent/'CMakeLists.txt',proof/'source.json',proof/'result.json',proof/commands[0]['stdout']]
        e=Experiment('I5','encoder-performance-native-inputs','cuda-prepare',sources=[__file__,*deps]);bundle=e.path/'inputs.tar';root='/tmp/image-perf-'+e.id
        with tarfile.open(bundle,'w') as tar:
            for name,item in fixtures.items():tar.add(ROOT/item['path'],arcname=name+'/image.bmp')
        rc=e.command(['ssh',HOST,shlex.join(['mkdir','-p',root])],'create-native-input-directory')
        rc=rc or e.command(['scp',str(bundle),HOST+':'+root+'/inputs.tar'],'copy-identical-BMPs')
        rc=rc or e.command(['ssh',HOST,shlex.join(['tar','xf',root+'/inputs.tar','-C',root])],'extract-native-inputs')
        check=dict(check='identical-input-staging',passed=rc==0);prep=dict(status='PASSED' if rc==0 else 'FAILED',checks=[check],inputs=fixtures,remote=root)
        write(e.path/'result.json',prep);prep['evidence']=e.finish('PASSED' if rc==0 else 'COMMAND_FAILED',dict(status=prep['status'],checks=[check]))
        if rc:return 1
    rows=[]
    for case in p['cases']:
        e=Experiment('I5','encoder-unprofiled-end-to-end','amd-original' if side=='amd' else 'cuda-original',case=case['id'],sources=[__file__,*deps])
        if side=='amd':write(e.path/'backend.observed.json',capture())
        item=fixtures[case['input']];local=ROOT/item['path'];source=str(local) if side=='amd' else root+'/'+case['input']+'/image.bmp'
        checks=[];repetitions=[]
        write(e.path/'inputs/manifest.json',dict(contract=case,input=item,regenerate='tools/moat/image_encoder_performance.py inputs() with frozen performance profile; large source uses pinned seed/shape/SHA'))
        try:
            for repetition in range(p['warmups']+p['repetitions']):
                output=(str(e.path/'products'/str(repetition)) if side=='amd' else root+'/outputs/'+e.id+'/'+str(repetition)) if case['mode']=='write' else None
                args=arguments(case,binary,str(Path(source).parent),output)
                config=dict(side=side,args=args,output=output,identities={binary:binary_sha,source:item['sha256'],**extra_identity})
                cmd=[sys.executable,'-c',TIMED_RUN,json.dumps(config,separators=(',',':'))] if side=='amd' else ['ssh',HOST,shlex.join(['env','CUDA_VISIBLE_DEVICES=1','python3','-c',TIMED_RUN,json.dumps(config,separators=(',',':'))])]
                rc=e.command(cmd,'unprofiled-'+str(repetition),timeout=600)
                log=(e.path/e.commands[-1]['stdout']).read_text();lines=log.splitlines()
                identity=json.loads(next(x.removeprefix('TIMED_IDENTITY ') for x in lines if x.startswith('TIMED_IDENTITY ')))
                result=json.loads(next(x.removeprefix('TIMED_RESULT ') for x in lines if x.startswith('TIMED_RESULT ')))
                expected={str(i)+'.jpg' for i in range(case['jobs'])} if case['mode']=='write' else set()
                valid=rc==result['return_code']==0 and identity['config']==config and math.isfinite(result['process_elapsed_ms']) and result['process_elapsed_ms']>0 and set(result['products'])==expected and all(x['bytes']>4 for x in result['products'].values())
                if side=='native':valid &= identity['CUDA_VISIBLE_DEVICES']=='1' and '5090' in identity['gpu']
                else:valid &= identity['HIP_VISIBLE_DEVICES']=='0' and f"RESULT status=PASS encoded={case['jobs']} " in log
                checks.append(dict(check='repetition-'+str(repetition),passed=bool(valid)))
                repetitions.append(dict(index=repetition,warmup=repetition<p['warmups'],**result,internal_stdout=[x for x in lines if x.startswith(('Throughput:','Latency:','TIMING ','RESULT ','Percentage:'))]))
                if not valid:break
            values=[r['process_elapsed_ms'] for r in repetitions if not r['warmup']];ordered=sorted(values)
            if len(values)!=7:raise ValueError('all seven unprofiled repetitions required')
            stats=dict(min_ms=min(values),median_ms=statistics.median(values),max_ms=max(values),p95_ms=ordered[math.ceil(.95*len(ordered))-1],MAD_ms=statistics.median(abs(x-statistics.median(values)) for x in values),median_process_images_per_second=case['jobs']*1000/statistics.median(values))
        except Exception as error:checks.append(dict(check='measurement-exception',passed=False,error=repr(error)));stats={}
        status='PASSED' if len(repetitions)==9 and checks and all(c['passed'] for c in checks) else 'FAILED'
        row=dict(case=case['id'],side=side,status=status,checks=checks,repetitions=repetitions,statistics=stats,binary_sha256=binary_sha,scope='Unprofiled process wall time and encoder PID max RSS from wait4; preparation child processes excluded. GPU/pinned peak allocations require separate profiler experiment; no latency equivalence or speedup claim.')
        write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'COMMAND_FAILED',dict(status=status,checks=checks));rows.append(row);write(ROOT/f'migration/reports/image-encoder-performance-v2-{side}.json',rows)
        record('IMG-01',side+'无profiler性能 '+case['id']+'：'+status+'；2次预热+7次进程墙钟，GPU内部延迟另列，不与端到端混用。',[row['evidence']]);print(side,case['id'],status,stats,flush=True)
        if status!='PASSED':return 1
    return 0

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('side',choices=['amd','native']);args=parser.parse_args();raise SystemExit(main(args.side))
