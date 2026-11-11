#!/usr/bin/env python3
"""Download or verify private NVIDIA SDKs; seal failed installation attempts."""
import json,shutil,tarfile
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def prefix_checks(prefix,previous,version,variant,sha):
    errors=[]
    if not previous or previous.get('version')!=version or previous.get('variant')!=variant or previous.get('vendor_sha256')!=sha:
        return ['no matching previously verified package identity']
    files=previous.get('files',{})
    if not files:return ['no previous file inventory']
    for name,row in files.items():
        p=prefix/name
        if not p.is_file() or p.stat().st_size!=row['bytes'] or digest(p)!=row['sha256']:errors.append(name)
    actual={str(p.relative_to(prefix)) for p in prefix.rglob('*') if p.is_file() and (p.suffix in ['.h','.txt'] or '.so' in p.name)}
    if actual!=set(files):errors.append('SDK file inventory differs')
    return errors

def main():
    manifests=json.loads((ROOT/'migration/reports/image-I0-SDK-manifests.json').read_text())['results']
    report=ROOT/'migration/reports/image-I0-private-SDKs.json'
    old=json.loads(report.read_text()) if report.exists() else []
    rows={r['SDK']:r for r in old};failed=False
    for name,key,variant in [('nvjpeg2000','libnvjpeg_2k','cuda13'),('nppplus','libnpp_plus','cuda12')]:
        package=manifests[name]['manifest'][key];item=package['linux-x86_64'][variant]
        url='https://developer.download.nvidia.com/compute/'+name+'/redist/'+item['relative_path']
        e=Experiment('I0','image-private-'+name+'-SDK','host-download',sources=[__file__,ROOT/'migration/reports/image-I0-SDK-manifests.json'])
        prefix=ROOT/'build/image-cuda-sdk'/name;previous=rows.get(name);valid=False;reason=None
        row=dict(SDK=name,version=package['version'],variant=variant,url=url,vendor_sha256=item['sha256'],prefix=str(prefix.relative_to(ROOT)))
        try:
            if prefix.exists():
                errors=prefix_checks(prefix,previous,package['version'],variant,item['sha256'])
                if errors:raise RuntimeError('existing SDK prefix refused: '+repr(errors))
                row=dict(previous,status='VERIFIED_REUSE',archive_evidence=previous.get('archive_evidence',previous['evidence']))
                valid=True
            else:
                # Preserve vendor payload only in raw evidence, never in Git archives.
                archive=e.path/'sdk.bin'
                rc=e.command(['curl','--fail','--location','--connect-timeout','15','--max-time','600','--retry','1','--output',str(archive),url],'official-archive-download',timeout=650)
                if rc or not archive.is_file() or archive.stat().st_size!=int(item['size']) or digest(archive)!=item['sha256']:
                    raise RuntimeError('official download failed or size/SHA mismatch')
                unpack=ROOT/'build/image-SDK-unpack'/e.id;unpack.mkdir(parents=True)
                with tarfile.open(archive,'r:xz') as tar:tar.extractall(unpack,filter='data')
                children=list(unpack.iterdir());sdk=children[0] if len(children)==1 else unpack
                prefix.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(sdk,prefix)
                files={str(p.relative_to(prefix)):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in prefix.rglob('*') if p.is_file() and (p.suffix in ['.h','.txt'] or '.so' in p.name)}
                if not files:raise RuntimeError('empty SDK installation')
                row.update(status='VERIFIED_DOWNLOAD',actual_sha256=digest(archive),archive_file='sdk.bin',files=files);valid=True
        except Exception as error:
            reason=repr(error);row.update(status='SDK_UNAVAILABLE',error=reason,previous_verified_identity=previous);failed=True
        write(e.path/'sdk-identity.json',row)
        ref=e.finish('OBSERVED' if valid else 'SDK_UNAVAILABLE',reason=reason)
        if valid and row['status']=='VERIFIED_DOWNLOAD':row['archive_evidence']=ref
        row['evidence']=ref;rows[name]=row;write(report,list(rows.values()))
        record('I0',name+' 私有SDK安装/重用：'+row['status']+'；现有prefix必须逐文件匹配，所有失败封存。',[ref])
        print(name,row['status'],flush=True)
    return int(failed)

if __name__=='__main__':raise SystemExit(main())
