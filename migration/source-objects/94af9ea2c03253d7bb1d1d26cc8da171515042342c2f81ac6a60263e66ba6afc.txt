#!/usr/bin/env python3
"""Build and exercise the bounded JPEG2000 container/main-header parser."""
import json
from experiment import ROOT, Experiment, digest, write
from image_progress import record

SOURCE = ROOT / 'rocm/probes/image/jpeg2000_container.cpp'
HEADER = ROOT / 'rocm/backends/codec/jpeg2000/container.hpp'
PROFILE = ROOT / 'migration/rewrite/image-j2k-container-profile.json'
BUILD = ROOT / 'migration/reports/image-j2k-container-build.json'
REPORT = ROOT / 'migration/reports/image-j2k-container-runs.json'


def result_of(e, command, label):
    rc = e.command(command, label, timeout=120)
    stdout = e.path / ('logs/0001-' + label + '.stdout.log')
    stderr = e.path / ('logs/0001-' + label + '.stderr.log')
    metadata = json.loads(stdout.read_text().strip()) if rc == 0 else None
    return rc, metadata, stderr.read_text()


def main():
    profile = json.loads(PROFILE.read_text())
    if profile['status'] != 'FROZEN' or len(profile['cases']) != 9:
        raise ValueError('nine frozen I6 parser cases required')
    e = Experiment('I6', 'JP2-J2K-main-header-parser-build', 'host-build',
                   sources=[__file__, SOURCE, HEADER, PROFILE],
                   parent=profile['evidence'].split('/')[-1])
    binary = e.path / 'probe'
    rc = e.command(['g++', '-std=c++17', '-O2', str(SOURCE), '-o', str(binary)],
                   'build-bounded-JP2-parser', timeout=120)
    build = dict(status='BUILT' if rc == 0 else 'BUILD_ERROR', return_code=rc,
                 binary=str(binary.relative_to(ROOT)) if rc == 0 else None,
                 binary_sha256=digest(binary) if rc == 0 else None,
                 dependencies={str(p.relative_to(ROOT)): digest(p) for p in [SOURCE, HEADER, PROFILE]},
                 experiment_id=e.id)
    write(e.path / 'build.json', build)
    build['evidence'] = e.finish('EXECUTED' if rc == 0 else 'BUILD_ERROR',
                                  dict(status=build['status'], checks=[
                                      dict(check='real-host-parser-build', passed=rc == 0)]))
    write(BUILD, build)
    record('I6', 'JP2/J2K 容器主头边界解析器构建：'+build['status']+'；不是 GPU codec。',
           [build['evidence']])
    if rc:
        return 1
    rows = []
    for item in profile['inputs']:
        source = ROOT / item['source']
        if digest(source) != item['sha256']:
            raise ValueError('frozen JP2 source changed')
        e = Experiment('I6', 'original-JP2-main-header-parse', 'CPU-parser',
                       case=item['case']+'-jp2', sources=[__file__, SOURCE, HEADER, PROFILE,
                                                       BUILD, source], parent=build['experiment_id'])
        rc, metadata, error = result_of(e, [str(binary), str(source)], 'parse-original-JP2')
        checks = [dict(check='original-JP2-parser-success', passed=rc == 0),
                  dict(check='independent-CPU-geometry-and-components', passed=
                       metadata is not None and metadata['width'] == item['width'] and
                       metadata['height'] == item['height'] and
                       metadata['components'] == item['components']),
                  dict(check='JP2-box-SOC-SIZ-COD-metadata', passed=
                       metadata is not None and metadata['jp2'] is True and
                       metadata['codestream_offset'] > 0 and metadata['codestream_bytes'] > 0 and
                       metadata['tiles_x'] > 0 and metadata['tiles_y'] > 0 and
                       metadata['transform'] == int(item['reversible']) and
                       metadata['bit_depth'] == [8, 8, 8] and metadata['signed'] == [0, 0, 0])]
        status = 'PASSED' if all(c['passed'] for c in checks) else 'NUMERIC_MISMATCH'
        row = dict(case=item['case']+'-jp2', status=status, checks=checks,
                   metadata=metadata, return_code=rc, error=error, experiment_id=e.id)
        write(e.path / 'run.json', row)
        row['evidence'] = e.finish(status if rc == 0 else 'RUNTIME_ERROR',
                                   dict(status=status, checks=checks))
        rows.append(row); write(REPORT, rows)
        record('I6', item['case']+' 原始 JP2 主头与独立 CPU 尺寸/分量校对：'+status+'。',
               [row['evidence']])
        print(row['case'], status, flush=True)
    original = ROOT / profile['inputs'][0]['source']
    contents = original.read_bytes(); offset = contents.find(b'\xff\x4f\xff\x51')
    if offset < 0:
        raise ValueError('SOC/SIZ missing in frozen source')
    raw = contents[offset:]
    variants = [('2k_lossless-raw-j2k', raw, True),
                ('invalid-signature', contents[:11] + bytes([contents[11] ^ 1]) + contents[12:], False),
                ('invalid-box-length', None, False),
                ('truncated-main-header', raw[:40], False),
                ('zero-components', raw[:40] + b'\0\0' + raw[42:], False),
                ('changed-SIZ-width', raw[:8] + (int.from_bytes(raw[8:12], 'big') - 1).to_bytes(4, 'big') + raw[12:], True)]
    jp2c = contents.find(b'jp2c')
    if jp2c < 4:
        raise ValueError('jp2c box missing')
    variants[2] = ('invalid-box-length', contents[:jp2c-4] + b'\xff\xff\xff\xff' + contents[jp2c:], False)
    for name, data, should_succeed in variants:
        e = Experiment('I6', 'JP2-J2K-main-header-boundary', 'CPU-parser', case=name,
                       sources=[__file__, SOURCE, HEADER, PROFILE, BUILD, original],
                       parent=build['experiment_id'])
        input_path = e.path / ('input.jp2' if name.startswith('invalid-') else 'input.j2k')
        input_path.write_bytes(data)
        rc, metadata, error = result_of(e, [str(binary), str(input_path)], 'parse-boundary-'+name)
        if should_succeed:
            good = rc == 0 and metadata is not None and metadata['jp2'] is False and \
                metadata['codestream_offset'] == 0 and metadata['components'] == 3 and \
                metadata['width'] == (1919 if name == 'changed-SIZ-width' else 1920)
        else:
            good = rc != 0 and metadata is None and 'RESULT status=FAIL' in error
        status = 'PASSED' if good else 'FAILED'
        checks = [dict(check=name+'-expected-result', passed=good)]
        row = dict(case=name, status=status, checks=checks, input_sha256=digest(input_path),
                   metadata=metadata, return_code=rc, error=error, experiment_id=e.id)
        write(e.path / 'run.json', row)
        row['evidence'] = e.finish(('PASSED' if should_succeed else 'EXPECTED_REJECTION')
                                    if good else 'NUMERIC_MISMATCH',
                                    dict(status=status, checks=checks))
        rows.append(row); write(REPORT, rows)
        record('I6', 'JP2/J2K 主头 '+name+' 边界/变化重放：'+status+'。', [row['evidence']])
        print(name, status, flush=True)
    return int(any(row['status'] != 'PASSED' for row in rows))


if __name__ == '__main__':
    raise SystemExit(main())
