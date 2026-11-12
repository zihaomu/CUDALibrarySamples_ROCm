#!/usr/bin/env python3
"""Mutation checks for Hough qualification and copied cold child archives."""
import copy,json,shutil,tempfile
from pathlib import Path
from unittest.mock import patch
from experiment import ROOT,Experiment,write,digest
from image_progress import record
import qualify_image_hough as q

NAMES=['real-45-child-cold-archive','actual-14-CPU-reference-gate',
       'duplicate-original-CLI','forged-PPM-SHA','forged-line-CSV-SHA',
       'forged-CPU-result','forged-nondefault-parameter-result',
       'forged-runtime-result','missing-GPU-vote-dispatch',
       'forged-native-pixel-difference','altered-cold-child-file',
       'coupled-cold-PPM-report-and-seal-forgery',
       'coupled-cold-runtime-failed-report-and-seal',
       'coupled-cold-runtime-validation-failed-report-and-seal',
       'coupled-cold-foreign-stream-failed-report-and-seal',
       'coupled-cold-trace-failed-report-and-seal',
       'coupled-cold-contract-failed-report-and-seal',
       'coupled-cold-build-failed-manifest-and-seal',
       'coupled-cold-foreign-wrong-backend-and-seal',
       'coupled-cold-trace-wrong-parent-and-seal',
       'cold-outer-checkout-command-forgery',
       'current-CPU-validation-wrong-parent-identity',
       'current-original-CLI-wrong-output-cwd']

def run_checks():
    checks=[];original=q.load
    def check(name,fn,wanted=True):
        try:ok=bool(fn())
        except (OSError,ValueError,KeyError,TypeError,IndexError,StopIteration):ok=False
        checks.append(dict(check=name,passed=ok==wanted))
    cold=original('cold')
    check(NAMES[0],lambda:q.cold_verify(cold))
    check(NAMES[1],lambda:next(c for c in q.collect(None)[0] if c['check']=='fourteen-complete-line-list-CSV-PPM-independent-CPU-recomputations')['passed'])
    def mutation(name,edit,gate):
        def changed(which):
            value=original(which)
            if which==name:value=copy.deepcopy(value);edit(value)
            return value
        with patch.object(q,'load',changed):
            return next(c for c in q.collect(None)[0] if c['check']==gate)['passed']
    check(NAMES[2],lambda:mutation('runs',lambda rows:rows.__setitem__(1,copy.deepcopy(rows[0])),
                                   'fourteen-actual-complete-original-CLI-and-products'),False)
    check(NAMES[3],lambda:mutation('runs',lambda rows:rows[0].update(ppm_sha256='0'*64),
                                   'fourteen-actual-complete-original-CLI-and-products'),False)
    check(NAMES[4],lambda:mutation('runs',lambda rows:rows[0].update(lines_sha256='0'*64),
                                   'fourteen-actual-complete-original-CLI-and-products'),False)
    check(NAMES[5],lambda:mutation('validation',lambda rows:rows[0].update(status='FAILED'),
                                   'fourteen-complete-line-list-CSV-PPM-independent-CPU-recomputations'),False)
    check(NAMES[6],lambda:mutation('options',lambda rows:rows[0]['validation'].update(status='FAILED'),
                                   'five-valid-nondefault-parameter-and-1196-peak-complete-products'),False)
    check(NAMES[7],lambda:mutation('runtime',lambda row:row.update(status='FAILED'),
                                   'nineteen-real-device-runtime-and-all-peaks-independent-CPU'),False)
    check(NAMES[8],lambda:mutation('trace',lambda row:row['counts'].update(cast_votes=0),
                                   'five-actual-Canny-and-Hough-GPU-dispatches-on-physical-one'),False)
    check(NAMES[9],lambda:mutation('native-comparison',lambda row:row.update(differing_RGB_pixels=0),
                                   'unmodified-native-5090-complete-PPM-and-declared-variant'),False)
    parent=ROOT/json.loads((ROOT/cold['evidence']/'manifest.json').read_text())['raw_artifact_dir']
    target=parent/'child-evidence/contracts/0/profile.json';real_digest=q.digest
    def wrong(path):return '0'*64 if Path(path)==target else real_digest(path)
    with patch.object(q,'digest',wrong):check(NAMES[10],lambda:q.cold_verify(cold),False)
    with tempfile.TemporaryDirectory(prefix='hough-cold-coupled-') as temporary:
        root=Path(temporary)
        changed=copy.deepcopy(cold)
        for child in changed['children']:
            source=parent/child['relative'];dest=root/child['relative'];dest.parent.mkdir(parents=True,exist_ok=True)
            if child['name']=='runs' and child['index']==1:shutil.copytree(source,dest)
            else:dest.symlink_to(source,target_is_directory=True)
        child=next(c for c in changed['children'] if c['name']=='runs' and c['index']==1)
        target=root/child['relative'];ppm=target/'outputs/hough_result.ppm'
        data=bytearray(ppm.read_bytes());data[-1]^=1;ppm.write_bytes(data)
        row=json.loads((target/'run.json').read_text());row['ppm_sha256']=digest(ppm)
        write(target/'run.json',row);child['report']['ppm_sha256']=row['ppm_sha256']
        seal=target/'child-seal.json';members=json.loads(seal.read_text())
        for filename in ['outputs/hough_result.ppm','run.json']:
            file=target/filename;members['files'][filename]=dict(bytes=file.stat().st_size,sha256=digest(file))
        write(seal,members)
        check(NAMES[11],lambda:q.cold_verify(changed,parent_override=root),False)
    for position,group,member in [(12,'runtime','runtime.json'),(13,'runtime-validation','results.json'),
                                  (14,'foreign-stream','results.json'),(15,'trace','trace-result.json')]:
        with tempfile.TemporaryDirectory(prefix='hough-cold-coupled-status-') as temporary:
            root=Path(temporary);changed=copy.deepcopy(cold)
            for child in changed['children']:
                source=parent/child['relative'];dest=root/child['relative'];dest.parent.mkdir(parents=True,exist_ok=True)
                if child['name']==group:shutil.copytree(source,dest)
                else:dest.symlink_to(source,target_is_directory=True)
            child=next(c for c in changed['children'] if c['name']==group)
            target=root/child['relative'];product=target/member
            data=json.loads(product.read_text());data['status']='FAILED';write(product,data)
            child['report']['status']='FAILED'
            seal=target/'child-seal.json';members=json.loads(seal.read_text())
            members['files'][member]=dict(bytes=product.stat().st_size,sha256=digest(product));write(seal,members)
            check(NAMES[position],lambda:q.cold_verify(changed,parent_override=root),False)
    for position,group,member,field,value in [
            (16,'contracts','contracts.json','status','FAILED'),
            (17,'build','manifest.json','experiment_outcome','BUILD_ERROR'),
            (18,'foreign-stream','manifest.json','backend','CPU-reference'),
            (19,'trace','manifest.json','parent_experiment_id','forged-build')]:
        with tempfile.TemporaryDirectory(prefix='hough-cold-identity-') as temporary:
            root=Path(temporary);changed=copy.deepcopy(cold)
            for child in changed['children']:
                source=parent/child['relative'];dest=root/child['relative'];dest.parent.mkdir(parents=True,exist_ok=True)
                if child['name']==group:shutil.copytree(source,dest)
                else:dest.symlink_to(source,target_is_directory=True)
            child=next(c for c in changed['children'] if c['name']==group)
            target=root/child['relative'];product=target/member
            data=json.loads(product.read_text());data[field]=value;write(product,data)
            if group=='contracts':child['report']['status']=value
            seal=target/'child-seal.json';members=json.loads(seal.read_text())
            members['files'][member]=dict(bytes=product.stat().st_size,sha256=digest(product));write(seal,members)
            check(NAMES[position],lambda:q.cold_verify(changed,parent_override=root),False)
    with tempfile.TemporaryDirectory(prefix='hough-cold-outer-') as temporary:
        root=Path(temporary);outer=ROOT/cold['evidence']
        shutil.copyfile(outer/'manifest.json',root/'manifest.json')
        commands=json.loads((outer/'commands.json').read_text())
        commands[1]['argv'][-1]='0'*40
        write(root/'commands.json',commands)
        check(NAMES[20],lambda:q.cold_verify(cold,parent_override=parent,outer_override=root),False)
    first=original('validation')[0]['evidence'];real_sealed=q.sealed
    def wrong_parent(ref):
        directory,manifest,source=real_sealed(ref)
        if ref==first:manifest=dict(manifest,parent_experiment_id='forged-nonmatching-run')
        return directory,manifest,source
    with patch.object(q,'sealed',wrong_parent):
        check(NAMES[21],lambda:next(c for c in q.collect(None)[0]
              if c['check']=='fourteen-complete-line-list-CSV-PPM-independent-CPU-recomputations')['passed'],False)
    original_run=original('runs')[0]
    command_path=ROOT/original_run['evidence']/'commands.json'
    forged=json.loads(command_path.read_text());forged[0]['cwd']='/tmp/forged-unrelated-cwd'
    real_read=Path.read_text
    def wrong_cwd(self,*args,**kwargs):
        return json.dumps(forged) if self==command_path else real_read(self,*args,**kwargs)
    with patch.object(Path,'read_text',wrong_cwd):
        check(NAMES[22],lambda:next(c for c in q.collect(None)[0]
              if c['check']=='fourteen-actual-complete-original-CLI-and-products')['passed'],False)
    if [c['check'] for c in checks]!=NAMES:raise ValueError('fixed Hough mutation suite')
    return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',
                case_count=len(checks),checks=checks)

def main():
    path=ROOT/'migration/rewrite/image-hough-qualification-checks-v6.json'
    if not path.exists():
        contract=Experiment('I3','Hough-qualification-mutation-contract','CPU-contract',sources=[__file__,ROOT/'migration/rewrite/image-hough-profile.json'])
        write(path,NAMES);write(contract.path/'cases.json',NAMES)
        result=dict(status='FROZEN',case_count=len(NAMES));write(contract.path/'contracts.json',result)
        result['evidence']=contract.finish('OBSERVED')
        write(ROOT/'migration/reports/image-hough-qualification-check-contract-v6.json',result)
        record('I3','Hough组合资格与45子封印的23项正反向检查合同冻结。',[result['evidence']])
    if json.loads(path.read_text())!=NAMES:raise ValueError('fixed Hough mutation names')
    e=Experiment('I3','Hough-actual-qualification-mutations','CPU-validator-test',
                 sources=[__file__,ROOT/'tools/moat/qualify_image_hough.py',path,ROOT/'migration/rewrite/image-hough-profile.json'])
    result=run_checks();write(e.path/'checks.json',result)
    result['evidence']=e.finish('PASSED' if result['status']=='PASSED' else 'VALIDATOR_GAP',
                                dict(status=result['status'],checks=result['checks']))
    write(ROOT/'migration/reports/image-hough-qualification-checks.json',result)
    record('I3','Hough23项实际组合资格与子封印正反向变异：'+result['status']+'。',[result['evidence']])
    print(result['status'],[c['check'] for c in result['checks'] if not c['passed']])
    return int(result['status']!='PASSED')

if __name__=='__main__':raise SystemExit(main())
