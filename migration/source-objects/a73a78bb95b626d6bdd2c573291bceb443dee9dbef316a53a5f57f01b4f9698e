#!/usr/bin/env python3
"""Strict input, case coverage and full-byte checks for image stage observations."""
from collections import Counter
import json
import numpy as np
from experiment import digest

def coverage(rows,expected):
    actual=Counter(r.get('case') for r in rows)
    required=Counter(r['case'] for r in expected)
    return dict(check='complete-unique-case-coverage',passed=bool(required) and actual==required and all(n==1 for n in actual.values()),
                actual=dict(actual),required=dict(required))

def file_set(directory,names):
    actual={p.name for p in directory.iterdir()} if directory.is_dir() else set()
    valid=directory.is_dir() and actual==set(names) and all((directory/n).is_file() for n in names)
    return dict(check='exact-output-file-set',passed=valid,actual=sorted(actual),required=sorted(names))

def fixture_identity(fixture,sha):
    manifest=fixture/'manifest.json'
    if not manifest.is_file() or digest(manifest)!=sha:return dict(check='frozen-input-identity',passed=False)
    try:
        files=json.loads(manifest.read_text())['files']
        valid=bool(files) and all((fixture/name).is_file() and (fixture/name).stat().st_size==r['bytes'] and digest(fixture/name)==r['sha256'] for name,r in files.items())
    except (KeyError,ValueError,OSError):valid=False
    return dict(check='frozen-input-identity',passed=valid)

def array_check(path,expected,sha):
    nbytes=int(expected.size*expected.dtype.itemsize)
    actual_bytes=path.stat().st_size if path.is_file() else None
    result=dict(check=path.stem,passed=False,elements=int(expected.size),expected_bytes=nbytes,actual_bytes=actual_bytes,mismatches=None)
    if actual_bytes!=nbytes:return result
    actual_sha=digest(path);result['output_sha256']=actual_sha
    if not isinstance(sha,str) or actual_sha!=sha:return result
    actual=np.fromfile(path,expected.dtype).reshape(expected.shape)
    mismatch=int(np.count_nonzero(actual!=expected))
    result.update(passed=mismatch==0,mismatches=mismatch)
    return result
