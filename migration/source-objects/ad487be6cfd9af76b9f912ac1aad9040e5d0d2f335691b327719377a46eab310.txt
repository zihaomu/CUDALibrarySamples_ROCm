#!/usr/bin/env python3
"""Synchronize the image plan's live snapshot and per-entry statuses with the catalog."""
import collections
import datetime as dt
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

from experiment import ROOT

START = re.compile(r'^截至 20\d\d-\d\d-\d\d，本计划四模块 .*$', re.M)
ROW = re.compile(r'^(\| \[([^\]]+)\]\([^)]*\) \| )([A-Z_]+)( \| [^|]+ \| )([^|]*)( \|)$', re.M)
WATERSHED = ('NPP/watershedSegmentation/', 'NPP+/watershedSegmentation/')


def main():
    catalog = json.loads((ROOT / 'migration/samples.yaml').read_text())
    planned = json.loads((ROOT / 'migration/rewrite/image-libraries-plan.json').read_text())
    ids = {item['sample_id'] for item in planned['samples']}
    samples = [s for s in catalog['samples'] if s['id'] in ids]
    by_source = {s['source']: s for s in samples}
    if len(samples) != 26 or len(by_source) != 26:
        raise ValueError('all 26 stable image entrypoints required')
    counts = collections.Counter(s['status'] for s in samples)
    project = collections.Counter(s['status'] for s in catalog['samples'])
    module_counts = {m: collections.Counter(s['status'] for s in samples if s['id'].startswith(m + '/'))
                     for m in ['NPP', 'NPP+', 'nvJPEG', 'nvJPEG2000']}
    today = dt.datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()
    snapshot = (f'截至 {today}，本计划四模块 **{counts["PASSED"]}/26 整例通过、'
                f'{counts["PARTIAL"]} PARTIAL、{counts["FAILED"]} FAILED**：' +
                '、'.join(f'{m} {module_counts[m]["PASSED"]}/{sum(module_counts[m].values())}'
                         for m in module_counts) +
                '。I3 两个 watershed 已有完整 HIP 文件入口及独立 CPU 逐字节结果，'
                '但原生分割/边界语义差异显著，保持 PARTIAL；I4–I8 JPEG/JPEG2000 整例目标仍未完成。'
                f'全项目为 {project["PASSED"]} PASSED、{project["PARTIAL"]} PARTIAL、'
                f'{project["FAILED"]} FAILED。详细资格及失败原因见项目的 '
                '`migration/reports/image-libraries-progress.md` 和 '
                '`migration/reports/support-log-index.md`。')
    path = ROOT.parent / 'doc/cuda_samples_on_rocm_image_libraries_plan.md'
    body = path.read_text()
    body, n = START.subn(snapshot, body, count=1)
    if n != 1:
        raise ValueError('plan snapshot not found')
    touched = set()
    def replace(match):
        prefix, source, _, middle, description, suffix = match.groups()
        if source not in by_source:
            return match.group(0)
        touched.add(source)
        sample = by_source[source]
        if source.startswith(WATERSHED):
            description = ('项目 HIP 八邻域下降/标签与边界输出；原图与独立 CPU 逐字节通过，'
                           '原生 NPP 分割/平台区和边界差异待修正；'
                           '[实测与日志](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/migration/reports/image-watershed.md)')
        elif sample['status'] == 'PASSED' and sample.get('actual_library'):
            description = sample['actual_library']
        return prefix + sample['status'] + middle + description + suffix
    body = ROW.sub(replace, body)
    if touched != set(by_source):
        raise ValueError('plan did not contain all 26 image entrypoints')
    path.write_text(body)
    (ROOT / 'migration/image-libraries-plan.md').write_text(body)
    print('Synced 26 image statuses:', dict(counts), 'project:', dict(project))


if __name__ == '__main__':
    main()
