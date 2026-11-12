#!/usr/bin/env python3
"""Tie actual I5 encoder GPU kernels to the selected physical AMD device."""
import collections
import csv
import json
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture


def main():
    profile = json.loads((ROOT / 'migration/rewrite/image-jpeg-encoder-gpu-profile.json').read_text())
    build = json.loads((ROOT / 'migration/reports/image-jpeg-encoder-build.json').read_text())
    runs = json.loads((ROOT / 'migration/reports/image-jpeg-encoder-runs.json').read_text())
    item = next(x for x in profile['inputs'] if x['case'] == 'odd-420')
    original = next(x for x in runs if x['case'] == 'odd-420')
    e = Experiment('I5', 'JPEG-encoder-real-GPU-color-FDCT-trace', 'rocm-trace',
                   sources=[__file__, ROOT / item['path'],
                            ROOT / 'rocm/common/image/jpeg_encoder_gpu.hpp',
                            ROOT / 'rocm/probes/image/jpeg_encoder_gpu.hip'],
                   parent=original['experiment_id'])
    observed = capture()
    write(e.path / 'backend.observed.json', observed)
    output = e.path / 'output.jpg'
    command = ['rocprofv3', '--kernel-trace', '--output-format', 'csv',
               '--output-directory', str(e.path / 'trace'), '--',
               str(ROOT / build['binary']), str(ROOT / item['path']),
               str(item['width']), str(item['height']), str(item['quality']),
               item['subsampling'], str(output)]
    rc = e.command(command, 'profile-GPU-JPEG-color-FDCT-quant', timeout=300)
    traces = list((e.path / 'trace').rglob('*kernel_trace.csv'))
    agents = list((e.path / 'trace').rglob('*agent_info.csv'))
    checks = [dict(check='profile-command-exit-zero', passed=rc == 0),
              dict(check='one-trace-and-agent-map', passed=len(traces) == len(agents) == 1),
              dict(check='profiled-bitstream-identical', passed=output.is_file() and
                   digest(output) == original['jpeg_sha256'])]
    counts = collections.Counter()
    if len(traces) == len(agents) == 1:
        lookup = {row['Node_Id']: row for row in csv.DictReader(agents[0].open())}
        allowed = {d['pci_bdf'] for d in observed['devices'] if d['physical_id'] == 1}
        for row in csv.DictReader(traces[0].open()):
            stage = next((x for x in ('rgb_to_plane', 'forward_dct_quantize')
                          if x in row['Kernel_Name']), None)
            if not stage:
                continue
            counts[stage] += 1
            agent = lookup[row['Agent_Id'].split()[-1]]
            location = int(agent['Location_Id'])
            pci = f"{int(agent['Domain']):04x}:{location >> 8:02x}:{(location >> 3) & 31:02x}.{location & 7}"
            checks.append(dict(check=f'{stage}-physical-GPU1-{counts[stage]}',
                               passed=pci in allowed and
                               int(row['End_Timestamp']) > int(row['Start_Timestamp']) and
                               int(row['Grid_Size_X']) > 0, pci_bdf=pci))
        checks.append(dict(check='three-color-plus-three-FDCT-dispatches',
                           passed=counts['rgb_to_plane'] == counts['forward_dct_quantize'] == 3,
                           counts=dict(counts)))
    status = 'PASSED' if all(x['passed'] for x in checks) else 'PROFILER_FAILED'
    result = dict(status=status, return_code=rc, checks=checks, counts=dict(counts),
                  experiment_id=e.id)
    write(e.path / 'trace-result.json', result)
    result['evidence'] = e.finish(status, dict(status=status, checks=checks))
    write(ROOT / 'migration/reports/image-jpeg-encoder-trace.json', result)
    record('I5', 'JPEG encoder GPU 实际色彩/降采样和 FDCT/量化各三次内核、物理 GPU1 及 bitstream 重放：'+status+'。',
           [result['evidence']])
    print(status, dict(counts))
    return int(status != 'PASSED')


if __name__ == '__main__':
    raise SystemExit(main())
