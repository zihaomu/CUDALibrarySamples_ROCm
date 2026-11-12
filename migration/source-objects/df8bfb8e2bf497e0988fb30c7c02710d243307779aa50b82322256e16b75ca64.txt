#!/usr/bin/env python3
"""Verify progressive JPEG IDCT and RGB kernels on the selected physical GPU."""
import collections
import csv
import json

from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture


def main():
    build = json.loads((ROOT / 'migration/reports/image-progressive-build.json').read_text())
    runs = json.loads((ROOT / 'migration/reports/image-progressive-runs.json').read_text())
    profile = json.loads((ROOT / 'migration/rewrite/image-progressive-gpu-profile.json').read_text())
    original = next(r for r in runs if r['input'] == 'cat.jpg')
    item = next(r for r in profile['inputs'] if r['path'].endswith('/cat.jpg'))
    e = Experiment('I4', 'progressive-JPEG-real-GPU-IDCT-and-color-trace',
                   'rocm-trace', sources=[__file__,
                   ROOT / 'rocm/probes/image/jpeg_progressive_gpu.hip',
                   ROOT / 'migration/rewrite/image-progressive-gpu-profile.json',
                   ROOT / item['path']], parent=original['experiment_id'])
    write(e.path / 'backend.observed.json', capture())
    gpu = e.path / 'gpu.rgb'; cpu = e.path / 'cpu.rgb'
    rc = e.command(['rocprofv3', '--kernel-trace', '--output-format', 'csv',
                    '--output-directory', str(e.path / 'trace'), '--',
                    str(ROOT / build['binary']), str(ROOT / item['path']), str(gpu), str(cpu)],
                   'trace-actual-progressive-pixel-kernels', timeout=300)
    traces = list((e.path / 'trace').rglob('*kernel_trace.csv'))
    agents = list((e.path / 'trace').rglob('*agent_info.csv'))
    checks = [dict(check='trace-command-exit-zero', passed=rc == 0),
              dict(check='one-kernel-trace-and-agent-map', passed=len(traces) == len(agents) == 1),
              dict(check='traced-GPU-pixels-identical',
                   passed=gpu.is_file() and digest(gpu) == original['gpu_sha256'])]
    counts = collections.Counter()
    if len(traces) == len(agents) == 1:
        lookup = {r['Node_Id']: r for r in csv.DictReader(agents[0].open())}
        allowed = {d['pci_bdf'] for d in json.loads(
            (e.path / 'backend.observed.json').read_text())['devices']
            if d['physical_id'] == 1}
        for row in csv.DictReader(traces[0].open()):
            name = row['Kernel_Name']
            stage = next((k for k in ['inverse_dct', 'convert_rgb'] if k in name), None)
            if not stage:
                continue
            counts[stage] += 1
            agent = lookup[row['Agent_Id'].split()[-1]]
            location = int(agent['Location_Id'])
            pci = f"{int(agent['Domain']):04x}:{location >> 8:02x}:{(location >> 3) & 31:02x}.{location & 7}"
            checks.append(dict(check=f'{stage}-actual-GPU-{counts[stage]}',
                passed=pci in allowed and
                       int(row['End_Timestamp']) > int(row['Start_Timestamp']) and
                       int(row['Grid_Size_X']) > 0, pci_bdf=pci))
        checks.append(dict(check='three-IDCT-plus-one-color-dispatch',
            passed=counts['inverse_dct'] == 3 and counts['convert_rgb'] == 1,
            counts=dict(counts)))
    status = 'PASSED' if all(c['passed'] for c in checks) else 'PROFILER_FAILED'
    result = dict(status=status, return_code=rc, checks=checks,
                  kernel_counts=dict(counts), original_run=original['evidence'])
    write(e.path / 'trace-result.json', result)
    result['evidence'] = e.finish(status, dict(status=status, checks=checks))
    write(ROOT / 'migration/reports/image-progressive-trace.json', result)
    record('I4', '原始 progressive cat.jpg 真实 AMD GPU trace 检查 3 个 IDCT + 1 个色彩 kernel、'
           '物理 GPU 与未 profile 全像素 SHA：' + status + '；完整入口待接入。',
           [result['evidence']])
    print(status, dict(counts))
    return int(status != 'PASSED')


if __name__ == '__main__':
    raise SystemExit(main())
