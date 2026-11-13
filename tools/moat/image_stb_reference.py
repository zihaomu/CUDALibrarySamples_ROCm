#!/usr/bin/env python3
"""Pin and build a second CPU JPEG reference for the 65535 axis boundary."""
import argparse,json,shutil
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

COMMIT='9600522de53973336fa033a289858a4354cbb04c'
DIRECTORY=ROOT/'build/deps'/('stb-reference-'+COMMIT[:12])
LOCK=ROOT/'migration/environments/stb-image-reference.lock.json'
BUILD=ROOT/'migration/reports/image-stb-reference-build.json'
SOURCE=ROOT/'rocm/probes/image/stb_cpu_reference.cpp'

def prepare():
    if LOCK.exists():
        old=json.loads(LOCK.read_text())
        if old['commit']!=COMMIT or any(digest(ROOT/p)!=sha for p,sha in old['files'].items()):raise ValueError('pinned CPU reference drift')
        return
    e=Experiment('I5','independent-CPU-stb-reference-source','CPU-dependency',sources=[__file__]);codes=[];files={}
    for name in ['stb_image.h','LICENSE']:
        path=e.path/name;url=f'https://raw.githubusercontent.com/nothings/stb/{COMMIT}/{name}'
        codes.append(e.command(['curl','--fail','--location','--retry','2',url,'--output',str(path)],'fetch-pinned-'+name,timeout=120))
        if codes[-1]:break
        files[name]=digest(path)
    if any(codes):
        evidence=e.finish('COMMAND_FAILED');record('IMG-01','独立CPU JPEG参考获取失败；保留下载命令与错误，不改现有CPU库。',[evidence]);return 1
    DIRECTORY.mkdir(parents=True,exist_ok=True)
    for name in files:shutil.copyfile(e.path/name,DIRECTORY/name)
    value=dict(status='PINNED',repository='https://github.com/nothings/stb',commit=COMMIT,
        files={str((DIRECTORY/name).relative_to(ROOT)):sha for name,sha in files.items()},
        license='Unmodified upstream dual public-domain/MIT source; MIT alternative retained with LICENSE.',
        scope='CPU-only independent reference. No stb entropy/decode linked into production HIP executables.')
    write(e.path/'lock.json',value);value['evidence']=e.finish('OBSERVED');write(LOCK,value)
    record('IMG-01','新增独立CPU参考stb_image源码锁定 '+COMMIT+'；头文件/许可证SHA完整保留，只供CPU验收，生产HIP路径不引入CPU熵解码。',[str(LOCK.relative_to(ROOT)),value['evidence']]);print(value['evidence'])

def build():
    lock=json.loads(LOCK.read_text())
    if lock['commit']!=COMMIT or any(digest(ROOT/p)!=sha for p,sha in lock['files'].items()):raise ValueError('reference dependency drift')
    deps={**lock['files'],str(SOURCE.relative_to(ROOT)):digest(SOURCE),str(LOCK.relative_to(ROOT)):digest(LOCK)}
    e=Experiment('I5','independent-CPU-stb-reference-build','CPU-build',sources=[__file__,*[ROOT/p for p in deps]]);binary=e.path/'stb-reference'
    compiler=e.command(['c++','--version'],'CPU-compiler-identity')
    rc=e.command(['c++','-std=c++17','-O2','-I'+str(DIRECTORY),str(SOURCE),'-o',str(binary)],'build-independent-CPU-JPEG-reference')
    checks=[dict(check='CPU-build-success',passed=rc==compiler==0)]
    if not rc:
        ld=e.command(['ldd',str(binary)],'CPU-reference-linked-libraries')
        text=(e.path/'logs/0003-CPU-reference-linked-libraries.stdout.log').read_text().lower()
        checks.append(dict(check='no-HIP-CUDA-or-libjpeg-decoder-link',passed=ld==0 and all(name not in text for name in ['libamdhip','libcuda','libjpeg','libnvjpeg'])))
    status='BUILT' if all(c['passed'] for c in checks) else 'BUILD_ERROR';row=dict(status=status,binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary) if binary.exists() else None,dependencies=deps,checks=checks,experiment_id=e.id)
    write(e.path/'build.json',row);row['evidence']=e.finish('EXECUTED' if status=='BUILT' else 'BUILD_ERROR');write(BUILD,row)
    record('IMG-01','第二独立CPU JPEG参考构建：'+status+'；编译器、链接依赖、源码和binary SHA已保存，仍需实际解码验证。',[row['evidence']]);print(status);return int(status!='BUILT')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','build']);args=parser.parse_args();raise SystemExit(globals()[args.action]())
