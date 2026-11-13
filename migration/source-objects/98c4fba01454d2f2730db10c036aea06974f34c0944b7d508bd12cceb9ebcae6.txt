#!/usr/bin/env python3
"""Independently validate all22 products of the two actual watershed programs."""
import json
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_encoder_math_binding import sealed
from image_watershed_graph_reference import reference
from image_watershed_region_metrics import compare
import image_watershed_completion_binding as binding
from image_watershed_completion_entries import BUILD,INVENTORY,PORTS,dependencies
RUNS=ROOT/'migration/reports/image-watershed-completion-entries-runs.json'

def current_build():
    b=json.loads(BUILD.read_text());proof=sealed(b,'build.json');binding.need(b['status']=='BUILT' and b['return_code']==0 and set(b['binaries'])==set(PORTS),'complete entry build')
    binding.need(b['contract_sha256']==digest(binding.CONTRACT),'entry build contract')
    binding.need(b['dependencies']=={str(p.relative_to(ROOT)):digest(p) for p in dependencies()},'entry compiled source closure')
    commands=json.loads((proof/'commands.json').read_text());binding.need(len(commands)==2 and all(c['return_code']==0 for c in commands),'two successful entry compiler commands')
    for family,record in b['binaries'].items():
        binary=ROOT/record['path'];binding.need(digest(binary)==record['sha256'],'entry executable SHA')
        command=next(c for c in commands if c['phase']=='build-'+family);argv=command['argv'];binding.need(str(ROOT/PORTS[family]) in argv and str(ROOT/'rocm/common/image/watershed.hip') in argv and '--offload-arch=gfx1201' in argv and argv[-2:]==['-o',str(binary)],'actual original entry compiler/source/output')
    return b

def current_run(row,sample,build):
    family=sample['sample_id'].split('/')[0];binding.need(row['sample_id']==sample['sample_id'] and row['family']==family,'entry identity')
    binding.need(row['status']=='EXECUTED' and row['return_code']==0 and row['contract_sha256']==digest(binding.CONTRACT),'successful current entry contract')
    binary=build['binaries'][family];binding.need(row['build_evidence']==build['evidence'] and row['binary_sha256']==binary['sha256'],'entry build/binary binding')
    proof=sealed(row,'run.json');manifest=json.loads((proof/'manifest.json').read_text());source=json.loads((proof/'source.json').read_text());commands=json.loads((proof/'commands.json').read_text())
    binding.need(manifest['backend']=='rocm-complete-original-entry' and manifest['sample_id']==sample['sample_id'] and manifest['experiment_outcome']=='EXECUTED','actual entry backend/sample/outcome')
    raw=ROOT/manifest['raw_artifact_dir'];binding.need(row['output_dir']==str((raw/'images').relative_to(ROOT)),'entry output path')
    binding.need(len(commands)==1 and commands[0]['return_code']==0 and commands[0]['phase']=='complete-original-file-workflow' and commands[0]['argv']==[str(ROOT/binary['path'])] and commands[0]['cwd']==str(raw/'work'),'actual original executable/cwd')
    binding.need(source['dependencies'].get(str(BUILD.relative_to(ROOT)))==digest(BUILD) and source['dependencies'].get(str(binding.CONTRACT.relative_to(ROOT)))==digest(binding.CONTRACT) and source['dependencies'].get(binary['path'])==binary['sha256'],'entry actual source/build/binary snapshots')
    for name,sha in build['dependencies'].items():binding.need(source['dependencies'].get(name)==sha,'entry compiled source snapshot '+name)
    observed=json.loads((proof/'backend.observed.json').read_text());binding.need(observed['rocm_release']=='10.1.0' and len(observed['devices'])==1 and observed['devices'][0]['physical_id']==1 and observed['devices'][0]['pci_bdf']=='0000:23:00.0','entry actual allowed GPU/ROCm')
    files=json.loads((proof/'sealed.json').read_text())['files'];binding.need(set(row['outputs'])==set(sample['products']),'complete original product inventory')
    for name,identity in row['outputs'].items():
        path=raw/'images'/name;binding.need(identity==files['images/'+name] and path.stat().st_size==identity['bytes']==sample['products'][name]['bytes'] and digest(path)==identity['sha256'],'sealed entry product '+name)
    for item in sample['inputs']:
        path=ROOT/family/'watershedSegmentation/images'/item['name'];binding.need(source['dependencies'].get(str(path.relative_to(ROOT)))==item['sha256'] and digest(raw/'images'/item['name'])==item['sha256'],'actual original input '+item['name'])
    return raw/'images'

def main():
    p=binding.contract();b=current_build();samples=json.loads(INVENTORY.read_text())['samples'];runs=json.loads(RUNS.read_text());native_paths={s:ROOT/f'migration/reports/image-watershed-completion-native-{s}.json' for s in ['NPP','NPPPlus']};native_rows={s:json.loads(path.read_text()) for s,path in native_paths.items()};native_folders={s:binding.native(row,s) for s,row in native_rows.items()}
    binding.need(len(runs)==2 and {r['sample_id'] for r in runs}=={s['sample_id'] for s in samples},'two unique actual entry runs');run_map={r['sample_id']:r for r in runs};results=[]
    helpers=['image_watershed_graph_reference.py','image_watershed_region_metrics.py','image_watershed_completion_binding.py','image_watershed_completion_entries.py','image_encoder_math_binding.py','image_watershed_v2_reference.py','image_watershed_semantics_reference.py']
    for sample in samples:
        run=run_map[sample['sample_id']];family=run['family'];folder=current_run(run,sample,b);native=native_folders['NPPPlus' if family=='NPP+' else 'NPP']
        e=Experiment('I3',sample['sample_id'],'CPU-complete-original-entry-reference',sources=[__file__,binding.CONTRACT,binding.SPEC,BUILD,INVENTORY,RUNS,*native_paths.values(),*[ROOT/'tools/moat'/h for h in helpers],*[ROOT/family/'watershedSegmentation/images'/i['name'] for i in sample['inputs']]]);checks=[];rows=[]
        for item in sample['inputs']:
            name=item['name'];shape=item['height'],item['width'];a=np.fromfile(ROOT/family/'watershedSegmentation/images'/name,np.uint8).reshape(shape);expected,_=reference(a)
            if family=='NPP':mapping={'Segmented_'+name:'segments','Labels_'+name:'labels'}
            else:
                prefix='CT_skull' if name.startswith('CT_skull') else name.split('_')[0];suffix=f'_8Way_{item["width"]}x{item["height"]}'
                mapping={prefix+'_Segments'+suffix+'_8u.raw':'segments',prefix+'_CompressedSegmentLabels'+suffix+'_32u.raw':'compact',prefix+'_SegmentBoundaries'+suffix+'_8u.raw':'boundaries',prefix+'_SegmentsWithContrastingBoundaries'+suffix+'_8u.raw':'contrast'}
            exact={product:(folder/product).read_bytes()==expected[kind].tobytes() for product,kind in mapping.items()};key='original-'+name.removesuffix('.raw')
            native_images={kind:(native/(key+f'-n8-m{mode}-r0.segments')).read_bytes()==expected[kind].tobytes() for kind,mode in [('segments',0),('boundaries',4),('contrast',3)]}
            labels=np.fromfile(native/(key+'-n8-m0-r0.labels'),'<u4').reshape(shape);stats=compare(expected['labels'],labels,e.path/'regions',key)
            checks.extend([dict(check=name+'-all-original-products-CPU-exact',passed=all(exact.values())),dict(check=name+'-native-gray-boundary-contrast-exact',passed=all(native_images.values()))]);rows.append(dict(input=name,products=exact,native_images_exact=native_images,marker_diagnostics=stats));print(family,name,all(exact.values()),all(native_images.values()),flush=True)
        status='PASSED' if all(c['passed'] for c in checks) else 'NUMERIC_MISMATCH';result=dict(status=status,sample_id=sample['sample_id'],family=family,checks=checks,rows=rows,evidence_references=[p['evidence'],b['evidence'],run['evidence'],*[r['evidence'] for r in native_rows.values()]],scope='Every product from the actual original-format program; CPU exact. All original images also match native image modes exactly; marker partitions use the declared graph variant.');write(e.path/'result.json',result);result['evidence']=e.finish(status,dict(status=status,checks=checks));results.append(result);write(ROOT/'migration/reports/image-watershed-completion-entries-reference.json',results)
        record('IMG-02',family+'原入口'+str(len(sample['products']))+'件完整产品独立SCC/native验收：'+status+'；源输入/实际二进制/物理GPU/封存产物均绑定，marker分区差异逐区公开。',[result['evidence']])
    return int(any(r['status']!='PASSED' for r in results))

if __name__=='__main__':raise SystemExit(main())
