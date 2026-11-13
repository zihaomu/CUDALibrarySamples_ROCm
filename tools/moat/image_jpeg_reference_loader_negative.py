#!/usr/bin/env python3
"""Ensure a valid decode through a different libjpeg cannot qualify."""
import json
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_jpeg_reference_modes import PROFILE,current,loaded_library_check

def main():
    reports,builds=current();build=builds[0]
    alternate=(ROOT/'build/libjpeg/libjpeg.so.62').resolve()
    expected=(ROOT/'build/cpu-codecs/lib/libjpeg.so.62.4.0').resolve()
    if not alternate.is_file() or digest(alternate)==digest(expected):raise ValueError('distinct real CPU library required')
    case=json.loads(PROFILE.read_text())['cases'][0];source=ROOT/case['path']
    e=Experiment('I5','CPU-reference-actual-loader-negative','CPU-negative',sources=[__file__,ROOT/'tools/moat/image_jpeg_reference_modes.py',PROFILE,*reports,source,alternate,*[ROOT/n for n in build['dependencies']]])
    checks=[];receipts=[]
    for label,prefix,want in [('positive',[],True),('wrong-library',['env','LD_LIBRARY_PATH='+str(alternate.parent)],False)]:
        output=e.path/(label+'.ycc');rc=e.command([*prefix,str(ROOT/build['binary']),str(source),str(output)],label+'-CPU-decode')
        receipt=loaded_library_check(e,e.commands[-1],build);receipts.append(dict(case=label,receipt=receipt))
        checks.append(dict(check=label+'-runs-complete-decode',passed=rc==0 and output.stat().st_size==case['width']*case['height']*3))
        checks.append(dict(check=label+'-identity-gate',passed=receipt['passed'] is want))
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(status=status,checks=checks,receipts=receipts)
    write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'VALIDATOR_GAP',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-jpeg-reference-loader-negative.json',row)
    record('IMG-01','CPU参考实际加载身份反向检查：'+status+'；正常库被接受，LD_LIBRARY_PATH替换为另一真实libjpeg即使完整解码也被拒绝。',[row['evidence']]);print(status)
    return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
