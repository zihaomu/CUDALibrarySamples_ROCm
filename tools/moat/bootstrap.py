#!/usr/bin/env python3
"""Restore or validate every part of the pinned local control checkout."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def git(control,*args,check=True):
    return subprocess.run(['git',*map(str,args)],cwd=control,check=check,capture_output=True,text=True)

def validate_existing(root=ROOT):
    lock=json.loads((root/'migration/moat/lock.json').read_text());control=(root/lock['control_checkout']).resolve()
    for path,key in [(lock['skill'],'skill_sha256'),('utils/moatlib.py','state_library_sha256')]:
        if hashlib.sha256((control/path).read_bytes()).hexdigest()!=lock[key]:raise RuntimeError('Pinned source mismatch: '+path)
    git(control,'merge-base','--is-ancestor',lock['upstream_commit'],'HEAD')
    if git(control,'branch','--show-current').stdout.strip()!='port/'+lock['project']:raise RuntimeError('Unexpected control branch')
    origin=git(control,'remote','get-url','origin').stdout.strip()
    if (control/origin).resolve()!=(control/'.git/project-sync.git').resolve():raise RuntimeError('Control origin must be the local bare synchronization repository')
    project=control/'projects'/lock['project'];src=project/'src'
    if not (project/'status.json').is_file() or src.resolve()!=root.resolve():raise RuntimeError('Missing project state or mismatched source checkout')
    return control

def ensure(root=ROOT):
    lock=json.loads((root/'migration/moat/lock.json').read_text());control=(root/lock['control_checkout']).resolve();branch='port/'+lock['project']
    fresh=not control.exists()
    if fresh:subprocess.run(['git','clone','--no-checkout',lock['upstream_url'],str(control)],check=True)
    if not (control/'.git').is_dir():raise RuntimeError('Existing control path is not a Git checkout')
    if git(control,'cat-file','-e',lock['upstream_commit']+'^{commit}',check=False).returncode:git(control,'fetch',lock['upstream_url'],lock['upstream_commit'])
    if fresh:git(control,'checkout','--detach',lock['upstream_commit'])
    current=git(control,'branch','--show-current').stdout.strip();project=control/'projects'/lock['project']
    if current!=branch:
        if git(control,'status','--porcelain','--untracked-files=no').stdout:raise RuntimeError('Do not replace modified control files')
        if not (project/'status.json').exists():
            bundle=root/'migration/moat/control.bundle'
            if not bundle.exists():raise RuntimeError('Saved project control bundle is required')
            if git(control,'show-ref','--verify','refs/heads/'+branch,check=False).returncode:git(control,'fetch',bundle,branch+':refs/heads/'+branch)
        git(control,'checkout',branch)
    if not (project/'status.json').is_file():raise RuntimeError('Expected branch has no project state; refusing to invent it')
    remotes=git(control,'remote').stdout.split()
    if 'origin' in remotes:
        url=git(control,'remote','get-url','origin').stdout.strip()
        if url.rstrip('/').removesuffix('.git')==lock['upstream_url'].rstrip('/'):
            if 'upstream' in remotes:raise RuntimeError('Ambiguous upstream/origin remotes')
            git(control,'remote','rename','origin','upstream');remotes.remove('origin')
        elif (control/url).resolve()!=(control/'.git/project-sync.git').resolve():raise RuntimeError('Unexpected origin; refusing public synchronization')
    bare=control/'.git/project-sync.git'
    if not bare.exists():git(control,'init','--bare',bare)
    if 'origin' not in remotes:git(control,'remote','add','origin','.git/project-sync.git')
    git(control,'push','-u','origin',branch)
    if git(control,'show-ref','--verify','refs/remotes/origin/main',check=False).returncode:git(control,'push','origin',lock['upstream_commit']+':refs/heads/main')
    subprocess.run(['bash','utils/setup_git.sh'],cwd=control,check=True)
    src=project/'src'
    if src.is_symlink() or src.exists():
        if src.resolve()!=root.resolve():raise RuntimeError('Existing project source link points to another checkout')
    else:src.symlink_to(root,target_is_directory=True)
    return validate_existing(root)

if __name__=='__main__':print('Verified pinned MOAT control checkout:',ensure())
