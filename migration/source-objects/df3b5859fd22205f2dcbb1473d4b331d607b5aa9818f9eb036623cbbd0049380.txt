#!/usr/bin/env python3
"""Observe the locked backend inside the process environment that will execute it."""
import argparse
import ctypes
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/migration'))


def capture():
    from device_guard import allowed_devices
    devices = allowed_devices()
    import _rocm_sdk_core
    core = Path(_rocm_sdk_core.__file__).parent
    hip = ctypes.CDLL(str(core/'lib/libamdhip64.so.7'))
    versions = {}
    for name in ['hipRuntimeGetVersion', 'hipDriverGetVersion']:
        n = ctypes.c_int()
        rc = getattr(hip, name)(ctypes.byref(n))
        versions[name] = dict(status=rc, value=n.value)
    for d in devices:
        value = ctypes.create_string_buffer(16)
        rc = hip.hipDeviceGetUuid(value, d['logical_id'])
        d['uuid'] = value.raw.hex() if rc == 0 else None
    packages = {d.metadata['Name']: d.version for d in importlib.metadata.distributions()
                if d.metadata['Name'].lower().startswith(('rocm', 'torch', 'triton'))}
    loaded = sorted(set(line.split()[-1] for line in Path('/proc/self/maps').read_text().splitlines()
                        if '.so' in line and ('rocm' in line or 'libamdhip' in line)))
    return dict(hostname=platform.node(), platform=platform.platform(),
                image_id=os.environ.get('DEEPINFER_IMAGE_ID'),
                rocm_release=os.environ.get('DEEPINFER_ROCM_RELEASE'),
                visible_devices=os.environ.get('HIP_VISIBLE_DEVICES'), devices=devices,
                versions=versions, packages=packages,
                loaded_libraries=[dict(path=p,sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
                                  for p in loaded if Path(p).is_file()])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = capture()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
