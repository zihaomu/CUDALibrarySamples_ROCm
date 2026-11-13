#!/usr/bin/env python3
"""Build isolated exact rational color and corrected DC encoder candidates."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

def main():
    from snapshot import capture
    profile=ROOT/'migration/rewrite/image-encoder-math-variant-profile.json'
    if json.loads(profile.read_text())['status']!='FROZEN':raise ValueError('freeze mathematics first')
    base=ROOT/'migration/reports/image-encoder-rounding-candidate-build.json';b=json.loads(base.read_text())
    if any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()):raise ValueError('parent source drift')
    parent=ROOT/'build/image-encoder-exact-DC-rounding-candidate/common';folder=ROOT/'build/image-encoder-math-candidate/common';copies=[]
    for name in b['dependencies']:
        source=ROOT/name
        if not source.is_relative_to(parent):continue
        dest=folder/source.relative_to(parent);dest.parent.mkdir(parents=True,exist_ok=True);data=source.read_text()
        if source.name=='jpeg_wide_transform.hpp':
            start=data.index('    float total=0.0f;');end=data.index('\n}\n',start)
            data=data[:start]+'''    // The largest numerator is 255.5 * 1,000,000 * 4, below INT_MAX.
    // Exact decimal weights prevent compiler FMA from moving half-integer ties.
    int total=0;
    for(int dy=0;dy<scale;++dy)for(int dx=0;dx<scale;++dx) {
        const int sx=x*scale+dx<width?x*scale+dx:width-1;
        const int sy=y*scale+dy<height?y*scale+dy:height-1;
        const auto* color=rgb+(size_t(sy)*width+sx)*3;
        const int r=color[0],g=color[1],b=color[2];
        total+=channel==0?299000*r+587000*g+114000*b:
               channel==1?128000000-168736*r-331264*g+500000*b:
                          128000000+500000*r-418688*g-81312*b;
    }
    const int denominator=1000000*scale*scale;
    int rounded=total/denominator;
    const int twice_remainder=2*(total%denominator);
    rounded+=twice_remainder>denominator || (twice_remainder==denominator && (rounded&1));
    plane[index]=static_cast<unsigned char>(rounded<0?0:rounded>255?255:rounded);'''+data[end:]
        if dest.exists() and dest.read_text()!=data:raise ValueError('isolated candidate already has different bytes')
        dest.write_text(data);copies.append(dest)
    jpeg=ROOT/'build/cpu-codecs';core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay'
    sources={'sample':ROOT/'rocm/ported/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp','probe':ROOT/'rocm/probes/image/jpeg_wide_transform.hip'}
    deps={str(p.relative_to(ROOT)):digest(p) for p in [profile,base,*copies,*sources.values(),jpeg/'include/jpeglib.h',jpeg/'lib/libjpeg.so.62.4.0']}
    e=Experiment('I5','encoder-mathematical-variant-build','rocm-build',sources=[__file__,*[ROOT/n for n in deps]])
    write(e.path/'backend.observed.json',capture());results={};checks=[]
    for kind,source in sources.items():
        binary=e.path/kind
        rc=e.command(['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-I'+str(folder),'-I'+str(jpeg/'include'),'-x','hip',str(source),'-o',str(binary),'-L'+str(core/'lib'),'-L'+str(jpeg/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-Wl,-rpath,'+str(jpeg/'lib'),'-lamdhip64','-ljpeg'],'build-'+kind)
        checks.append(dict(check='build-'+kind,passed=rc==0));results[kind]=dict(binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary) if binary.exists() else None)
    status='BUILT' if all(c['passed'] for c in checks) else 'BUILD_ERROR'
    row=dict(status=status,checks=checks,**results['sample'],probe=results['probe'],dependencies=deps,experiment_id=e.id,scope='Isolated rational color, exact DC, nearest ties-away; production source unchanged.')
    write(e.path/'build.json',row);row['evidence']=e.finish('EXECUTED' if status=='BUILT' else 'BUILD_ERROR');write(ROOT/'migration/reports/image-encoder-math-candidate-build.json',row)
    record('IMG-01','数学合同隔离候选及实际变换探针构建：'+status+'；颜色使用有理数整数计算，DC精确1/8，尚未接入正式入口。',[row['evidence']]);print(status);return int(status!='BUILT')

if __name__=='__main__':raise SystemExit(main())
