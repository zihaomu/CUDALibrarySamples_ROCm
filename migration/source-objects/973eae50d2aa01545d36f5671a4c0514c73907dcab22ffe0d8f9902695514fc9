#!/usr/bin/env python3
"""Freeze both complete original watershed entrypoints before the HIP rewrite."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_progress import record
from image_watershed_research import NATIVE,SIZES

SOURCES={
 'NPP':'NPP/watershedSegmentation/watershedSegmentation.cpp',
 'NPP+':'NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp',
}
INPUTS={
 'NPP':['Lena_512x512_8u_Gray.raw','CT_skull_512x512_8u_Gray.raw',
  'Rocks_512x512_8u_Gray.raw','coins_500x383_8u_Gray.raw','coins_overlay_500x569_8u_Gray.raw'],
 'NPP+':['CT_skull_512x512_8u_Gray.raw','Rocks_512x512_8u_Gray.raw','Corn_614x461_8u_Gray.raw'],
}

def main():
 sources=[Path(__file__),ROOT/'tools/moat/image_watershed_research.py']
 for family in SOURCES:
  sources += [ROOT/SOURCES[family],ROOT/NATIVE[family]/'run.json']
  sources += [ROOT/family/'watershedSegmentation/images'/name for name in INPUTS[family]]
 e=Experiment('I3','two-original-watershed-entrypoints-and-six-images','CPU-contract',sources=sources)
 samples=[]
 for family in SOURCES:
  native=json.loads((ROOT/NATIVE[family]/'run.json').read_text())
  images=[]
  for name in INPUTS[family]:
   path=ROOT/family/'watershedSegmentation/images'/name;w,h=SIZES[name]
   images.append(dict(name=name,width=w,height=h,bytes=w*h,sha256=digest(path)))
  products={name.removeprefix('images/'):meta for name,meta in native['files'].items()
            if name.startswith('images/') and name.removeprefix('images/') not in INPUTS[family]}
  if len(products)!=(10 if family=='NPP' else 12):raise ValueError('complete original output inventory')
  samples.append(dict(sample_id=family+'/watershedSegmentation::'+Path(SOURCES[family]).name,
    original_source=SOURCES[family],source_sha256=digest(ROOT/SOURCES[family]),
    native_evidence=NATIVE[family],native_status=native['status'],
    inputs=images,products=products,default_cli=[],invalid_cases=['missing-input'],
    output_modes=['segments','labels'] if family=='NPP' else
      ['segments','compressed-labels','boundaries-only','contrasting-boundaries']))
 profile=dict(status='FROZEN',stage='I3',samples=samples,
  project_algorithm=dict(connectivity=8,rule='each pixel selects minimum (intensity, row-major index) in its 3x3 neighborhood; repeated pointer doubling reaches a fixed root',
    segments='unsigned 8-bit intensity at final root',labels='unsigned 32-bit zero-based root index',
    compact_labels='roots ordered by row-major index and replaced with consecutive zero-based IDs',
    boundaries_only='0 if any in-bounds eight-neighbor has a different root, otherwise 255',
    contrasting_boundaries='255 at project boundary, otherwise root intensity'),
  acceptance=dict(project_CPU_vs_HIP='EXACT for every output byte and product name/size',
    native_comparison='ALGORITHM_VARIANT: report pixel agreement and label partition metrics for all original images; no NVIDIA pixel-exact claim',
    GPU_execution='actual gfx1201 kernels and independent output/hash/stream checks required',
    failure='missing original image returns nonzero with diagnostic; no silent fallback'))
 write(e.path/'profile.json',profile)
 ref=e.finish('OBSERVED',dict(status='FROZEN',checks=[dict(check='two-original-entrypoints-eight-input-uses-and-22-products',passed=True)]))
 profile['evidence']=ref
 write(ROOT/'migration/rewrite/image-watershed-profile.json',profile)
 record('I3','NPP 5图10产品、NPP+ 3图12产品及5090原始SHA/完整输出模式冻结；项目八邻域下降算法只按CPU精确验收，跨vendor差异明确记ALGORITHM_VARIANT，不升级资格。',[ref])
 print('FROZEN',len(samples),sum(len(s['products']) for s in samples),ref)

if __name__=='__main__':main()
