#!/usr/bin/env python3
"""Reject malformed I5 full GPU encoder inputs without producing a JPEG file."""
import json
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture


def main():
    build = json.loads((ROOT / 'migration/reports/image-jpeg-encoder-full-gpu-build.json').read_text())
    profile = json.loads((ROOT / 'migration/rewrite/image-jpeg-encoder-full-gpu-profile.json').read_text())
    item = profile['inputs'][0]
    cases = [('truncated-rgb', item['path'], '34', '29', '75', '420'),
             ('zero-width', item['path'], '0', '29', '75', '420'),
             ('bad-quality', item['path'], '33', '29', '0', '420'),
             ('bad-sampling', item['path'], '33', '29', '75', '422')]
    rows = []
    for name, source, width, height, quality, sampling in cases:
        e = Experiment('I5', 'full-GPU-JPEG-malformed-input-rejection',
                       'rocm-negative', case=name, sources=[__file__, ROOT / source,
                       ROOT / 'rocm/common/image/jpeg_full_gpu.hpp'],
                       parent=build['experiment_id'])
        write(e.path / 'backend.observed.json', capture())
        output = e.path / 'must-not-exist.jpg'
        rc = e.command([str(ROOT / build['binary']), str(ROOT / source), width,
                        height, quality, sampling, str(output)], 'reject-malformed-JPEG-input')
        checks = [dict(check='invalid-input-returns-error', passed=rc != 0),
                  dict(check='invalid-input-produces-no-JPEG', passed=not output.exists())]
        status = 'EXPECTED_REJECTION' if all(x['passed'] for x in checks) else 'VALIDATOR_GAP'
        row = dict(case=name, status=status, return_code=rc, checks=checks,
                   experiment_id=e.id)
        write(e.path / 'negative.json', row)
        row['evidence'] = e.finish(status, dict(status=status, checks=checks))
        rows.append(row)
        write(ROOT / 'migration/reports/image-jpeg-encoder-full-gpu-negative.json', rows)
        record('I5', '全 GPU JPEG encoder 负向输入 '+name+'：'+status+'；非法输入无输出码流。',
               [row['evidence']])
        print(name, status)
    return int(any(x['status'] != 'EXPECTED_REJECTION' for x in rows))


if __name__ == '__main__':
    raise SystemExit(main())
