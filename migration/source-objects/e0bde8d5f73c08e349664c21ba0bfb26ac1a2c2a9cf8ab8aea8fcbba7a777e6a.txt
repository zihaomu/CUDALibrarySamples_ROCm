#!/usr/bin/env python3
"""Verify five frozen inverse 5/3 + RCT GPU outputs, negatives, and replay."""
import json
import shutil
import struct
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

PROFILE = ROOT / 'migration/rewrite/image-j2k-i53-rct-profile.json'
BUILD = ROOT / 'migration/reports/image-j2k-i53-build.json'
REPORT = ROOT / 'migration/reports/image-j2k-i53-runs.json'
HEADER = ROOT / 'rocm/backends/codec/jpeg2000/reversible53.hpp'
SOURCE = ROOT / 'rocm/probes/image/jpeg2000_reversible53.hip'


def main():
    profile = json.loads(PROFILE.read_text()); build = json.loads(BUILD.read_text())
    if build['status'] != 'BUILT' or any(digest(ROOT / n) != sha for n, sha in
                                           build['dependencies'].items()) or \
            digest(ROOT / build['binary']) != build['binary_sha256']:
        raise ValueError('current HIP probe build required')
    rows = []
    for item in profile['fixtures']:
        coefficients = ROOT / item['coefficients']; expected = ROOT / item['expected_rgb']
        if (digest(coefficients) != item['coefficients_sha256'] or
                digest(expected) != item['expected_rgb_sha256']):
            raise ValueError('I6 fixture identity drift')
        e = Experiment('I6', 'JPEG2000-GPU-inverse-5-3-RCT-component', 'rocm-prototype',
                       case=item['case'], sources=[__file__, SOURCE, HEADER, PROFILE,
                                                     BUILD, coefficients, expected],
                       parent=build['experiment_id'])
        write(e.path / 'backend.observed.json', capture())
        output = e.path / 'decoded.rgb'
        command = [str(ROOT / build['binary']), str(coefficients),
                   str(item['width']), str(item['height']), str(output)]
        rc = e.command(command, 'actual-GPU-inverse-53-RCT', timeout=120)
        metadata_path = e.path / 'logs/0001-actual-GPU-inverse-53-RCT.stdout.log'
        metadata = json.loads(metadata_path.read_text().splitlines()[-1]) if rc == 0 else {}
        checks = [dict(check='actual-GPU-command-success', passed=rc == 0),
                  dict(check='exact-frozen-RGB-bytes', passed=output.is_file() and
                       output.read_bytes() == expected.read_bytes()),
                  dict(check='honest-isolated-component-claim', passed=
                       metadata.get('gpu_inverse53') is True and
                       metadata.get('gpu_inverse_rct') is True and
                       metadata.get('full_jp2_decode') is False)]
        status = 'PASSED' if all(c['passed'] for c in checks) else 'NUMERIC_MISMATCH'
        row = dict(case=item['case'], status=status, checks=checks, return_code=rc,
                   decoded_rgb_sha256=digest(output) if output.is_file() else None,
                   experiment_id=e.id)
        write(e.path / 'run.json', row)
        row['evidence'] = e.finish(status if rc == 0 else 'RUNTIME_ERROR',
                                   dict(status=status, checks=checks))
        rows.append(row); write(REPORT, rows)
        record('I6', 'JPEG2000 inverse 5/3+RCT '+item['case']+' 原图系数 GPU 逆变换与预冻 RGB 精确比对：'+status+'；不计整例。',
               [row['evidence']])
        print(item['case'], status, flush=True)
    anchor = profile['fixtures'][3]
    for name, kind in [('truncated', 'truncate'), ('zero-width', 'dimension'),
                       ('changed-coefficient', 'change')]:
        src = ROOT / anchor['coefficients']; expected = ROOT / anchor['expected_rgb']
        e = Experiment('I6', 'JPEG2000-GPU-inverse-5-3-RCT-boundary', 'rocm-prototype',
                       case=name, sources=[__file__, SOURCE, HEADER, PROFILE, BUILD, src, expected],
                       parent=build['experiment_id'])
        write(e.path / 'backend.observed.json', capture())
        altered = e.path / 'coefficients.i32'; shutil.copyfile(src, altered)
        width = anchor['width']
        if kind == 'truncate':
            altered.write_bytes(altered.read_bytes()[:-4])
        elif kind == 'dimension':
            width = 0
        else:
            data = bytearray(altered.read_bytes())
            first = struct.unpack_from('<i', data)[0]
            struct.pack_into('<i', data, 0, first + 1)
            altered.write_bytes(data)
        out = e.path / 'decoded.rgb'
        rc = e.command([str(ROOT / build['binary']), str(altered), str(width),
                        str(anchor['height']), str(out)], 'boundary-'+name, timeout=120)
        if kind == 'change':
            good = rc == 0 and out.is_file() and out.read_bytes() != expected.read_bytes()
            outcome = 'PASSED' if good else 'NUMERIC_MISMATCH'
        else:
            stderr = (e.path / ('logs/0001-boundary-'+name+'.stderr.log')).read_text()
            good = rc != 0 and not out.exists() and 'RESULT status=FAIL' in stderr
            outcome = 'EXPECTED_REJECTION' if good else 'NUMERIC_MISMATCH'
        row = dict(case=name, status='PASSED' if good else 'FAILED',
                   return_code=rc, checks=[dict(check=kind+'-boundary', passed=good)],
                   input_sha256=digest(altered), output_sha256=digest(out) if out.is_file() else None,
                   experiment_id=e.id)
        write(e.path / 'run.json', row)
        row['evidence'] = e.finish(outcome, dict(status=row['status'], checks=row['checks']))
        rows.append(row); write(REPORT, rows)
        record('I6', 'JPEG2000 inverse 5/3+RCT '+name+' 输入拒绝/变化重放：'+row['status']+'。',
               [row['evidence']])
        print(name, row['status'], flush=True)
    return int(any(r['status'] != 'PASSED' for r in rows))


if __name__ == '__main__':
    raise SystemExit(main())
