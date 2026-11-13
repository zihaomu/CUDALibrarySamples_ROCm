#!/usr/bin/env python3
"""Prove actual libjpeg recovery warnings cannot qualify truncated products."""
import json
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_encoder_math_binding import cpu_binding
from image_jpeg_reference_modes import loaded_library_check

def main():
    bp=ROOT/'migration/reports/image-encoder-math-reference-build.json';build=json.loads(bp.read_text());cpu_binding(build)
    runs=ROOT/'migration/reports/image-encoder-math-amd.json';row=json.loads(runs.read_text())[0];source=ROOT/row['products'][0]['path']
    if digest(source)!=row['products'][0]['sha256']:raise ValueError('product drift')
    data=source.read_bytes();rows=[]
    for name,value,want in [('complete',data,0),('missing-EOI',data[:-2],1),('truncated-entropy',data[:-20]+b'\xff\xd9',1)]:
        e=Experiment('I5','encoder-strict-CPU-truncation-controls','CPU-negative',case=name,sources=[__file__,bp,runs,source,ROOT/'tools/moat/image_encoder_math_binding.py',ROOT/'tools/moat/image_jpeg_reference_modes.py',ROOT/'rocm/probes/image/jpeg_cpu_coefficients_strict.cpp',ROOT/build['library']])
        path=e.path/'input.jpg';path.write_bytes(value);rc=e.command([str(ROOT/build['binary']),str(path)],'strict-full-coefficient-read')
        checks=[dict(check='expected-return-code',passed=rc==want),loaded_library_check(e,e.commands[-1],dict(dependencies={build['library']:build['library_sha256']}))]
        stderr=(e.path/e.commands[-1]['stderr']).read_text()
        if want:checks.append(dict(check='truncation-or-recovery-reported',passed='Premature' in stderr or 'recovery warning' in stderr or 'Corrupt' in stderr))
        status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';result=dict(case=name,status=status,checks=checks,input_sha256=digest(path),evidence_references=[build['evidence'],row['evidence']])
        write(e.path/'result.json',result);result['evidence']=e.finish('EXPECTED_REJECTION' if status=='PASSED' and want else 'PASSED' if status=='PASSED' else 'VALIDATOR_GAP',dict(status=status,checks=checks));rows.append(result)
        write(ROOT/'migration/reports/image-encoder-strict-decoder-negatives.json',rows)
        record('IMG-01','实际CPU零警告解码 '+name+'：'+status+'；截断不得因可恢复系数而通过。',[result['evidence']]);print(name,status)
    return int(any(r['status']!='PASSED' for r in rows))

if __name__=='__main__':raise SystemExit(main())
