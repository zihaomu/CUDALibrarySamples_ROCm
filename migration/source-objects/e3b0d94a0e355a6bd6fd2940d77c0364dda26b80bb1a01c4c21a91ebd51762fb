#!/usr/bin/env python3
"""Trace the isolated MQ decoder on physical AMD GPU1."""
import csv
import json
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

PROFILE = ROOT / 'migration/rewrite/image-j2k-mq-profile.json'
BUILD = ROOT / 'migration/reports/image-j2k-mq-build.json'
RUNS = ROOT / 'migration/reports/image-j2k-mq-runs.json'
REPORT = ROOT / 'migration/reports/image-j2k-mq-trace.json'


def main():
    profile = json.loads(PROFILE.read_text())
    build = json.loads(BUILD.read_text())
    runs = json.loads(RUNS.read_text())
    if runs['status'] != 'PASSED' or len(runs['cases']) != 7:
        raise ValueError('seven MQ numerical and negative gates required')
    fixture = profile['cases'][3]
    coded = ROOT / fixture['files']['mq']['path']
    context = ROOT / fixture['files']['ctx']['path']
    expected = fixture['files']['bits']['sha256']
    e = Experiment('I6', 'JPEG2000-MQ-arithmetic-GPU-kernel-trace', 'rocm-trace',
                   sources=[__file__, PROFILE, BUILD, RUNS, coded, context,
                            ROOT / 'rocm/backends/codec/jpeg2000/mq_decode.hpp',
                            ROOT / 'rocm/backends/codec/jpeg2000/mq_states.hpp'],
                   parent=build['experiment_id'])
    observed = capture()
    write(e.path / 'backend.observed.json', observed)
    output = e.path / 'out.bits'
    rc = e.command(['rocprofv3', '--kernel-trace', '--output-format', 'csv',
                    '--output-directory', str(e.path / 'trace'), '--',
                    str(ROOT / build['binary']), str(coded), str(context), str(output)],
                   'profile-isolated-MQ-GPU-decoder', timeout=300)
    traces = list((e.path / 'trace').rglob('*kernel_trace.csv'))
    agents = list((e.path / 'trace').rglob('*agent_info.csv'))
    checks = [dict(check='profiled-command-success', passed=rc == 0),
              dict(check='profiled-exact-all-1023-bits', passed=output.is_file() and digest(output) == expected),
              dict(check='trace-agent-map', passed=len(traces) == len(agents) == 1)]
    kernels = []
    allowed = {device['pci_bdf'] for device in observed['devices'] if device['physical_id'] == 1}
    if len(traces) == len(agents) == 1:
        lookup = {row['Node_Id']: row for row in csv.DictReader(agents[0].open())}
        for event in csv.DictReader(traces[0].open()):
            if 'decode_one' not in event['Kernel_Name']:
                continue
            agent = lookup[event['Agent_Id'].split()[-1]]
            loc = int(agent['Location_Id'])
            location = f"{int(agent['Domain']):04x}:{loc >> 8:02x}:{(loc >> 3) & 31:02x}.{loc & 7}"
            kernels.append(dict(name=event['Kernel_Name'], pci_bdf=location,
                                grid_size=int(event['Grid_Size_X']),
                                stream_id=event['Stream_Id'],
                                duration_ns=int(event['End_Timestamp']) - int(event['Start_Timestamp'])))
        checks.append(dict(check='one-real-physical-GPU1-MQ-kernel',
                           passed=len(kernels) == 1 and kernels[0]['pci_bdf'] in allowed and
                           kernels[0]['grid_size'] > 0 and kernels[0]['duration_ns'] > 0,
                           kernels=kernels))
    status = 'PASSED' if all(check['passed'] for check in checks) else 'PROFILER_FAILED'
    result = dict(status=status, checks=checks, kernels=kernels, experiment_id=e.id)
    write(e.path / 'trace-result.json', result)
    result['evidence'] = e.finish(status, dict(status=status, checks=checks))
    write(REPORT, result)
    record('I6', 'JPEG2000 孤立 MQ 算术解码 GPU trace：' + status +
           '；核对实际 kernel/物理 GPU1/全部1023 bit；尚非真实码块。', [result['evidence']])
    print(status, kernels)
    return int(status != 'PASSED')


if __name__ == '__main__':
    raise SystemExit(main())
