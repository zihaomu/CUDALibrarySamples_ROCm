#!/usr/bin/env python3
"""Full corpus: exact graph oracle and both native image-mode references."""
import argparse,json
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_watershed_graph_reference import reference,topology,output_checks
from image_watershed_region_metrics import compare
from image_watershed_semantics_reference import canonical
from image_watershed_v2_reference import bound
import image_watershed_completion_binding as binding
import image_watershed_reference_amendment as amendment
CONTRACT=ROOT/'migration/rewrite/image-watershed-completion-contract.json'
ACTIVE=None

def main(mode,amended=False):
    global ACTIVE
    p=json.loads(CONTRACT.read_text());rp=ROOT/f'migration/reports/image-watershed-completion-AMD-{mode}.json';run=json.loads(rp.read_text());paths={side:ROOT/f'migration/reports/image-watershed-completion-native-{side}.json' for side in ['NPP','NPPPlus']};natives={s:json.loads(f.read_text()) for s,f in paths.items()}
    helpers=['image_watershed_graph_reference.py','image_watershed_region_metrics.py','image_watershed_semantics_reference.py','image_watershed_v2_reference.py','image_encoder_math_binding.py','image_watershed_completion_binding.py','image_watershed_reference_amendment.py']
    e=Experiment('I3','watershed-full-SCC-CPU-native-'+('amended-' if amended else '')+mode,'CPU-reference',sources=[__file__,CONTRACT,binding.SPEC,binding.BUILD,rp,*paths.values(),*[ROOT/'tools/moat'/f for f in helpers],*[ROOT/i['path'] for i in p['inputs']],*([amendment.PATH,amendment.DIAG,amendment.STRICT] if amended else [])]);ACTIVE=e
    p=binding.contract();build=binding.build();raw=binding.amd(run,mode,build);nr={s:binding.native(r,s) for s,r in natives.items()};binding.need(len({r['evidence'] for r in natives.values()})==2,'distinct native vendor records');checks=[];rows=[];expected_names=[];native_names=[]
    amended_contract=amendment.load() if amended else None
    for item in p['inputs']:
        source=ROOT/item['path']
        if source.stat().st_size!=item['bytes'] or digest(source)!=item['sha256']:raise ValueError('frozen input identity')
        shape=item['height'],item['width'];a=np.fromfile(source,np.uint8).reshape(shape);expected,graph=reference(a);topo=topology(expected['labels'],expected['segments']);suffixes=list(expected) if mode!='no-labels' else [s for s in expected if s not in ['labels','compact']]
        actual={}
        for suffix in suffixes:
            name=item['id']+'.'+suffix;expected_names.append(name);actual[suffix]=(raw/name).read_bytes()
        equal=output_checks(expected,actual,mode!='no-labels')
        vendors={}
        for side,folder in nr.items():
            image_modes={};native_labels=[]
            for suffix,m in [('segments',0),('black',1),('white',2),('contrast',3),('boundaries',4)]:
                for repeat in [0,1]:
                    key=item['id']+f'-n8-m{m}-r{repeat}';image_modes[f'{suffix}-r{repeat}']=(folder/(key+'.segments')).read_bytes()==expected[suffix].tobytes();native_labels.append(np.fromfile(folder/(key+'.labels'),'<u4').reshape(shape))
                    if side=='NPP':native_names += [key+'.segments',key+'.labels']
                if m in [3,4]:
                    name=item['id']+f'-n8-m{m}-null.segments';image_modes[suffix+'-null-marker']=(folder/name).read_bytes()==expected[suffix].tobytes()
                    if side=='NPP':native_names.append(name)
            stats=compare(expected['labels'],native_labels[0],e.path/'regions'/side,item['id']);stats['partition_stable_all_modes_and_repeats']=all(np.array_equal(canonical(lab),canonical(native_labels[0])) for lab in native_labels[1:]);vendors[side]=dict(image_exact=image_modes,marker_diagnostics=stats)
            exact=all(image_modes.values());allowed=False
            if not exact and amended:
                allowed=amendment.permits(amended_contract,item,side,a,expected,all(equal.values()),all(vendors['NPP']['image_exact'].values()))
            vendors[side]['comparison_status']='EXACT' if exact else 'NATIVE_MISMATCH';vendors[side]['accepted_under_reference_amendment']=allowed
            checks.append(dict(check=item['id']+'-'+side+('-explicit-project-reference-amendment' if allowed else '-12-native-images'),passed=exact or allowed))
        checks += [dict(check=item['id']+'-all-CPU-products',passed=all(equal.values())),dict(check=item['id']+'-all-regions-connected-and-constant-gray',passed=topo['all_regions_connected'] and topo['all_regions_constant_gray'])]
        row=dict(case=item['id'],split=item['split'],CPU_exact=equal,topology=topo,native=vendors,SCC_components=graph['seed_components']);rows.append(row);print(item['id'],all(equal.values()),all(all(v['image_exact'].values()) for v in vendors.values()),topo,flush=True)
    checks.append(dict(check='complete-AMD-output-inventory',passed=set(run['products'])==set(expected_names) and len(expected_names)==len(p['inputs'])*(5 if mode=='no-labels' else 7)))
    for side,r in natives.items():
        checks.append(dict(check=side+'-complete-native1320-products',passed=set(r['products'])==set(native_names) and len(native_names)==1320))
        proof=ROOT/r['evidence'];commands=json.loads((proof/'commands.json').read_text());command=next(c for c in commands if c['phase']=='frozen-native-corpus');log=(proof/command['stdout']).read_text();lines=[line for line in log.splitlines() if line.startswith('RESULT ')]
        checks.append(dict(check=side+'-720-successful-native-calls-and-padding',passed=len(lines)==720 and all('status=0 padding=1 ' in line for line in lines)))
    status='PASSED' if all(c['passed'] for c in checks) else 'NUMERIC_MISMATCH';result=dict(status=status,mode=mode,amended=amended,checks=checks,rows=rows,contract_sha256=digest(CONTRACT),evidence_references=[p['evidence'],build['evidence'],run['evidence'],*[r['evidence'] for r in natives.values()],*([amended_contract['evidence']] if amended else [])],scope='Component contract only. Marker partition is an explicit algorithm variant. '+('NPP60/60 EXACT; NPPPlus57/60 EXACT and three precisely identified native disagreements under the sealed amendment; original strict failures remain.' if amended else 'Every native image product is an exact gate; native failures are not accepted.'));write(e.path/'result.json',result);result['evidence']=e.finish(status,dict(status=status,checks=checks));write(ROOT/f'migration/reports/image-watershed-completion-reference-{"amended-" if amended else ""}{mode}.json',result)
    record('IMG-02','60输入 '+mode+' 独立SCC参考/双原生检查：'+status+'；36保留输入完整纳入，逐区交叉表、含未匹配惩罚的一对一IoU、四方向逐边差异和null-marker模式均保留。',[result['evidence']]);return int(status!='PASSED')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',default='padded',choices=['compact','padded','inplace','no-labels']);p.add_argument('--amended',action='store_true');a=p.parse_args()
    try:rc=main(a.mode,a.amended)
    except Exception as error:
        if ACTIVE is not None and not ACTIVE.sealed:
            ref=ACTIVE.finish('VALIDATOR_GAP',reason=repr(error));record('IMG-02','完整Watershed参考异常已封存：'+repr(error),[ref])
        raise
    raise SystemExit(rc)
