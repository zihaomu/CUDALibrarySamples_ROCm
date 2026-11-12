#!/usr/bin/env python3
"""Run every frozen full-GPU baseline JPEG encoder prototype input and independently decode it."""
import io
import json
import math
from PIL import Image, JpegImagePlugin
import numpy as np
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

PROFILE = ROOT / 'migration/rewrite/image-jpeg-encoder-full-gpu-profile.json'
BUILD = ROOT / 'migration/reports/image-jpeg-encoder-full-gpu-build.json'
REPORT = ROOT / 'migration/reports/image-jpeg-encoder-full-gpu-runs.json'


def main():
    profile = json.loads(PROFILE.read_text())
    build = json.loads(BUILD.read_text())
    if build['status'] != 'BUILT' or any(digest(ROOT / p) != sha for p, sha in
                                           build['dependencies'].items()) or \
       digest(ROOT / build['binary']) != build['binary_sha256']:
        raise ValueError('current encoder binary/dependencies required')
    rows = []
    for item in profile['inputs']:
        source = ROOT / item['path']
        if digest(source) != item['sha256']:
            raise ValueError('frozen input changed')
        e = Experiment('I5', 'full-GPU-JPEG-baseline-and-cross-decode',
                       'rocm-prototype', case=item['case'],
                       sources=[__file__, PROFILE, BUILD, source,
                                ROOT / 'rocm/probes/image/jpeg_full_gpu.hip',
                                ROOT / 'rocm/common/image/jpeg_full_gpu.hpp', ROOT / 'rocm/common/image/jpeg_entropy_gpu.hpp', ROOT / 'rocm/common/image/jpeg_encoder_gpu.hpp'],
                       parent=build['experiment_id'])
        write(e.path / 'backend.observed.json', capture())
        jpeg = e.path / 'output.jpg'
        argv = [str(ROOT / build['binary']), str(source), str(item['width']),
                str(item['height']), str(item['quality']), item['subsampling'], str(jpeg)]
        rc = e.command(argv, 'encode-real-AMD-GPU-FDCT-Huffman-pack-stuff')
        source_pixels = np.frombuffer(source.read_bytes(), dtype=np.uint8).reshape(
            item['height'], item['width'], 3)
        checks = [dict(check='encode-command-exit-zero', passed=rc == 0)]
        metrics = {}
        try:
            with Image.open(jpeg) as opened:
                opened.load()
                output_pixels = np.asarray(opened.convert('RGB'))
                sampling = JpegImagePlugin.get_sampling(opened)
                quant = opened.quantization
                fmt = opened.format
            reference = io.BytesIO()
            Image.fromarray(source_pixels, 'RGB').save(
                reference, format='JPEG', quality=item['quality'],
                subsampling=2 if item['subsampling'] == '420' else 0)
            reference.seek(0)
            with Image.open(reference) as opened:
                opened.load()
                expected_quant = opened.quantization
                reference_pixels = np.asarray(opened.convert('RGB'))
            if digest(ROOT / item['reference_jpeg']) != item['reference_jpeg_sha256']:
                raise ValueError('frozen CPU-entropy reference JPEG changed')
            with Image.open(ROOT / item['reference_jpeg']) as frozen:
                frozen.load()
                frozen_pixels = np.asarray(frozen.convert('RGB'))
            diff = output_pixels.astype(np.float64) - source_pixels.astype(np.float64)
            mse = float(np.mean(diff * diff))
            psnr = float('inf') if mse == 0 else 10 * math.log10(255 * 255 / mse)
            delta = np.abs(output_pixels.astype(np.int16) - reference_pixels.astype(np.int16))
            metrics = dict(width=output_pixels.shape[1], height=output_pixels.shape[0],
                           psnr_vs_source_db=psnr, max_abs_vs_cpu_encoder=int(delta.max()),
                           psnr_vs_cpu_encoder_db=float('inf') if not np.any(delta) else
                           10 * math.log10(255 * 255 / float(np.mean(delta.astype(np.float64)**2))),
                           encoded_bytes=jpeg.stat().st_size, sampling=sampling,
                           quantization_matches_cpu=quant == expected_quant,
                           format=fmt)
            checks.extend([
                dict(check='independent-Pillow-libjpeg-decode-JPEG', passed=fmt == 'JPEG'),
                dict(check='exact-output-dimensions', passed=output_pixels.shape == source_pixels.shape),
                dict(check='exact-subsampling', passed=sampling ==
                     (2 if item['subsampling'] == '420' else 0)),
                dict(check='exact-quantization-tables', passed=quant == expected_quant),
                dict(check='nonempty-bitstream', passed=jpeg.stat().st_size > 100),
                dict(check='exact-decoded-RGB-vs-frozen-GPU-FDCT-CPU-entropy',
                     passed=np.array_equal(output_pixels,frozen_pixels))])
            (e.path / 'decoded.rgb').write_bytes(output_pixels.tobytes())
            (e.path / 'frozen.rgb').write_bytes(frozen_pixels.tobytes())
            (e.path / 'reference.rgb').write_bytes(reference_pixels.tobytes())
            (e.path / 'cpu-reference.jpg').write_bytes(reference.getvalue())
        except Exception as error:
            metrics['decode_error'] = repr(error)
            checks.append(dict(check='independent-cross-decode', passed=False,
                               error=repr(error)))
        stdout=(e.path / 'logs/0001-encode-real-AMD-GPU-FDCT-Huffman-pack-stuff.stdout.log').read_text()
        metadata=json.loads(stdout.splitlines()[-1]) if rc==0 and stdout.strip() else {}
        checks.append(dict(check='GPU-entropy-without-CPU-entropy',passed=metadata.get('gpu_huffman') is True and metadata.get('gpu_pack_stuff') is True and metadata.get('cpu_entropy') is False))
        status = 'PASSED' if all(c['passed'] for c in checks) else 'NUMERIC_MISMATCH'
        row = dict(case=item['case'], status=status, return_code=rc, checks=checks,
                   metrics=metrics, metadata=metadata, experiment_id=e.id,
                   jpeg_sha256=digest(jpeg) if jpeg.is_file() else None)
        write(e.path / 'run.json', row)
        row['evidence'] = e.finish(status if rc == 0 else 'RUNTIME_ERROR',
            dict(status=status, checks=checks), metrics=metrics)
        rows.append(row)
        write(REPORT, rows)
        record('I5', 'GPU JPEG FDCT/量化+Huffman/pack/stuff '+item['case']+' 独立跨解码：'+
               status+'；PSNR='+str(metrics.get('psnr_vs_source_db'))+' dB。',
               [row['evidence']])
        print(item['case'], status, metrics, flush=True)
    return int(any(r['status'] != 'PASSED' for r in rows))


if __name__ == '__main__':
    raise SystemExit(main())
