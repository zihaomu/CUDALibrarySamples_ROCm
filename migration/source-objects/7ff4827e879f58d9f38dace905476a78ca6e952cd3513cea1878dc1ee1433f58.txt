#!/usr/bin/env python3
"""Independently decode original JP2s and quantify differences from native CUDA BMPs."""
import json
import math
from PIL import Image, features, __version__ as pillow_version
import numpy as np
from experiment import ROOT, Experiment, digest, write
from image_progress import record

PROFILE = ROOT / 'migration/rewrite/image-j2k-part1-crossdecode-profile.json'
REPORT = ROOT / 'migration/reports/image-j2k-part1-crossdecode.json'


def main():
    profile = json.loads(PROFILE.read_text())
    if profile['status'] != 'FROZEN' or len(profile['inputs']) != 3:
        raise ValueError('predeclared JP2/CUDA identities required')
    rows = []
    for item in profile['inputs']:
        source = ROOT / item['source']; native = ROOT / item['native_output']
        if digest(source) != item['source_sha256'] or digest(native) != item['native_output_sha256']:
            raise ValueError('JP2 or CUDA output identity drift')
        e = Experiment('I6', 'original-JP2-independent-OpenJPEG-vs-CUDA',
                       'CPU-reference', case=item['case'],
                       sources=[__file__, PROFILE, source, native],
                       parent=profile['evidence'].split('/')[-1])
        try:
            with Image.open(source) as image:
                image.load(); a = np.asarray(image.convert('RGB'))
                fmt = image.format; mode = image.mode; geometry = image.size
            with Image.open(native) as image:
                image.load(); b = np.asarray(image.convert('RGB'))
                native_geometry = image.size
            if a.shape != b.shape:
                metrics = dict(source_geometry=geometry, native_geometry=native_geometry,
                               exact_shape=False)
                status = 'NATIVE_MISMATCH'
            else:
                delta = np.abs(a.astype(np.int16) - b.astype(np.int16))
                squared = np.square(delta.astype(np.float64))
                mse = float(np.mean(squared))
                metrics = dict(width=geometry[0], height=geometry[1], components=3,
                               exact_shape=True, exact_rgb=bool(not np.any(delta)),
                               differing_bytes=int(np.count_nonzero(delta)),
                               max_abs=int(np.max(delta)), mean_abs=float(np.mean(delta)),
                               mse=mse, psnr_db=float('inf') if mse == 0 else
                               10 * math.log10(255 * 255 / mse),
                               source_format=fmt, source_mode=mode,
                               source_rgb_sha256=__import__('hashlib').sha256(a.tobytes()).hexdigest(),
                               cuda_rgb_sha256=__import__('hashlib').sha256(b.tobytes()).hexdigest())
                status = 'OBSERVED'
            library_paths = sorted(set(line.split()[-1] for line in
                __import__('pathlib').Path('/proc/self/maps').read_text().splitlines()
                if 'openjp2' in line and '/' in line.split()[-1]))
            libraries = [dict(path=p, sha256=digest(p)) for p in library_paths]
            checks = [dict(check='independent-JP2-decode', passed=fmt == 'JPEG2000'),
                      dict(check='native-and-independent-geometry', passed=a.shape == b.shape),
                      dict(check='lossless-native-RGB-exact-observation',
                           passed=not item['reversible'] or metrics.get('exact_rgb', False))]
            if item['reversible'] and not metrics.get('exact_rgb', False):
                status = 'NATIVE_MISMATCH'
            write(e.path / 'library.json', dict(pillow=pillow_version,
                pillow_openjpeg_version=features.version('jpg_2000'), loaded_openjp2=libraries))
        except Exception as error:
            metrics = dict(error=repr(error)); checks = [dict(check='independent-JP2-decode',
                                                            passed=False, error=repr(error))]
            status = 'RUNTIME_ERROR'
        result = dict(case=item['case'], status=status, checks=checks, metrics=metrics,
                      comparison_scope='CPU OpenJPEG vs original CUDA output, observation only',
                      experiment_id=e.id)
        write(e.path / 'comparison.json', result)
        result['evidence'] = e.finish(status, dict(status=status, checks=checks), metrics=metrics)
        rows.append(result); write(REPORT, rows)
        record('I6', '原始 JP2 '+item['case']+' OpenJPEG CPU 与原生 CUDA BMP 全像素观测：'+status+
               '，maxAbs='+str(metrics.get('max_abs'))+'；不计 AMD 支持。', [result['evidence']])
        print(item['case'], status, metrics.get('max_abs'), metrics.get('psnr_db'), flush=True)
    return int(any(r['status'] == 'RUNTIME_ERROR' for r in rows))


if __name__ == '__main__':
    raise SystemExit(main())
