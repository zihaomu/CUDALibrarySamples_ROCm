#!/usr/bin/env python3
"""Execute frozen held-out encoding inputs; quality qualification is separate."""
import argparse,json,shlex,tarfile,shutil
from pathlib import Path
from experiment import ROOT,Experiment,digest,write
from audit import check as audit_check
from image_completion_progress import record
PROFILE=ROOT/'migration/rewrite/image-encoder-math-variant-profile.json'
HOST='nvidia-5090x2'

def arguments(c,binary,source,out):
    a=[str(binary),'-i',str(source),'-o',str(out),'-n','1','-j','1','-s','1','-b','gpu','-q',str(c['quality'])]
    return a+(['-p'] if c['sampling']==1 else [])+(['-f'] if c['optimized'] else [])

REMOTE='''import hashlib,json,os,pathlib,subprocess,sys
c=json.loads(sys.argv[1]);sha=lambda p:hashlib.file_digest(pathlib.Path(p).open('rb'),'sha256').hexdigest()
for key in ['input','original','binary']:assert sha(c[key])==c[key+'_sha256']
ldd=subprocess.check_output(['ldd',c['binary']],text=True);libs={}
for line in ldd.splitlines():
 w=line.split()
 if '=>' in w and len(w)>2 and w[2].startswith('/'):
  p=pathlib.Path(w[2]).resolve();libs[str(p)]=dict(sha256=sha(p),bytes=p.stat().st_size)
print(json.dumps(dict(config=c,libraries=libs,ldd=ldd,CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),physical_device_index=1,gpu=subprocess.check_output(['nvidia-smi','--id=1','--query-gpu=name,uuid,pci.bus_id,driver_version','--format=csv,noheader'],text=True).strip())),flush=True)
pathlib.Path(c['out']).mkdir(parents=True);rc=subprocess.run(c['args']).returncode
print(json.dumps(dict(return_code=rc,outputs={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in pathlib.Path(c['out']).iterdir()})),flush=True);sys.exit(rc)
'''

def main(side):
    p=json.loads(PROFILE.read_text());inputs={i['id']:i for i in p['inputs']}
    if len(p['cases'])!=80:raise ValueError('complete frozen matrix required')
    for i in inputs.values():
        if digest(ROOT/i['path'])!=i['sha256'] or (ROOT/i['path']).stat().st_size!=i['bytes']:raise ValueError('input drift')
    if side=='amd':
        from snapshot import capture
        bp=ROOT/'migration/reports/image-encoder-math-candidate-build.json';b=json.loads(bp.read_text())
        if b['status']!='BUILT' or digest(ROOT/b['binary'])!=b['binary_sha256'] or any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()):raise ValueError('stale AMD binary')
        deps=[bp,*[ROOT/n for n in b['dependencies']]];binary=str(ROOT/b['binary']);binary_sha=b['binary_sha256']
    else:
        bp=ROOT/'migration/reports/image-completion-encoder-native.json';b=json.loads(bp.read_text());original=ROOT/b['source']
        proof=ROOT/b['cases'][0]['evidence'];cmds=json.loads((proof/'commands.json').read_text());log=proof/cmds[0]['stdout']
        receipt=json.loads(log.read_text().splitlines()[0]);binary_sha=receipt['binary_sha256'];binary=b['remote']+'/build/nvJPEGEncMultipleInstances'
        if audit_check(proof) or digest(original)!=b['source_sha256'] or digest(original.parent/'CMakeLists.txt')!=b['cmake_sha256'] or json.loads((proof/'result.json').read_text())!={k:v for k,v in b['cases'][0].items() if k!='evidence'}:raise ValueError('native source/evidence drift')
        deps=[bp,original,original.parent/'CMakeLists.txt',proof/'source.json',proof/'result.json',log]
        e=Experiment('I5','encoder-math-native-inputs','cuda-prepare',sources=[__file__,PROFILE,*deps,*[ROOT/i['path'] for i in inputs.values()]])
        root='/tmp/image-quality-'+e.id;bundle=e.path/'inputs.tar'
        with tarfile.open(bundle,'w') as tar:
            for i in inputs.values():tar.add(ROOT/i['path'],arcname=i['id']+'/image.bmp')
        rc=e.command(['ssh',HOST,shlex.join(['mkdir','-p',root])],'prepare-native-inputs')
        rc=rc or e.command(['scp',str(bundle),HOST+':'+root+'/inputs.tar'],'upload-frozen-BMPs')
        rc=rc or e.command(['ssh',HOST,shlex.join(['tar','xf',root+'/inputs.tar','-C',root])],'extract-frozen-BMPs')
        prep=dict(status='PASSED' if rc==0 else 'FAILED',checks=[dict(check='prepare-native-inputs',passed=rc==0)],remote=root)
        write(e.path/'result.json',prep);prep['evidence']=e.finish('PASSED' if rc==0 else 'COMMAND_FAILED',dict(status=prep['status'],checks=prep['checks']))
        if rc:return 1
    rows=[]
    for c in p['cases']:
        i=inputs[c['input']];e=Experiment('I5','encoder-math-quality-original-entry',side+'-original',case=c['id'],sources=[__file__,PROFILE,ROOT/'tools/moat/image_encoder_math_contract.py',ROOT/i['path'],*deps])
        out=e.path/'products';checks=[];products=[]
        if side=='amd':
            write(e.path/'backend.observed.json',capture());out.mkdir();indir=e.path/'inputs';indir.mkdir();shutil.copyfile(ROOT/i['path'],indir/'image.bmp')
            checks.append(dict(check='staged-input-SHA',passed=digest(indir/'image.bmp')==i['sha256']))
            rc=e.command(arguments(c,binary,indir,out),'AMD-original-entry',timeout=300)
            checks.append(dict(check='actual-original-entry-command',passed=rc==0));identity=dict(binary_sha256=binary_sha,build_report_sha256=digest(bp))
        else:
            source=root+'/'+i['id']+'/image.bmp';dest=root+'/outputs/'+c['id']
            config=dict(input=source,input_sha256=i['sha256'],original=b['remote']+'/source/'+original.name,original_sha256=b['source_sha256'],binary=binary,binary_sha256=binary_sha,out=dest,args=arguments(c,binary,str(Path(source).parent),dest))
            rc=e.command(['ssh',HOST,shlex.join(['env','CUDA_VISIBLE_DEVICES=1','python3','-c',REMOTE,json.dumps(config,separators=(',',':'))])],'native-GPU1-identity-and-entry',timeout=300)
            cr=e.command(['scp','-r',HOST+':'+dest,str(out)],'collect-native-products',timeout=120)
            checks.append(dict(check='native-command-and-collection',passed=rc==cr==0));identity=dict(binary_sha256=binary_sha,prepare_evidence=prep['evidence'],native_build_evidence=b['build_evidence'])
        try:
            products=[dict(name=x.name,path=str(x.relative_to(ROOT)),sha256=digest(x),bytes=x.stat().st_size) for x in sorted(out.iterdir()) if x.is_file()]
            checks.append(dict(check='exact-one-complete-JPEG',passed={x.name for x in out.iterdir()}=={'0.jpg'} and len(products)==1 and products[0]['bytes']>0))
            if side=='native':
                log=(e.path/e.commands[0]['stdout']).read_text().splitlines();actual=json.loads(log[0]);result=json.loads(log[-1])
                checks.append(dict(check='actual-native-GPU1-source-binary-input-receipt',passed=actual['CUDA_VISIBLE_DEVICES']=='1' and actual['physical_device_index']==1 and '5090' in actual['gpu'] and actual['config']==config))
                checks.append(dict(check='local-products-match-remote-receipt',passed={x['name']:dict(sha256=x['sha256'],bytes=x['bytes']) for x in products}==result['outputs'] and result['return_code']==0))
        except Exception as error:checks.append(dict(check='validation-exception',passed=False,error=repr(error)))
        status='PASSED' if all(x['passed'] for x in checks) else 'FAILED';row=dict(case=c['id'],status=status,checks=checks,experiment_id=e.id,products=products,input=i,**identity)
        write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks));rows.append(row);write(ROOT/f'migration/reports/image-encoder-math-{side}.json',rows)
        record('IMG-01',side+'编码质量矩阵运行 '+c['id']+'：'+status+'；仅运行/文件身份检查，三方数值验收另行执行。',[row['evidence']]);print(side,c['id'],status,flush=True)
        if status!='PASSED':return 1
    return int(any(r['status']!='PASSED' for r in rows))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('side',choices=['amd','native']);a=parser.parse_args();raise SystemExit(main(a.side))
