#!/usr/bin/env python3
"""Trace the isolated JPEG2000 inverse transform on physical AMD GPU1."""
import csv
import json
from collections import Counter
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

PROFILE = ROOT / 'migration/rewrite/image-j2k-i53-rct-profile.json'
BUILD = ROOT / 'migration/reports/image-j2k-i53-build.json'
RUNS = ROOT / 'migration/reports/image-j2k-i53-runs.json'
REPORT = ROOT / 'migration/reports/image-j2k-i53-trace.json'
STAGES = ('inverse_vertical', 'inverse_horizontal', 'inverse_rct_rgb')


def main():
    profile = json.loads(PROFILE.read_text()); build = json.loads(BUILD.read_text())
    runs = json.loads(RUNS.read_text())
    item = next(x for x in profile['fixtures'] if x['case'] == 'tile-edge')
    prior = next(x for x in runs if x['case'] == item['case'])
    if len(runs) != 8 or any(x['status'] != 'PASSED' for x in runs):
        raise ValueError('five numeric and three boundary gates required')
    e = Experiment('I6', 'JPEG2000-inverse-5-3-RCT-real-GPU-trace', 'rocm-trace',
                   sources=[__file__, PROFILE, BUILD, RUNS,
                            ROOT / 'rocm/probes/image/jpeg2000_reversible53.hip',
                            ROOT / 'rocm/backends/codec/jpeg2000/reversible53.hpp',
                            ROOT / item['coefficients'], ROOT / item['expected_rgb']],
                   parent=prior['experiment_id'])
    observed = capture(); write(e.path / 'backend.observed.json', observed)
    output = e.path / 'decoded.rgb'
    command = ['rocprofv3', '--kernel-trace', '--output-format', 'csv',
               '--output-directory', str(e.path / 'trace'), '--',
               str(ROOT / build['binary']), str(ROOT / item['coefficients']),
               str(item['width']), str(item['height']), str(output)]
    rc = e.command(command, 'profile-real-GPU-inverse-53-RCT', timeout=300)
    traces = list((e.path / 'trace').rglob('*kernel_trace.csv'))
    agents = list((e.path / 'trace').rglob('*agent_info.csv'))
    checks = [dict(check='profiled-command-success', passed=rc == 0),
              dict(check='profiled-exact-RGB', passed=output.is_file() and
                   digest(output) == item['expected_rgb_sha256'] == prior['decoded_rgb_sha256']),
              dict(check='single-trace-and-agent-map', passed=len(traces) == len(agents) == 1)]
    counts = Counter(); pci = set(); streams = set()
    if len(traces) == len(agents) == 1:
        lookup = {row['Node_Id']: row for row in csv.DictReader(agents[0].open())}
        allowed = {d['pci_bdf'] for d in observed['devices'] if d['physical_id'] == 1}
        for event in csv.DictReader(traces[0].open()):
            stage = next((name for name in STAGES if name in event['Kernel_Name']), None)
            if stage is None:
                continue
            counts[stage] += 1; streams.add(event['Stream_Id'])
            agent = lookup[event['Agent_Id'].split()[-1]]
            loc = int(agent['Location_Id'])
            location = f"{int(agent['Domain']):04x}:{loc >> 8:02x}:{(loc >> 3) & 31:02x}.{loc & 7}"
            pci.add(location)
            checks.append(dict(check=stage+'-actual-physical-GPU1',
                               passed=location in allowed and
                               int(event['End_Timestamp']) > int(event['Start_Timestamp']) and
                               int(event['Grid_Size_X']) > 0,
                               pci_bdf=location, stream_id=event['Stream_Id']))
        checks.append(dict(check='exact-three-stage-dispatches',
                           passed=counts == {name: 1 for name in STAGES}, counts=dict(counts)))
    status = 'PASSED' if all(c['passed'] for c in checks) else 'PROFILER_FAILED'
    result = dict(status=status, checks=checks, counts=dict(counts),
                  pci_bdfs=sorted(pci), stream_ids=sorted(streams), experiment_id=e.id)
    write(e.path / 'trace-result.json', result)
    result['evidence'] = e.finish(status, dict(status=status, checks=checks))
    write(REPORT, result)
    record('I6', 'JPEG2000 可逆 5/3+RCT 孤立组件 3 个真实 HIP kernel/物理 GPU1/重放 RGB：'+status+'；JP2 码流仍未实现。',
           [result['evidence']])
    print(status, result['counts'], result['pci_bdfs'])
    return int(status != 'PASSED')


if __name__ == '__main__':
    raise SystemExit(main())
