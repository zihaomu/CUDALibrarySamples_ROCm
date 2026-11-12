#!/usr/bin/env python3
"""Check each GPU MQ bit against frozen OpenJPEG vectors and rejection cases."""
import json
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

PROFILE = ROOT / 'migration/rewrite/image-j2k-mq-profile.json'
BUILD = ROOT / 'migration/reports/image-j2k-mq-build.json'
REPORT = ROOT / 'migration/reports/image-j2k-mq-runs.json'


def main():
    profile = json.loads(PROFILE.read_text())
    build = json.loads(BUILD.read_text())
    binary = ROOT / build['binary']
    if profile['status'] != 'FROZEN' or build['status'] != 'BUILT' or \
            digest(binary) != build['binary_sha256']:
        raise ValueError('MQ profile/build identity mismatch')
    results = []
    for case in profile['cases']:
        files = {kind: ROOT / case['files'][kind]['path'] for kind in ('mq', 'ctx', 'bits')}
        if any(digest(path) != case['files'][kind]['sha256']
               for kind, path in files.items()):
            raise ValueError('frozen MQ fixture changed')
        e = Experiment('I6', 'JPEG2000-MQ-HIP-all-bits-' + case['id'], 'rocm-GPU',
                       case=case['id'], sources=[__file__, PROFILE, binary, *files.values()],
                       parent=build['experiment_id'])
        write(e.path / 'backend.observed.json', capture())
        output = e.path / 'out.bits'
        rc = e.command([str(binary), str(files['mq']), str(files['ctx']), str(output)],
                       'decode-all-OpenJPEG-bits-on-GPU')
        exact = rc == 0 and output.exists() and \
            output.read_bytes() == files['bits'].read_bytes()
        result = dict(case=case['id'], status='PASSED' if exact else 'NUMERIC_MISMATCH',
                      symbols=case['symbols'], encoded_bytes=case['encoded_bytes'],
                      output_sha256=digest(output) if output.exists() else None,
                      expected_sha256=case['files']['bits']['sha256'], return_code=rc)
        result['evidence'] = e.finish('PASSED' if exact else 'NUMERIC_MISMATCH',
                                      dict(status=result['status'], checks=[
                                          dict(check='full-bitstream-exact', passed=exact)]))
        results.append(result)
        record('I6', f'MQ HIP {case["id"]}：{result["status"]}；{case["symbols"]} bit 与独立 OpenJPEG 精确对照，仅孤立熵组件。',
               [result['evidence']])
        if not exact:
            break

    if len(results) == 4 and all(row['status'] == 'PASSED' for row in results):
        fixture = profile['cases'][3]
        source = ROOT / fixture['files']['mq']['path']
        context = ROOT / fixture['files']['ctx']['path']
        expected = ROOT / fixture['files']['bits']['path']
        e = Experiment('I6', 'JPEG2000-MQ-HIP-changed-coded-byte-replay', 'rocm-GPU',
                       sources=[__file__, PROFILE, binary, source, context],
                       parent=build['experiment_id'])
        write(e.path / 'backend.observed.json', capture())
        mutated = bytearray(source.read_bytes()); mutated[1] ^= 0x20
        changed = e.path / 'changed.mq'; changed.write_bytes(mutated)
        output = e.path / 'out.bits'
        rc = e.command([str(binary), str(changed), str(context), str(output)],
                       'changed-MQ-coded-byte-GPU-replay')
        different = rc == 0 and output.exists() and output.read_bytes() != expected.read_bytes()
        result = dict(case='changed-coded-byte', status='PASSED' if different else 'FAILED',
                      input_sha256=digest(changed), output_sha256=digest(output) if output.exists() else None,
                      differs_from_frozen_bits=different, return_code=rc)
        result['evidence'] = e.finish('PASSED' if different else 'VALIDATOR_GAP',
                                      dict(status=result['status'], checks=[
                                          dict(check='changed-input-changes-GPU-output', passed=different)]))
        results.append(result)
        record('I6', 'MQ HIP 已改变码流字节重放：' + result['status'] + '；输出必须变化。',
               [result['evidence']])

        for name in ('truncated-payload', 'invalid-context'):
            e = Experiment('I6', 'JPEG2000-MQ-HIP-' + name, 'rocm-GPU-negative',
                           sources=[__file__, PROFILE, binary, source, context],
                           parent=build['experiment_id'])
            write(e.path / 'backend.observed.json', capture())
            bad_coded = e.path / 'bad.mq'; bad_context = e.path / 'bad.ctx'
            bad_coded.write_bytes(source.read_bytes()[:1] if name == 'truncated-payload'
                                  else source.read_bytes())
            bad_context.write_bytes(bytes([19]) + context.read_bytes()[1:] if name == 'invalid-context'
                                    else context.read_bytes())
            output = e.path / 'out.bits'
            rc = e.command([str(binary), str(bad_coded), str(bad_context), str(output)],
                           'reject-invalid-MQ-payload')
            rejected = rc != 0 and not output.exists()
            result = dict(case=name, status='PASSED' if rejected else 'FAILED',
                          return_code=rc, no_output=not output.exists(),
                          input_sha256=digest(bad_coded), context_sha256=digest(bad_context))
            result['evidence'] = e.finish('EXPECTED_REJECTION' if rejected else 'VALIDATOR_GAP',
                                          dict(status=result['status'], checks=[
                                              dict(check='invalid-input-rejected', passed=rejected)]))
            results.append(result)
            record('I6', f'MQ HIP {name}：{result["status"]}，应拒绝且无输出文件。',
                   [result['evidence']])
    passed = len(results) == 7 and all(row['status'] == 'PASSED' for row in results)
    write(REPORT, dict(status='PASSED' if passed else 'FAILED',
                       scope='Isolated MQ arithmetic decode; not real EBCOT codeblock or JP2 original sample.',
                       cases=results))
    print('PASSED' if passed else 'FAILED', len(results))
    return int(not passed)


if __name__ == '__main__':
    raise SystemExit(main())
