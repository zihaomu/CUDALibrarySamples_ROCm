#!/usr/bin/env python3
"""Inspect complete native repetitions, topology and the previously failed descent model."""
import json
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_encoder_math_binding import sealed
from image_watershed_research import descent

def canonical(labels):
    _,first,inverse=np.unique(labels,return_index=True,return_inverse=True)
    rank=np.empty(len(first),np.int64);rank[np.argsort(first)]=np.arange(len(first))
    return rank[inverse].reshape(labels.shape)

def main():
    pp=ROOT/'migration/rewrite/image-watershed-semantics-profile.json';p=json.loads(pp.read_text());reports={side:ROOT/f'migration/reports/image-watershed-semantics-{side}.json' for side in ['NPP','NPPPlus']};runs={s:json.loads(f.read_text()) for s,f in reports.items()};roots={}
    for side,row in runs.items():
        proof=sealed(row);roots[side]=ROOT/json.loads((proof/'manifest.json').read_text())['raw_artifact_dir']/'outputs'
        for name,identity in row['products'].items():
            f=roots[side]/name;expected=json.loads((proof/'sealed.json').read_text())['files']['outputs/'+name]
            if identity!=expected or f.stat().st_size!=identity['bytes'] or digest(f)!=identity['sha256']:raise ValueError('native product identity')
    e=Experiment('I3','watershed-native-repeatability-and-descent-diagnosis','CPU-observation',sources=[__file__,pp,ROOT/'tools/moat/image_watershed_research.py',ROOT/'tools/moat/image_encoder_math_binding.py',*reports.values(),*[ROOT/i['path'] for i in p['inputs']]])
    rows=[];checks=[]
    for item in p['inputs']:
        shape=item['height'],item['width'];source=np.fromfile(ROOT/item['path'],np.uint8).reshape(shape);old,old_segments,_=descent(source)
        for norm in p['connectivity']:
            values={};repeat=True;labels_modes=True;vendor_equal=True
            for side,root in roots.items():
                groups=[]
                for mode in range(5):
                    repeats=[]
                    for r in range(3):
                        key=f'{item["id"]}-n{norm}-m{mode}-r{r}';seg=np.fromfile(root/(key+'.segments'),np.uint8).reshape(shape);labels=np.fromfile(root/(key+'.labels'),'<u4').reshape(shape);repeats.append((seg,labels))
                    repeat &= all(np.array_equal(a,repeats[0][0]) and np.array_equal(canonical(b),canonical(repeats[0][1])) for a,b in repeats[1:]);groups.append(repeats[0])
                labels_modes &= all(np.array_equal(canonical(g[1]),canonical(groups[0][1])) for g in groups[1:]);values[side]=groups
            vendor_equal=all(np.array_equal(a[0],b[0]) and np.array_equal(canonical(a[1]),canonical(b[1])) for a,b in zip(values['NPP'],values['NPPPlus']))
            seg,labels=values['NPP'][0];c=canonical(labels);oldc=canonical(old)
            row=dict(case=item['id'],connectivity=norm,stable_across_scratch_fills=bool(repeat),same_partition_all_boundary_modes=bool(labels_modes),NPP_and_NPPPlus_equal=bool(vendor_equal),native_regions=int(np.unique(labels).size),native_segment_values=np.unique(seg).tolist())
            if norm==8:row.update(old_descent_regions=int(np.unique(old).size),old_descent_segment_match=float(np.mean(seg==old_segments)),old_descent_partition_exact=bool(np.array_equal(c,oldc)))
            rows.append(row);print(item['id'],norm,row,flush=True)
    checks.append(dict(check='complete18-inputs-two-connectivities',passed=len(rows)==36))
    for side,run in runs.items():
        proof=ROOT/run['evidence'];commands=json.loads((proof/'commands.json').read_text());command=next(c for c in commands if c['phase']=='native-semantic-observations');log=(proof/command['stdout']).read_text();results=[line for line in log.splitlines() if line.startswith('RESULT ')]
        checks.append(dict(check=side+'-all540-API-observations-and-padding',passed=len(results)==540 and all('status=0 padding=1 ' in line for line in results)))
    result=dict(status='OBSERVED',checks=checks,rows=rows,evidence_references=[r['evidence'] for r in runs.values()],scope='Semantic observations only. Repeatability is measured, not assumed; the previously failed local-descent model is diagnosed, not promoted.')
    write(e.path/'result.json',result);result['evidence']=e.finish('OBSERVED',dict(status='OBSERVED',checks=checks));write(ROOT/'migration/reports/image-watershed-semantics-reference.json',result)
    record('IMG-02','18个输入/两邻域语义比对完成：工作区初值重复、5边界模式标签分区及两SDK结果均逐项记录；同时定位旧局部下降模型差异，不据原生观察新增资格。',[result['evidence']]);return 0

if __name__=='__main__':raise SystemExit(main())
