#!/usr/bin/env python3
"""Exercise actual watershed file programs: kernels, changed inputs and I/O errors."""
import argparse,collections,csv,json,shutil
from experiment import ROOT,Experiment,digest,write
from snapshot import capture
from image_completion_progress import record
from image_encoder_math_binding import sealed
from image_watershed_completion_entries import BUILD,INVENTORY,CONTRACT,dependencies

RUNS=ROOT/'migration/reports/image-watershed-completion-entries-runs.json'
STAGES=('descend','root_jump','root_gray','relax_markers','mark_used','scan_blocks','scan_offsets','render')

def build():
    b=json.loads(BUILD.read_text());sealed(b,'build.json')
    if b['status']!='BUILT' or b['dependencies']!={str(p.relative_to(ROOT)):digest(p) for p in dependencies()} or b['contract_sha256']!=digest(CONTRACT):raise ValueError('current original build required')
    for item in b['binaries'].values():
        if digest(ROOT/item['path'])!=item['sha256']:raise ValueError('executable identity')
    return b

def mapping(item,family):
    name=item['name']
    if family=='NPP':return {'Segmented_'+name:'segments','Labels_'+name:'labels'}
    prefix='CT_skull' if name.startswith('CT_skull') else name.split('_')[0]
    suffix=f'_8Way_{item["width"]}x{item["height"]}'
    return {prefix+'_Segments'+suffix+'_8u.raw':'segments',prefix+'_CompressedSegmentLabels'+suffix+'_32u.raw':'compact',prefix+'_SegmentBoundaries'+suffix+'_8u.raw':'boundaries',prefix+'_SegmentsWithContrastingBoundaries'+suffix+'_8u.raw':'contrast'}

def main(action):
    b=build();samples=json.loads(INVENTORY.read_text())['samples'];runs={r['sample_id']:r for r in json.loads(RUNS.read_text())};rows=[]
    for sample in samples:
        family=sample['sample_id'].split('/')[0];binary=ROOT/b['binaries'][family]['path'];baseline=runs[sample['sample_id']];sealed(baseline,'run.json')
        cases=['original'] if action=='trace' else ['invert-first'] if action=='replay' else ['missing-first','missing-last','truncated-first','blocked-output']
        for case in cases:
            e=Experiment('I3',sample['sample_id'],'rocm-complete-entry-'+action,case=case,sources=[__file__,BUILD,INVENTORY,CONTRACT,RUNS,binary,*dependencies(),*[ROOT/family/'watershedSegmentation/images'/i['name'] for i in sample['inputs']]])
            try:
                write(e.path/'backend.observed.json',capture());images=e.path/'images';images.mkdir();work=e.path/'work';work.mkdir()
                for item in sample['inputs']:
                    source=ROOT/family/'watershedSegmentation/images'/item['name']
                    if digest(source)!=item['sha256']:raise ValueError('original input identity')
                    shutil.copyfile(source,images/item['name'])
                first=sample['inputs'][0];last=sample['inputs'][-1];expected=set(sample['products']);bad=None
                if case=='invert-first':
                    path=images/first['name'];path.write_bytes(bytes(255-v for v in path.read_bytes()))
                elif case in ('missing-first','missing-last'):
                    bad=first if case=='missing-first' else last;(images/bad['name']).unlink();expected-=set(mapping(bad,family))
                    if case=='missing-first':expected=set()
                elif case=='truncated-first':
                    bad=first;path=images/first['name'];path.write_bytes(path.read_bytes()[:-1]);expected=set()
                elif case=='blocked-output':
                    bad=first;(images/next(iter(mapping(first,family)))).mkdir();expected=set()
                input_rows={i['name']:dict(sha256=digest(images/i['name']),bytes=(images/i['name']).stat().st_size) for i in sample['inputs'] if (images/i['name']).is_file()}
                write(e.path/'runtime-contract.json',dict(action=action,case=case,recipe='first input byte v becomes 255-v; all others unchanged' if action=='replay' else case,inputs=input_rows,expected_products=sorted(expected),build_evidence=b['evidence'],binary_sha256=digest(binary)))
                argv=['rocprofv3','--kernel-trace','--output-format','csv','--output-directory',str(e.path/'trace'),'--',str(binary)] if action=='trace' else [str(binary)]
                rc=e.command(argv,'actual-entry-'+case,cwd=work,timeout=300)
                outputs={p.name:dict(bytes=p.stat().st_size,sha256=digest(p)) for p in images.iterdir() if p.is_file() and p.name not in input_rows}
                checks=[dict(check='exact-file-inventory-and-extents',passed=set(outputs)==expected and all(outputs[n]['bytes']==sample['products'][n]['bytes'] for n in expected)),dict(check='entry-exit-status',passed=rc==0 if action!='negative' else rc==1)]
                observed=json.loads((e.path/'backend.observed.json').read_text());checks.append(dict(check='actual-approved-GPU-and-ROCm',passed=observed['rocm_release']=='10.1.0' and len(observed['devices'])==1 and observed['devices'][0]['physical_id']==1 and observed['devices'][0]['pci_bdf']=='0000:23:00.0'))
                counts=collections.Counter()
                if action=='trace':
                    checks.append(dict(check='all-traced-products-identical-to-validated-originals',passed=outputs==baseline['outputs']))
                    traces=list((e.path/'trace').rglob('*kernel_trace.csv'));agents=list((e.path/'trace').rglob('*agent_info.csv'))
                    checks.append(dict(check='one-kernel-and-agent-trace',passed=len(traces)==len(agents)==1))
                    dispatches=[]
                    if len(traces)==len(agents)==1:
                        agent_map={r['Node_Id']:r for r in csv.DictReader(agents[0].open())}
                        for row in csv.DictReader(traces[0].open()):
                            stage=next((s for s in STAGES if 'image_watershed_v2::'+s+'(' in row['Kernel_Name']),None)
                            if stage is None:continue
                            counts[stage]+=1;agent=agent_map[row['Agent_Id'].split()[-1]];loc=int(agent['Location_Id']);pci=f"{int(agent['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}"
                            dispatches.append(pci=='0000:23:00.0' and int(row['End_Timestamp'])>int(row['Start_Timestamp']) and int(row['Grid_Size_X'])>0)
                    n=len(sample['inputs']);stages=STAGES if family=='NPP+' else tuple(s for s in STAGES if s not in ('mark_used','scan_blocks','scan_offsets'))
                    checks.extend([dict(check='all-required-GPU-stages',passed=set(counts)==set(stages) and all(counts[s]>=n for s in stages)),dict(check='eight-pointer-jumps-per-original-image',passed=counts['root_jump']==8*n),dict(check='all-real-dispatches-positive-and-correct-physical-GPU',passed=bool(dispatches) and all(dispatches))])
                elif action=='negative':
                    stderr=(e.path/e.commands[-1]['stderr']).read_text();stdout=(e.path/e.commands[-1]['stdout']).read_text();message='Failed to save products for ' if case=='blocked-output' else 'Failed to load '
                    checks.extend([dict(check='specific-error-no-false-success',passed=message+bad['name'] in stderr and 'Processed '+bad['name'] not in stdout),dict(check='earlier-complete-products-retain-correct-bytes',passed=all(outputs[n]==baseline['outputs'][n] for n in expected))])
                else:
                    changed=set(mapping(first,family));checks.extend([dict(check='every-first-image-product-changed',passed=all(outputs.get(n)!=baseline['outputs'][n] for n in changed)),dict(check='all-other-images-identical',passed=all(outputs.get(n)==baseline['outputs'][n] for n in expected-changed))])
                status='PASSED' if all(c['passed'] for c in checks) else 'RUNTIME_ERROR'
                row=dict(status=status,action=action,case=case,sample_id=sample['sample_id'],family=family,return_code=rc,checks=checks,outputs=outputs,input_rows=input_rows,output_dir=str(images.relative_to(ROOT)),kernel_counts=dict(counts),binary_sha256=digest(binary),build_evidence=b['evidence'],evidence_references=[b['evidence'],baseline['evidence']])
                write(e.path/'result.json',row);row['evidence']=e.finish('EXPECTED_REJECTION' if status=='PASSED' and action=='negative' else status,dict(status=status,checks=checks));rows.append(row);write(ROOT/f'migration/reports/image-watershed-completion-entry-{action}.json',rows)
                record('IMG-02',family+'原入口'+action+'/'+case+'：'+status+'，完整文件集合、实际GPU和构建身份已记录。'+('独立CPU重算待验证。' if action=='replay' else ''),[row['evidence']]);print(family,action,case,status,dict(counts),flush=True)
            except BaseException as error:
                if not e.sealed:e.finish('VALIDATOR_GAP',reason=repr(error))
                raise
    return int(any(r['status']!='PASSED' for r in rows))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['trace','replay','negative']);raise SystemExit(main(p.parse_args().action))
