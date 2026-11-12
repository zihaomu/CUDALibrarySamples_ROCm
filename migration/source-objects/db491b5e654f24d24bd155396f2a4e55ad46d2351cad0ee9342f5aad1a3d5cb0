#!/usr/bin/env python3
"""Independent NumPy reference for every original watershed output product."""
import json
from pathlib import Path

import numpy as np

from experiment import ROOT, Experiment, digest, write
from image_progress import record
from image_watershed_research import descent, NATIVE

PROFILE = ROOT / 'migration/rewrite/image-watershed-profile.json'
RUNS = ROOT / 'migration/reports/image-watershed-runs.json'
REPORT = ROOT / 'migration/reports/image-watershed-reference.json'


def boundary(roots):
    h, w = roots.shape
    result = np.zeros((h, w), dtype=bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if not (dy or dx):
                continue
            y0, y1 = max(0, -dy), min(h, h - dy)
            x0, x1 = max(0, -dx), min(w, w - dx)
            result[y0:y1, x0:x1] |= (
                roots[y0:y1, x0:x1] !=
                roots[y0 + dy:y1 + dy, x0 + dx:x1 + dx])
    return result


def native_output_dir(family):
    archive = ROOT / NATIVE[family]
    manifest = json.loads((archive / 'manifest.json').read_text())
    return ROOT / manifest['raw_artifact_dir'] / 'outputs/images'


def validate_sample(sample, run):
    family = run['family']
    e = Experiment('I3', sample['sample_id'], 'independent-CPU-reference',
                   sources=[__file__, ROOT / 'tools/moat/image_watershed_research.py',
                            PROFILE, RUNS, ROOT / NATIVE[family] / 'run.json',
                            *[ROOT / family / 'watershedSegmentation/images' / image['name']
                              for image in sample['inputs']]],
                   parent=run['experiment_id'])
    output_dir = ROOT / run['output_dir']
    native_dir = native_output_dir(family)
    products = {}
    image_metrics = []
    for item in sample['inputs']:
        name, w, h = item['name'], item['width'], item['height']
        source = ROOT / family / 'watershedSegmentation/images' / name
        if digest(source) != item['sha256']:
            raise ValueError('original source hash changed: ' + name)
        image = np.fromfile(source, np.uint8).reshape(h, w)
        roots, segments, steps = descent(image)
        roots_flat = roots.reshape(-1)
        fixed = bool(np.all(roots_flat[roots_flat] == roots_flat))
        parent_values = image.reshape(-1)[roots_flat]
        monotone = bool(np.all(parent_values <= image.reshape(-1)))
        expected = {}
        if family == 'NPP':
            expected['Segmented_' + name] = segments.tobytes()
            expected['Labels_' + name] = roots.astype('<u4').tobytes()
            native_segment_name = 'Segmented_' + name
            native_label_name = 'Labels_' + name
        else:
            prefix = name.split('_')[0]
            if name.startswith('CT_skull'):
                prefix = 'CT_skull'
            elif name.startswith('Corn'):
                prefix = 'Corn'
            suffix = f'_8Way_{w}x{h}'
            root_flags = np.zeros(w * h, dtype=np.uint32)
            root_flags[np.unique(roots_flat)] = 1
            root_ranks = np.cumsum(root_flags, dtype=np.uint32) - 1
            compact = root_ranks[roots_flat].reshape(h, w)
            edge = boundary(roots)
            boundaries = np.where(edge, 0, 255).astype(np.uint8)
            contrast = np.where(edge, 255, segments).astype(np.uint8)
            expected[prefix + '_Segments' + suffix + '_8u.raw'] = segments.tobytes()
            expected[prefix + '_CompressedSegmentLabels' + suffix + '_32u.raw'] = compact.astype('<u4').tobytes()
            expected[prefix + '_SegmentBoundaries' + suffix + '_8u.raw'] = boundaries.tobytes()
            expected[prefix + '_SegmentsWithContrastingBoundaries' + suffix + '_8u.raw'] = contrast.tobytes()
            native_segment_name = prefix + '_Segments' + suffix + '_8u.raw'
            native_label_name = prefix + '_CompressedSegmentLabels' + suffix + '_32u.raw'
        native_segments = np.fromfile(native_dir / native_segment_name, np.uint8).reshape(h, w)
        native_labels = np.fromfile(native_dir / native_label_name, np.uint32).reshape(h, w)
        project_edges = boundary(roots)
        native_edges = boundary(native_labels)
        image_metrics.append(dict(input=name, pixels=w * h, descent_steps=steps,
            root_fixed=fixed, root_intensity_monotone=monotone,
            roots=int(np.unique(roots_flat).size),
            native_segments_equal_fraction=float(np.mean(segments == native_segments)),
            native_segments_mean_absolute_difference=float(np.mean(
                np.abs(segments.astype(np.int16) - native_segments.astype(np.int16)))),
            native_label_boundary_agreement_fraction=float(np.mean(project_edges == native_edges)),
            native_unique_label_count=int(np.unique(native_labels).size)))
        for product_name, expected_bytes in expected.items():
            actual_path = output_dir / product_name
            actual = actual_path.read_bytes() if actual_path.is_file() else b''
            equal = actual == expected_bytes
            first_difference = next((i for i, (a, b) in enumerate(zip(actual, expected_bytes))
                                     if a != b), None) if not equal else None
            products[product_name] = dict(exact=equal, expected_bytes=len(expected_bytes),
                actual_bytes=len(actual), expected_sha256=__import__('hashlib').sha256(expected_bytes).hexdigest(),
                actual_sha256=digest(actual_path) if actual_path.is_file() else None,
                first_difference=first_difference)
    checks = [dict(check='all-22-or-10-original-product-bytes',
                   passed=len(products) == len(sample['products']) and
                   set(products) == set(sample['products']) and
                   all(p['exact'] for p in products.values())),
              dict(check='all-descent-roots-fixed',
                   passed=all(m['root_fixed'] for m in image_metrics)),
              dict(check='all-root-intensities-monotone',
                   passed=all(m['root_intensity_monotone'] for m in image_metrics)),
              dict(check='native-algorithm-variant-measured',
                   passed=all(0 <= m['native_segments_equal_fraction'] <= 1 and
                              0 <= m['native_label_boundary_agreement_fraction'] <= 1
                              for m in image_metrics))]
    status = 'PASSED' if all(c['passed'] for c in checks) else 'NUMERIC_MISMATCH'
    report = dict(sample_id=sample['sample_id'], family=family, status=status,
                  experiment_id=e.id, run_evidence=run['evidence'],
                  algorithm_variant='NVIDIA NPP uses different basin/label rules; pixel exactness is qualified against independent project CPU reference only',
                  products=products, image_metrics=image_metrics, checks=checks)
    write(e.path / 'reference.json', report)
    report['evidence'] = e.finish(status, dict(status=status, checks=checks),
                                  metrics=dict(images=image_metrics))
    record('I3', f'{family} watershed 独立 NumPy 参考验收：'
           f'{sum(p["exact"] for p in products.values())}/{len(products)} 输出逐字节一致，'
           f'状态 {status}；原生 NPP 差异按 ALGORITHM_VARIANT 记录。', [report['evidence']])
    print(family, status, sum(p['exact'] for p in products.values()), '/', len(products), flush=True)
    return report


def main():
    profile = json.loads(PROFILE.read_text())
    runs = json.loads(RUNS.read_text())
    if len(runs) != 2 or any(r['status'] != 'EXECUTED' for r in runs):
        raise ValueError('complete original-entry HIP executions required')
    rows = []
    for sample, run in zip(profile['samples'], runs):
        if sample['sample_id'] != run['sample_id']:
            raise ValueError('sample/run order mismatch')
        rows.append(validate_sample(sample, run))
        write(REPORT, rows)
    return int(any(row['status'] != 'PASSED' for row in rows))


if __name__ == '__main__':
    raise SystemExit(main())
