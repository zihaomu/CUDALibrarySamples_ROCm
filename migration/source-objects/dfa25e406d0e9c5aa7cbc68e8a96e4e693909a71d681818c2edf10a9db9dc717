#!/usr/bin/env python3
"""Report every original NPP output difference without silently tolerating it."""
import json

import numpy as np

from experiment import ROOT, Experiment, write
from image_progress import record
from image_watershed_reference import boundary, native_output_dir

PROFILE = ROOT / 'migration/rewrite/image-watershed-profile.json'
RUNS = ROOT / 'migration/reports/image-watershed-runs.json'
REPORT = ROOT / 'migration/reports/image-watershed-native-comparison.json'


def main():
    profile = json.loads(PROFILE.read_text())
    runs = json.loads(RUNS.read_text())
    e = Experiment('I3', 'both-watershed-full-native-product-comparison',
                   'CPU-native-comparison',
                   sources=[__file__, PROFILE, RUNS,
                            ROOT / 'tools/moat/image_watershed_reference.py'])
    rows = []
    for sample, run in zip(profile['samples'], runs):
        family = run['family']
        native_dir = native_output_dir(family)
        output_dir = ROOT / run['output_dir']
        for name, info in sample['products'].items():
            width = next(x['width'] for x in sample['inputs']
                         if str(x['width']) + 'x' + str(x['height']) in name or
                         name.endswith(x['name']))
            height = info['bytes'] // width // (4 if 'Labels' in name else 1)
            dtype = np.uint32 if 'Labels' in name else np.uint8
            project = np.fromfile(output_dir / name, dtype).reshape(height, width)
            native = np.fromfile(native_dir / name, dtype).reshape(height, width)
            delta = (project.astype(np.int64) - native.astype(np.int64))
            row = dict(family=family, product=name, pixels=width * height,
                exact_pixels=int(np.count_nonzero(delta == 0)),
                equal_fraction=float(np.mean(delta == 0)),
                mean_absolute_difference=float(np.mean(np.abs(delta))),
                max_absolute_difference=int(np.max(np.abs(delta))),
                output_kind='label-id' if dtype == np.uint32 else 'image')
            if dtype == np.uint32:
                row['label_partition_neighbor_agreement_fraction'] = float(np.mean(
                    boundary(project) == boundary(native)))
            rows.append(row)
    result = dict(status='OBSERVED_ALGORITHM_VARIANT', rows=rows,
        disclaimer='Original NPP output and project gradient-descent watershed differ; equality to the independent project CPU model alone is insufficient for original-vendor equivalence.')
    write(e.path / 'comparison.json', result)
    result['evidence'] = e.finish('OBSERVED', dict(status=result['status'],
        checks=[dict(check='all-22-original-products-compared', passed=len(rows) == 22)]))
    write(REPORT, result)
    record('I3', 'NPP/NPP+ watershed 22 个原生输出与 HIP 全像素比较：ALGORITHM_VARIANT；'
           '尤其 CT 分割原生一致率约 71.7%，不得据项目 CPU 自洽性声称完整 NPP 等价。',
           [result['evidence']])
    print(result['status'], len(rows))


if __name__ == '__main__':
    main()
