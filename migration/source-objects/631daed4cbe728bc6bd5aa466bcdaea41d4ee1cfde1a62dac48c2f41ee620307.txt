#!/usr/bin/env python3
"""Inspect the frozen Q1 gradient failure with independent CPU coefficients."""
import json
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_jpeg_reference_modes import loaded_library_check

def main():
    case='gradient-q1-s2-opt0';paths={};reports=[]
    for side in ['amd','native','cpu']:
        report=ROOT/f'migration/reports/image-encoder-quality-{side}.json';reports.append(report)
        row=next(r for r in json.loads(report.read_text()) if r['case']==case)
        paths[side]=ROOT/row['evidence']/('cpu.jpg' if side=='cpu' else 'products/0.jpg')
    source=ROOT/'rocm/probes/image/jpeg_cpu_coefficients.cpp';jpeg=ROOT/'build/cpu-codecs';lib=jpeg/'lib/libjpeg.so.62.4.0'
    e=Experiment('I5','encoder-Q1-gradient-coefficient-diagnosis','CPU-reference',sources=[__file__,source,ROOT/'tools/moat/image_jpeg_reference_modes.py',jpeg/'include/jpeglib.h',lib,*paths.values()])
    binary=e.path/'coefficients';rc=e.command(['c++','-std=c++17','-O2','-I'+str(jpeg/'include'),str(source),'-o',str(binary),'-L'+str(jpeg/'lib'),'-Wl,-rpath,'+str(jpeg/'lib'),'-ljpeg','-ldl'],'build-coefficient-reference')
    checks=[dict(check='reference-build',passed=rc==0)];data={};differences={}
    try:
        for side,path in paths.items():
            rc=e.command([str(binary),str(path)],side+'-CPU-coefficients');checks.append(dict(check=side+'-coefficient-command',passed=rc==0))
            identity=loaded_library_check(e,e.commands[-1],dict(dependencies={str(lib.relative_to(ROOT)):digest(lib)}));identity['check']+='-'+side;checks.append(identity)
            data[side]=json.loads((e.path/e.commands[-1]['stdout']).read_text())
        for side in ['cpu','native']:
            differences[side]=[]
            for c,(a,b) in enumerate(zip(data['amd']['components'],data[side]['components'])):
                values=[dict(x=(i//64)%a['width_blocks'],y=(i//64)//a['width_blocks'],frequency=i%64,amd=x,reference=y)
                    for i,(x,y) in enumerate(zip(a['coefficients'],b['coefficients'])) if x!=y]
                differences[side].append(dict(component=c,different_coefficients=len(values),positions=values))
    except Exception as error:checks.append(dict(check='inspection-exception',passed=False,error=repr(error)))
    status='OBSERVED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(status=status,checks=checks,differences=differences,input_jpegs={s:dict(path=str(p.relative_to(ROOT)),sha256=digest(p)) for s,p in paths.items()})
    write(e.path/'result.json',row);row['evidence']=e.finish('OBSERVED' if status=='OBSERVED' else 'PROBE_FAILED',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-Q1-diagnosis.json',row)
    record('IMG-01','Q1渐变局部失败的独立CPU系数诊断：'+status+'；逐分量/块/频率差异保留，数值门槛及生产算法未变。',[row['evidence']]);print(status)

if __name__=='__main__':main()
