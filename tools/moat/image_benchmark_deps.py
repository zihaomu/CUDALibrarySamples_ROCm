#!/usr/bin/env python3
"""Stage the same pinned OpenCV C++ build used by the native 5090 benchmark."""
import json,os
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def main():
    native=json.loads((ROOT/'migration/reports/image-I3-native-OpenCV.json').read_text())
    receipt=native['receipt'];prefix=ROOT/'build/image-opencv-4.12'
    prefix.mkdir(parents=True,exist_ok=True)
    e=Experiment('I3','benchmark-matched-private-OpenCV-4.12','rocm-setup',
                 sources=[__file__,ROOT/'migration/reports/image-I3-native-OpenCV.json'])
    source=receipt['source']['prefix']
    rc=e.command(['scp','-r',*[f'nvidia-5090x2:{source}/{name}' for name in ['include','lib','share']],str(prefix)],
                 'copy-exact-native-OpenCV-prefix',timeout=240)
    checks=[dict(check='remote-copy',passed=rc==0),
            dict(check='pinned-source-commit',passed=receipt['source']['commit']=='49486f61fb25722cbcf586b7f4320921d46fb38e')]
    mismatches=[]
    for name,identity in receipt['files'].items():
        path=prefix/name
        if not path.is_file() or path.stat().st_size!=identity['bytes'] or digest(path)!=identity['sha256']:
            mismatches.append(name)
    checks.append(dict(check='all-200-native-matched-files',passed=len(receipt['files'])==200 and not mismatches,
                       mismatches=mismatches))
    argv=['/home/zihaomu/zihaomu_workspace/rocm10-launch.sh','env',
          'ROCR_VISIBLE_DEVICES=3','HIP_VISIBLE_DEVICES=0',
          'LD_LIBRARY_PATH='+str(prefix/'lib'),'ldd',str(prefix/'lib/libopencv_imgproc.so.4.12.0')]
    if rc==0:rc=e.command(argv,'real-ROCm10-container-C++-loader',env=dict(os.environ,HIP_VISIBLE_DEVICES='2'))
    log=e.path/'logs/0002-real-ROCm10-container-C++-loader.stdout.log'
    loader=log.read_text() if log.is_file() else ''
    checks.append(dict(check='real-ROCm10-loader-resolves-minimal-core-imgproc',
                       passed=rc==0 and 'not found' not in loader and 'libopencv_core.so.412' in loader))
    status='READY' if all(c['passed'] for c in checks) else 'FAILED'
    result=dict(status=status,source=receipt['source'],prefix=str(prefix.relative_to(ROOT)),
                files_checked=len(receipt['files']),checks=checks)
    write(e.path/'results.json',result)
    result['evidence']=e.finish('PASSED' if status=='READY' else 'DEPENDENCY_FAILED',dict(status=status,checks=checks))
    write(ROOT/'migration/reports/image-I3-rocm-OpenCV.json',result)
    record('I3','ROCm10镜像使用与5090原生benchmark相同OpenCV 4.12私有构建；200文件SHA/大小及实际容器动态加载：'+status+'。',[result['evidence']])
    print(status,result['evidence'])
    return int(status!='READY')

if __name__=='__main__':raise SystemExit(main())
