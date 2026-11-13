#!/usr/bin/env python3
"""Separate native output-value connectivity from watershed basin labels."""
import json
import numpy as np
from scipy.ndimage import label
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_watershed_semantics_reference import canonical
from image_encoder_math_binding import sealed

def main():
    pp=ROOT/'migration/rewrite/image-watershed-semantics-profile.json';p=json.loads(pp.read_text());rp=ROOT/'migration/reports/image-watershed-semantics-NPP.json';run=json.loads(rp.read_text());proof=sealed(run);root=ROOT/json.loads((proof/'manifest.json').read_text())['raw_artifact_dir']/'outputs'
    e=Experiment('I3','watershed-native-segment-label-topology','CPU-research',sources=[__file__,pp,rp,ROOT/'tools/moat/image_watershed_semantics_reference.py']);rows=[]
    for item in p['inputs']:
        for norm in [4,8]:
            key=item['id']+f'-n{norm}-m0-r0';files=[root/(key+'.segments'),root/(key+'.labels')]
            if any(digest(f)!=run['products'][f.name]['sha256'] for f in files):raise ValueError('native identity')
            seg=np.fromfile(files[0],np.uint8).reshape(item['height'],item['width']);labels=np.fromfile(files[1],'<u4').reshape(seg.shape)
            for connectivity in [4,8]:
                structure=np.ones((3,3)) if connectivity==8 else np.array([[0,1,0],[1,1,1],[0,1,0]])
                components=np.zeros(seg.shape,np.int32);offset=0
                for value in np.unique(seg):
                    mask=seg==value;c,n=label(mask,structure);components[mask]=c[mask]+offset;offset+=n
                row=dict(case=item['id'],native_connectivity=norm,component_connectivity=connectivity,output_value_components=offset,native_regions=int(np.unique(labels).size),partition_exact=bool(np.array_equal(canonical(components),canonical(labels))));rows.append(row);print(row)
    result=dict(status='OBSERVED',rows=rows,evidence_references=[run['evidence']]);write(e.path/'result.json',result);result['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-watershed-label-research.json',result)
    record('IMG-02','单独核查原生输出灰度连通块与marker分区关系，避免把恒定输出灰度等同于区域标签；18×2×2组拓扑观察封存。',[result['evidence']])

if __name__=='__main__':main()
