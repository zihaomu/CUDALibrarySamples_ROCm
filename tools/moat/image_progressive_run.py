#!/usr/bin/env python3
"""Run the I4 GPU progressive JPEG prototype against pinned CPU pixels."""
import json
import math

import numpy as np

from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

PROFILE = ROOT / 'migration/rewrite/image-progressive-gpu-profile.json'
BUILD = ROOT / 'migration/reports/image-progressive-build.json'
REPORT = ROOT / 'migration/reports/image-progressive-runs.json'


def main():
    profile = json.loads(PROFILE.read_text())
    build = json.loads(BUILD.read_text())
    if build['status'] != 'BUILT' or any(
            digest(ROOT / name) != sha for name, sha in build['dependencies'].items()):
        raise ValueError('current HIP progressive build required')
    binary = ROOT / build['binary']
    if digest(binary) != build['binary_sha256']:
        raise ValueError('binary changed')
    rows = []
    for item in profile['inputs']:
        if digest(ROOT / item['path']) != item['sha256']:
            raise ValueError('input changed: ' + item['path'])
        name = item['path'].split('/')[-1]
        e = Experiment('I4', 'progressive-JPEG-GPU-pixel-synthesis',
                       'rocm-prototype', case=name,
                       sources=[__file__, PROFILE, BUILD, ROOT / item['path'],
                                ROOT / 'rocm/probes/image/jpeg_progressive_gpu.hip'],
                       parent=build['experiment_id'])
        write(e.path / 'backend.observed.json', capture())
        gpu = e.path / 'gpu.rgb'; cpu = e.path / 'cpu.rgb'
        rc = e.command([str(binary), str(ROOT / item['path']), str(gpu), str(cpu)],
                       'actual-progressive-GPU-IDCT-and-RGB', timeout=300)
        stdout = (e.path / 'logs/0001-actual-progressive-GPU-IDCT-and-RGB.stdout.log').read_text()
        metadata = json.loads(stdout.splitlines()[-1]) if rc == 0 else {}
        valid_size = (rc == 0 and gpu.is_file() and cpu.is_file() and
            gpu.stat().st_size == cpu.stat().st_size ==
            metadata.get('width', 0) * metadata.get('height', 0) * 3)
        max_abs = None; psnr = None; mismatched = None
        if valid_size:
            a = np.fromfile(gpu, np.uint8).astype(np.int16)
            b = np.fromfile(cpu, np.uint8).astype(np.int16)
            delta = np.abs(a - b)
            max_abs = int(delta.max())
            mse = float(np.mean((a - b).astype(np.float64) ** 2))
            psnr = float('inf') if mse == 0 else 10 * math.log10(255 * 255 / mse)
            mismatched = int(np.count_nonzero(delta))
        gates = profile['gates']
        checks = [dict(check='actual-HIP-command-exit-zero', passed=rc == 0),
                  dict(check='full-expected-RGB-byte-count', passed=valid_size),
                  dict(check='declared-GPU-IDCT-and-color-no-CPU-pixel-fallback',
                       passed=metadata.get('gpu_idct') is True and
                              metadata.get('gpu_chroma_rgb') is True and
                              metadata.get('cpu_pixel_fallback') is False),
                  dict(check='fixed-maxAbs-RGB', passed=valid_size and max_abs <= gates['max_abs_per_channel'],
                       measured=max_abs, limit=gates['max_abs_per_channel']),
                  dict(check='fixed-min-PSNR-RGB', passed=valid_size and psnr >= gates['min_rgb_psnr_db'],
                       measured=psnr, limit=gates['min_rgb_psnr_db'])]
        status = 'PASSED' if all(c['passed'] for c in checks) else 'NUMERIC_MISMATCH'
        row = dict(input=name, status=status, return_code=rc, metadata=metadata,
                   max_abs=max_abs, psnr_db=psnr, mismatched_channels=mismatched,
                   gpu_sha256=digest(gpu) if gpu.is_file() else None,
                   cpu_sha256=digest(cpu) if cpu.is_file() else None,
                   gpu_bytes=gpu.stat().st_size if gpu.is_file() else None,
                   cpu_bytes=cpu.stat().st_size if cpu.is_file() else None,
                   checks=checks, experiment_id=e.id)
        write(e.path / 'run.json', row)
        row['evidence'] = e.finish(status if rc == 0 else 'RUNTIME_ERROR',
                                    dict(status=status, checks=checks))
        rows.append(row); write(REPORT, rows)
        record('I4', f'原始 progressive {name} GPU IDCT/色彩 vs libjpeg-turbo 非平滑参考：'
               f'maxAbs={max_abs}、PSNR={psnr} dB，{status}；GPU trace 和完整入口待验。',
               [row['evidence']])
        print(name, status, max_abs, psnr, flush=True)
    return int(any(row['status'] != 'PASSED' for row in rows))


if __name__ == '__main__':
    raise SystemExit(main())
