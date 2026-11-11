#!/usr/bin/env python3
"""Build unmodified nvJPEG2000 originals and run their complete bundled setup check."""
import json, shlex, tarfile
from experiment import ROOT, Experiment, write, digest
from image_progress import record

def main():
    module=ROOT/'nvJPEG2000'
    sources=[__file__]+[p for p in module.rglob('*') if p.is_file() and (p.suffix in {'.h','.cpp','.sh'} or p.name=='CMakeLists.txt')]
    e=Experiment('I0','nvJPEG2000-original-build-and-examples','cuda-baseline',sources=sources)
    sdk=next(x for x in json.loads((ROOT/'migration/reports/image-I0-native-private-SDKs.json').read_text()) if x['SDK']=='nvjpeg2000')
    prefix=sdk['remote']+'/libnvjpeg_2k-linux-x86_64-'+sdk['identity']['version']+'_'+sdk['identity']['variant']+'-archive'
    remote='/tmp/'+e.id
    bundle=e.path/'originals.tar.gz'
    with tarfile.open(bundle,'w:gz') as tar:tar.add(module,arcname='nvJPEG2000')
    commands=[(['ssh','nvidia-5090x2',shlex.join(['mkdir','-p',remote])],'prepare'),
              (['scp',str(bundle),'nvidia-5090x2:'+remote+'/originals.tar.gz'],'upload-original-tree'),
              (['ssh','nvidia-5090x2',shlex.join(['tar','-xzf',remote+'/originals.tar.gz','-C',remote])],'unpack-original-tree'),
              (['ssh','nvidia-5090x2',shlex.join(['cmake','-S',remote+'/nvJPEG2000','-B',remote+'/build','-DCMAKE_BUILD_TYPE=Release',
                  '-DCMAKE_CUDA_COMPILER=/usr/local/cuda-13.4/bin/nvcc','-DCMAKE_CUDA_ARCHITECTURES=120',
                  '-DNVJPEG2K_PATH='+prefix,'-DCMAKE_INSTALL_PREFIX='+remote+'/install'])],'configure-original-CMake'),
              (['ssh','nvidia-5090x2',shlex.join(['cmake','--build',remote+'/build','--parallel','4'])],'build-four-unmodified-originals'),
              (['ssh','nvidia-5090x2',shlex.join(['cmake','--install',remote+'/build'])],'install-originals-private-prefix')]
    rc=0
    for command,phase in commands:
        rc=e.command(command,phase,timeout=300)
        if rc:break
    if rc==0:
        # The original runner accepts package/lib/<CUDA major>; the tarball uses package/lib.
        code="""import pathlib,json,hashlib,subprocess
root=pathlib.Path(REMOTE);lib=root/'package/lib';lib.mkdir(parents=True,exist_ok=True);(lib/'13').symlink_to(SDKLIB,target_is_directory=True)
files=list((root/'install/bin').iterdir());print(json.dumps({str(p):dict(sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),ldd=subprocess.run(['ldd',str(p)],capture_output=True,text=True).stdout) for p in files}))
""".replace('REMOTE',repr(remote)).replace('SDKLIB',repr(prefix+'/lib'))
        rc=e.command(['ssh','nvidia-5090x2',shlex.join(['python3','-c',code])],'actual-binary-and-loader-identity')
    if rc==0:
        rc=e.command(['ssh','nvidia-5090x2',shlex.join(['env','CUDA_VISIBLE_DEVICES=1',remote+'/install/run_examples.sh',remote+'/package','13'])],
                     'actual-original-file-setup-check-including-HTJ2K',timeout=600)
    if rc==0:
        rc=e.command(['scp','-r','nvidia-5090x2:'+remote+'/install/output',str(e.path/'outputs')],'collect-complete-native-output',timeout=300)
    outputs={str(p.relative_to(e.path)):dict(sha256=digest(p),bytes=p.stat().st_size) for p in (e.path/'outputs').rglob('*') if p.is_file()}
    result=dict(status='EXECUTED' if rc==0 else 'FAILED',return_code=rc,remote=remote,SDK=sdk['identity'],
                original_sources={str(p.relative_to(ROOT)):digest(p) for p in sources[1:]},outputs=outputs,
                scope='Original bundled native setup baseline. NLT3/FP/YUV/type/quality cases and AMD qualification are separate pending contracts.')
    write(e.path/'native-result.json',result)
    ref=e.finish('OBSERVED' if rc==0 else 'NATIVE_HARNESS_NONZERO')
    write(ROOT/'migration/reports/image-I0-native-JPEG2000-originals.json',dict(**result,evidence=ref))
    record('I0','nvJPEG2000四个原始入口的私有SDK构建/原仓库完整setup baseline：'+result['status']+'；包括实际文件decode、pipeline、tile ROI、classic/HT可逆编码与原图文件逐字节回环检查。其它类型分支尚未验收。',[ref])
    print(rc,ref)
    return rc

if __name__=='__main__':raise SystemExit(main())
