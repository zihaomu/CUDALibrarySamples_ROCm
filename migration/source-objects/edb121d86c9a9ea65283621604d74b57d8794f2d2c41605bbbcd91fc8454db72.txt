#!/usr/bin/env python3
"""Verify actual benchmark executable and private OpenCV shared objects before running."""
import json,re
from pathlib import Path
from experiment import ROOT,digest,write

def inspect(e,build):
    native=json.loads((ROOT/'migration/reports/image-I3-native-OpenCV.json').read_text())
    receipt=native['receipt']['files']
    opencv=ROOT/build['opencv_prefix'];library=ROOT/build['library'];binary=ROOT/build['binary']
    expected={'libimage_benchmark.so':(library,build['library_sha256']),
              'libopencv_core.so.412':(opencv/'lib/libopencv_core.so.412',receipt['lib/libopencv_core.so.412']['sha256']),
              'libopencv_imgproc.so.412':(opencv/'lib/libopencv_imgproc.so.412',receipt['lib/libopencv_imgproc.so.412']['sha256'])}
    checks=[dict(check='current-binary-sha',passed=binary.is_file() and digest(binary)==build['binary_sha256']),
            dict(check='current-GPU-library-sha',passed=library.is_file() and digest(library)==build['library_sha256']),
            dict(check='same-200-pinned-OpenCV-files',passed=len(receipt)==200 and all(
              (opencv/name).is_file() and (opencv/name).stat().st_size==identity['bytes']
              and digest(opencv/name)==identity['sha256'] for name,identity in receipt.items()))]
    rc=e.command(['ldd',str(binary)],'resolve-real-image-libraries',timeout=30) if binary.is_file() else 1
    log=e.path/'logs/0001-resolve-real-image-libraries.stdout.log'
    loader=log.read_text() if log.is_file() else ''
    checks.append(dict(check='loader-success-no-missing-library',passed=rc==0 and 'not found' not in loader))
    for soname,(path,sha) in expected.items():
      matches=re.findall(r'^\s*'+re.escape(soname)+r'\s*=>\s*(\S+)',loader,re.MULTILINE)
      resolved=Path(matches[0]) if len(matches)==1 else None
      checks.append(dict(check='actual-loaded-'+soname,passed=resolved is not None
        and resolved.resolve()==path.resolve() and path.is_file() and digest(path)==sha,
        resolved=str(resolved) if resolved else None,sha256=sha))
    result=dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,
                binary=str(binary),library=str(library),opencv_prefix=str(opencv))
    write(e.path/'loaded-libraries.json',result)
    return result
