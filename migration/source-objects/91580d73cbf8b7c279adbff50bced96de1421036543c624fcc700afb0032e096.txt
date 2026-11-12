#!/usr/bin/env python3
"""Trace optimized Huffman histogram and entropy on physical AMD GPU1."""
import collections
import csv
import json
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

PROFILE = ROOT / 'migration/rewrite/image-jpeg-opt-huffman-profile.json'
BUILD = ROOT / 'migration/reports/image-jpeg-opt-huffman-build.json'
RUNS = ROOT / 'migration/reports/image-jpeg-opt-huffman-runs.json'
REPORT = ROOT / 'migration/reports/image-jpeg-opt-huffman-trace.json'
STAGES = ('rgb_to_plane', 'forward_dct_quantize', 'gather_mcu_coefficients',
          'histogram', 'encode_blocks', 'prefix_bits', 'pack_bytes',
          'prefix_stuff', 'scatter_stuff')


def main():
    profile = json.loads(PROFILE.read_text())
    build = json.loads(BUILD.read_text())
    runs = json.loads(RUNS.read_text())
    if len(runs) != 5 or any(row['status'] != 'PASSED' for row in runs):
        raise ValueError('four numeric and one negative optimized JPEG gates required')
    item = profile['cases'][0]
    original = runs[0]
    e = Experiment('I5', 'optimized-JPEG-GPU-histogram-entropy-trace', 'rocm-trace',
                   sources=[__file__, PROFILE, BUILD, RUNS, ROOT / item['path'],
                            ROOT / 'rocm/common/image/jpeg_opt_full_gpu.hpp',
                            ROOT / 'rocm/common/image/jpeg_optimal_huffman.hpp'],
                   parent=original['evidence'].split('/')[-1])
    observed = capture()
    write(e.path / 'backend.observed.json', observed)
    output = e.path / 'output.jpg'
    rc = e.command(['rocprofv3', '--kernel-trace', '--output-format', 'csv',
                    '--output-directory', str(e.path / 'trace'), '--',
                    str(ROOT / build['binary']), str(ROOT / item['path']),
                    str(item['width']), str(item['height']), str(item['quality']),
                    item['subsampling'], str(output)], 'profile-optimized-JPEG-GPU-stages', timeout=300)
    traces = list((e.path / 'trace').rglob('*kernel_trace.csv'))
    agents = list((e.path / 'trace').rglob('*agent_info.csv'))
    checks = [dict(check='profile-command-success', passed=rc == 0),
              dict(check='profiled-JPEG-identical', passed=output.is_file() and
                   digest(output) == original['output_sha256']),
              dict(check='one-trace-and-agent-map', passed=len(traces) == len(agents) == 1)]
    counts = collections.Counter(); pci_bdfs = set()
    if len(traces) == len(agents) == 1:
        lookup = {row['Node_Id']: row for row in csv.DictReader(agents[0].open())}
        allowed = {device['pci_bdf'] for device in observed['devices'] if device['physical_id'] == 1}
        for event in csv.DictReader(traces[0].open()):
            stage = next((name for name in STAGES if name in event['Kernel_Name']), None)
            if not stage:
                continue
            counts[stage] += 1
            agent = lookup[event['Agent_Id'].split()[-1]]
            loc = int(agent['Location_Id'])
            pci = f"{int(agent['Domain']):04x}:{loc >> 8:02x}:{(loc >> 3) & 31:02x}.{loc & 7}"
            pci_bdfs.add(pci)
            checks.append(dict(check=stage + '-actual-GPU1-' + str(counts[stage]),
                               passed=pci in allowed and
                               int(event['End_Timestamp']) > int(event['Start_Timestamp']) and
                               int(event['Grid_Size_X']) > 0, pci_bdf=pci))
        expected = {'rgb_to_plane': 3, 'forward_dct_quantize': 3,
                    **{name: 1 for name in STAGES[2:]}}
        checks.append(dict(check='all-nine-stage-kernel-counts',
                           passed=counts == expected, counts=dict(counts)))
    status = 'PASSED' if all(check['passed'] for check in checks) else 'PROFILER_FAILED'
    result = dict(status=status, checks=checks, counts=dict(counts),
                  pci_bdfs=sorted(pci_bdfs), return_code=rc)
    write(e.path / 'trace-result.json', result)
    result['evidence'] = e.finish(status, dict(status=status, checks=checks))
    write(REPORT, result)
    record('I5', '优化 Huffman 原型真实 GPU1 的直方图、FDCT/量化、MCU/Huffman/pack/stuff trace：' + status +
           '；保持孤立阶段，不升级原入口。', [result['evidence']])
    print(status, dict(counts), sorted(pci_bdfs))
    return int(status != 'PASSED')


if __name__ == '__main__':
    raise SystemExit(main())
