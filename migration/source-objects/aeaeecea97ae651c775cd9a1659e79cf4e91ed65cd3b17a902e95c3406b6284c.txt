#!/usr/bin/env python3
"""Trace the original-JP2 MQ segment replay on physical AMD GPU1."""
import csv
import json
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

VECTOR = ROOT / 'migration/rewrite/image-j2k-real-mq-vector.json'
REPLAY = ROOT / 'migration/reports/image-j2k-real-mq-replay.json'
BUILD = ROOT / 'migration/reports/image-j2k-mq-build.json'
REPORT = ROOT / 'migration/reports/image-j2k-real-mq-trace.json'


def main():
    vector = json.loads(VECTOR.read_text())
    replay = json.loads(REPLAY.read_text())
    build = json.loads(BUILD.read_text())
    if vector['status'] != 'FROZEN' or replay['status'] != 'PASSED':
        raise ValueError('real JP2 MQ bit replay required before trace')
    coded = ROOT / vector['mq']; context = ROOT / vector['context']
    if digest(coded) != vector['mq_sha256'] or digest(context) != vector['context_sha256']:
        raise ValueError('frozen real-JP2 MQ inputs changed')
    e = Experiment('I6', 'original-JP2-MQ-segment-physical-GPU-trace', 'rocm-trace',
                   sources=[__file__, VECTOR, REPLAY, BUILD, coded, context],
                   parent=replay['evidence'].split('/')[-1])
    observed = capture()
    write(e.path / 'backend.observed.json', observed)
    output = e.path / 'out.bits'
    rc = e.command(['rocprofv3', '--kernel-trace', '--output-format', 'csv',
                    '--output-directory', str(e.path / 'trace'), '--',
                    str(ROOT / build['binary']), str(coded), str(context), str(output)],
                   'trace-real-original-JP2-MQ-segment', timeout=300)
    traces = list((e.path / 'trace').rglob('*kernel_trace.csv'))
    agents = list((e.path / 'trace').rglob('*agent_info.csv'))
    checks = [dict(check='profiled-command-success', passed=rc == 0),
              dict(check='all-real-JP2-bits-exact', passed=output.is_file() and
                   digest(output) == vector['bits_sha256']),
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
            pci = f"{int(agent['Domain']):04x}:{loc >> 8:02x}:{(loc >> 3) & 31:02x}.{loc & 7}"
            kernels.append(dict(name=event['Kernel_Name'], pci_bdf=pci,
                                duration_ns=int(event['End_Timestamp']) - int(event['Start_Timestamp']),
                                grid_size=int(event['Grid_Size_X'])))
        checks.append(dict(check='one-actual-GPU1-MQ-kernel',
                           passed=len(kernels) == 1 and kernels[0]['pci_bdf'] in allowed and
                           kernels[0]['duration_ns'] > 0 and kernels[0]['grid_size'] > 0,
                           kernels=kernels))
    status = 'PASSED' if all(c['passed'] for c in checks) else 'PROFILER_FAILED'
    result = dict(status=status, checks=checks, kernels=kernels, symbols=vector['symbols'])
    write(e.path / 'trace-result.json', result)
    result['evidence'] = e.finish(status, dict(status=status, checks=checks))
    write(REPORT, result)
    record('I6', f'真实JP2 MQ 段{vector["symbols"]} bit 物理GPU1 trace：{status}；仅算术解码组件。',
           [result['evidence'], str(REPORT.relative_to(ROOT))])
    print(status, kernels)
    return int(status != 'PASSED')


if __name__ == '__main__':
    raise SystemExit(main())
