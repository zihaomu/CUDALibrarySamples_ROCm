#!/usr/bin/env python3
"""Bind and explain the native long-ramp disagreement using an analytic oracle."""
import hashlib,json,shlex,tarfile
import numpy as np
from scipy.ndimage import minimum_filter
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_watershed_v2_reference import bound
from image_encoder_math_binding import sealed
import image_watershed_completion_binding as binding

def main():
    pp=ROOT/'migration/rewrite/image-watershed-monotone-native-profile.json';profile=json.loads(pp.read_text());paths={key:ROOT/f'migration/reports/image-watershed-monotone-{key}.json' for key in ['NPP-padded','NPP-compact','NPPPlus-padded','NPPPlus-compact','AMD']};runs={k:json.loads(f.read_text()) for k,f in paths.items()}
    helpers=['image_watershed_v2_reference.py','image_encoder_math_binding.py','image_watershed_completion_binding.py']
    e=Experiment('I3','watershed-monotone-native-independent-reference','CPU-reference',sources=[__file__,pp,*paths.values(),binding.BUILD,*[ROOT/'tools/moat'/f for f in helpers],ROOT/'rocm/probes/image/watershed_monotone_native.cpp',*[ROOT/i['path'] for i in profile['inputs']]]);folders={k:bound(r) for k,r in runs.items()};checks=[];rows=[]
    sealed(profile,'profile.json');b=binding.build();fixture=ROOT/'migration/fixtures/image-watershed-monotone-native';native_source=ROOT/'rocm/probes/image/watershed_monotone_native.cpp'
    expected_ids={f'{direction}-{size}' for direction in ['x','y','diagonal','reverse-x'] for size in [17,33,49,65,97,129]}
    binding.need(profile['status']=='FROZEN_OBSERVATION_ONLY' and len(profile['inputs'])==24 and {i['id'] for i in profile['inputs']}==expected_ids,'sealed24 analytic input inventory')
    expected_list=''.join(f'{i["id"]} {i["width"]} {i["height"]}\n' for i in profile['inputs']);binding.need((fixture/'cases.txt').read_text()==expected_list,'actual analytic input list')
    for item in profile['inputs']:
        size=int(item['id'].rsplit('-',1)[1]);binding.need(item['width']==item['height']==size and item['bytes']==size*size and (ROOT/item['path']).stat().st_size==item['bytes'] and digest(ROOT/item['path'])==item['sha256'],'analytic input dimension/extent/SHA')
    native_names={i['id']+f'-n8-m{m}-r{r}.'+suffix for i in profile['inputs'] for m in range(5) for r in range(2) for suffix in ['segments','labels']}
    native_names|={i['id']+f'-n8-m{m}-null.segments' for i in profile['inputs'] for m in [3,4]}
    native_names|={i['id']+f'-pass{r}.segments' for i in profile['inputs'] for r in range(1,5)}
    amd_names={i['id']+'.'+suffix for i in profile['inputs'] for suffix in ['segments','labels','compact','boundaries','contrast','black','white']}
    for key,row in runs.items():
        proof=ROOT/row['evidence'];commands=json.loads((proof/'commands.json').read_text());source=json.loads((proof/'source.json').read_text());manifest=json.loads((proof/'manifest.json').read_text())
        binding.need(source['dependencies'].get(str(pp.relative_to(ROOT)))==digest(pp),'diagnostic profile source binding')
        binding.need(source['dependencies'].get(str((fixture/'cases.txt').relative_to(ROOT)))==digest(fixture/'cases.txt'),'diagnostic input list snapshot')
        for item in profile['inputs']:binding.need(source['dependencies'].get(item['path'])==item['sha256'],'diagnostic input snapshot '+item['id'])
        binding.need(all(c['return_code']==0 for c in commands),'diagnostic actual command status')
        if key=='AMD':
            b=binding.build();binding.need(row['status']=='PASSED' and row['build_evidence']==b['evidence'],'diagnostic AMD build identity');command=next(c for c in commands if c['phase']=='analytic-ramp-corpus');binding.need(command['argv']==[str(ROOT/b['binary']['path']),str(ROOT/'migration/fixtures/image-watershed-monotone-native'),str(ROOT/json.loads((proof/'manifest.json').read_text())['raw_artifact_dir']/'outputs'),'padded'],'actual diagnostic AMD input/binary/layout')
            observed=json.loads((proof/'backend.observed.json').read_text());binding.need(observed['rocm_release']=='10.1.0' and observed['devices'][0]['physical_id']==1 and observed['devices'][0]['pci_bdf']=='0000:23:00.0','actual diagnostic AMD device')
            binding.need(manifest['backend']=='rocm' and len(commands)==1 and len(observed['devices'])==1 and observed['packages']['rocm-sdk-core']=='10.1.0','diagnostic actual AMD backend')
            binding.need(source['dependencies'].get(str(binding.BUILD.relative_to(ROOT)))==digest(binding.BUILD) and source['dependencies'].get(b['binary']['path'])==b['binary']['sha256'],'diagnostic actual build/executable snapshots')
            for name,sha in b['dependencies'].items():binding.need(source['dependencies'].get(name)==sha,'diagnostic compiled source '+name)
            lines=(proof/command['stdout']).read_text().splitlines();binding.need([s for s in lines if s.startswith('RESULT ')]==[f'RESULT {i["id"]} pixels={i["bytes"]} products=7 padding=1 mode=padded' for i in profile['inputs']],'actual analytic AMD calls and padding')
        else:
            vendor,layout=key.split('-');binding.need(row['vendor']==vendor and row['layout']==layout and row['status']=='OBSERVED','diagnostic vendor/layout identity');command=next(c for c in commands if c['phase']=='native-monotone-diagnosis');argv=shlex.split(command['argv'][-1]);binding.need(command['argv'][:2]==['ssh','nvidia-5090x2'] and argv[:2]==['env','CUDA_VISIBLE_DEVICES=1'],'actual diagnostic NVIDIA host/device');compile_command=next(c for c in commands if c['phase']=='build');flags=shlex.split(compile_command['argv'][-1]);binding.need(('-DIMAGE_NPP_PLUS' in flags)==(vendor=='NPPPlus') and (('-DIMAGE_TIGHT_PITCH' in flags)==(layout=='compact')),'actual diagnostic SDK/pitch compile flags');log=(proof/command['stdout']).read_text();binding.need('PCI 0000:E1:00.0 NPP '+('12.4.0' if vendor=='NPPPlus' else '13.2.0') in log,'actual diagnostic native SDK/device')
            remote='/tmp/'+manifest['experiment_id'];binding.need(manifest['backend']=='cuda-diagnosis' and argv==['env','CUDA_VISIBLE_DEVICES=1',remote+'/probe',remote+'/inputs',remote+'/outputs'],'complete diagnostic native argv')
            binding.need(flags[0]=='/usr/local/cuda-13.4/bin/nvcc' and remote+'/probe.cpp' in flags and flags[flags.index('-o')+1]==remote+'/probe','diagnostic actual compiled source/output')
            binding.need(source['dependencies'].get(str(native_source.relative_to(ROOT)))==digest(native_source),'diagnostic source snapshot')
            with tarfile.open(ROOT/manifest['raw_artifact_dir']/'inputs.tar') as tar:
                binding.need(hashlib.sha256(tar.extractfile('probe.cpp').read()).hexdigest()==digest(native_source) and tar.extractfile('inputs/cases.txt').read()==(fixture/'cases.txt').read_bytes(),'uploaded diagnostic source/list')
                for item in profile['inputs']:binding.need(hashlib.sha256(tar.extractfile('inputs/'+item['id']+'.raw').read()).hexdigest()==item['sha256'],'uploaded analytic raw '+item['id'])
            lines=log.splitlines();calls=[s for s in lines if s.startswith('RESULT ')];chains=[s for s in lines if s.startswith('CHAIN ')]
            checks.append(dict(check=key+'-all288-API-calls-and-padding-plus96-chain-calls',passed=len(calls)==288 and all('status=0 padding=1 ' in s for s in calls) and len(chains)==96 and all(s.endswith('status=0') for s in chains)))
        checks.append(dict(check=key+'-complete-product-set',passed=set(row['products'])==(amd_names if key=='AMD' else native_names)))
        checks.append(dict(check=key+'-bound-actual-vendor-layout-platform-input',passed=True))
    for item in profile['inputs']:
        path=ROOT/item['path'];binding.need(digest(path)==item['sha256'],'analytic input identity');shape=item['height'],item['width'];a=np.fromfile(path,np.uint8).reshape(shape);lower=minimum_filter(a,size=3,mode='constant',cval=255)<a
        analytic=bool(np.all(lower|(a==0)));checks.append(dict(check=item['id']+'-all-terminal-minima-proven-zero',passed=analytic));row=dict(case=item['id'],analytic_minimum_zero=analytic,sides={})
        for key,folder in folders.items():
            exact={}
            if key=='AMD':
                for suffix,value in [('segments',0),('black',0),('white',0),('contrast',0),('boundaries',255)]:exact[suffix]=(folder/(item['id']+'.'+suffix)).read_bytes()==bytes([value])*item['bytes']
            else:
                for mode in range(5):
                    for repeat in range(2):
                        suffix=f'-n8-m{mode}-r{repeat}.segments';exact[suffix]=(folder/(item['id']+suffix)).read_bytes()==bytes([255 if mode==4 else 0])*item['bytes']
                for mode in [3,4]:
                    suffix=f'-n8-m{mode}-null.segments';exact[suffix]=(folder/(item['id']+suffix)).read_bytes()==bytes([255 if mode==4 else 0])*item['bytes']
                for repeat in range(1,5):
                    suffix=f'-pass{repeat}.segments';exact[suffix]=(folder/(item['id']+suffix)).read_bytes()==bytes(item['bytes'])
            row['sides'][key]=dict(all_image_outputs_analytic_exact=all(exact.values()),image_checks=exact)
            if key in ['AMD','NPP-padded','NPP-compact']:checks.append(dict(check=item['id']+'-'+key+'-exact-analytic-image-modes',passed=all(exact.values())))
        rows.append(row)
    identity=all(runs['NPPPlus-padded']['products'][name]==runs['NPPPlus-compact']['products'][name] for name in runs['NPPPlus-padded']['products'])
    checks.append(dict(check='NPPPlus-both-pitches-all624-products-byte-identical',passed=identity and all((folders['NPPPlus-padded']/name).read_bytes()==(folders['NPPPlus-compact']/name).read_bytes() for name in native_names)))
    failures={key:[row['case'] for row in rows if not row['sides'][key]['all_image_outputs_analytic_exact']] for key in runs}
    checks.append(dict(check='NPPPlus16-repeatable-diagnostic-disagreements-in-both-layouts',passed=len(failures['NPPPlus-padded'])==16 and failures['NPPPlus-padded']==failures['NPPPlus-compact']))
    for key in ['NPPPlus-padded','NPPPlus-compact']:
        changed=[];monotone=True
        for item in profile['inputs']:
            arrays=[np.fromfile(folders[key]/(item['id']+f'-pass{k}.segments'),np.uint8) for k in range(1,5)]
            monotone &= all(bool(np.all(next_array<=previous)) for previous,next_array in zip(arrays,arrays[1:]))
            if any(not np.array_equal(previous,next_array) for previous,next_array in zip(arrays,arrays[1:])):changed.append(item['id'])
        checks.append(dict(check=key+'-all-chain-values-nonincreasing-and16-disagreements-still-changing',passed=bool(monotone) and set(changed)==set(failures[key]) and len(changed)==16))
    status='PASSED' if all(c['passed'] for c in checks) else 'NUMERIC_MISMATCH';result=dict(status=status,checks=checks,rows=rows,native_disagreements=failures,NPPPlus_all_products_identical_between_pitches=identity,evidence_references=[profile['evidence'],b['evidence'],*[r['evidence'] for r in runs.values()]],scope='PASS validates the analytic reference and the measured disagreement, not NPPPlus correctness. NPPPlus mismatch remains a failed native comparison. No project algorithm or acceptance amendment is applied here.');write(e.path/'result.json',result);result['evidence']=e.finish(status,dict(status=status,checks=checks));write(ROOT/'migration/reports/image-watershed-monotone-reference.json',result)
    record('IMG-02','24解析坡度独立参考：'+status+'；NPP和HIP五模式精确，NPP+两pitch各16例不符且复调用仍改变。诊断通过不代表NPP+通过，原60输入严格门槛失败继续保留。',[result['evidence']]);print(status,failures,identity);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
