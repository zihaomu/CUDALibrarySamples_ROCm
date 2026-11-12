#!/usr/bin/env python3
"""Trace real HIP watershed stages and bind the traced products to validation."""
import collections
import csv
import json
import shutil

from experiment import ROOT, Experiment, digest, write
from image_progress import record
from image_watershed_build import dependencies
from snapshot import capture

KERNELS = ('select_parent', 'jump', 'render', 'mark_roots',
           'block_scan', 'scan_sums', 'compact_roots')
PROFILE = ROOT / 'migration/rewrite/image-watershed-profile.json'
BUILD = ROOT / 'migration/reports/image-watershed-build.json'
RUNS = ROOT / 'migration/reports/image-watershed-runs.json'
REPORT = ROOT / 'migration/reports/image-watershed-trace.json'


def main():
    sample = json.loads(PROFILE.read_text())['samples'][1]
    build = json.loads(BUILD.read_text())
    run = json.loads(RUNS.read_text())[1]
    binary = ROOT / build['binaries']['NPP+']['path']
    if digest(binary) != build['binaries']['NPP+']['sha256']:
        raise ValueError('binary identity mismatch')
    e = Experiment('I3', sample['sample_id'], 'rocm-real-kernel-trace',
                   sources=[__file__, PROFILE, BUILD, RUNS, *dependencies()],
                   parent=run['experiment_id'])
    write(e.path / 'backend.observed.json', capture())
    images = e.path / 'images'; images.mkdir()
    for item in sample['inputs']:
        shutil.copyfile(ROOT / 'NPP+/watershedSegmentation/images' / item['name'],
                        images / item['name'])
    work = e.path / 'work'; work.mkdir()
    rc = e.command(['rocprofv3', '--kernel-trace', '--output-format', 'csv',
                    '--output-directory', str(e.path / 'trace'), '--', str(binary)],
                   'actual-original-watershed-kernels', cwd=work, timeout=300)
    traced = list((e.path / 'trace').rglob('*kernel_trace.csv'))
    agents = list((e.path / 'trace').rglob('*agent_info.csv'))
    checks = [dict(check='profiled-original-entry-exit-zero', passed=rc == 0),
              dict(check='one-kernel-and-agent-trace',
                   passed=len(traced) == len(agents) == 1),
              dict(check='all-12-traced-products-identical-to-unprofiled',
                   passed=all((images / name).is_file() and
                              digest(images / name) == info['sha256']
                              for name, info in run['outputs'].items()))]
    counts = collections.Counter()
    if len(traced) == len(agents) == 1:
        agent_rows = {r['Node_Id']: r for r in csv.DictReader(agents[0].open())}
        allowed = {d['pci_bdf'] for d in json.loads(
            (e.path / 'backend.observed.json').read_text())['devices']
            if d['physical_id'] == 1}
        for row in csv.DictReader(traced[0].open()):
            name = row['Kernel_Name']
            stage = next((key for key in KERNELS if key in name), None)
            if stage is None:
                continue
            counts[stage] += 1
            agent = agent_rows[row['Agent_Id'].split()[-1]]
            loc = int(agent['Location_Id'])
            pci = f"{int(agent['Domain']):04x}:{loc >> 8:02x}:{(loc >> 3) & 31:02x}.{loc & 7}"
            checks.append(dict(check=f'actual-{stage}-dispatch-{counts[stage]}',
                passed=pci in allowed and
                       int(row['End_Timestamp']) > int(row['Start_Timestamp']) and
                       int(row['Grid_Size_X']) > 0,
                pci_bdf=pci))
        checks.append(dict(check='all-seven-HIP-stages-dispatched',
                           passed=all(counts[key] > 0 for key in KERNELS),
                           counts=dict(counts)))
    status = 'PASSED' if all(c['passed'] for c in checks) else 'PROFILER_FAILED'
    result = dict(status=status, return_code=rc, checks=checks,
                  kernel_counts=dict(counts), run_evidence=run['evidence'])
    write(e.path / 'trace-result.json', result)
    result['evidence'] = e.finish(status, dict(status=status, checks=checks))
    write(REPORT, result)
    record('I3', 'NPP+ watershed 真实 AMD GPU kernel trace/物理卡/7阶段/12产品哈希：'
           + status + '；算法语义差异仍待修正。', [result['evidence']])
    print(status, dict(counts))
    return int(status != 'PASSED')


if __name__ == '__main__':
    raise SystemExit(main())
