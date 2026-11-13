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
    watershed_complete = all(s['status'] == 'PASSED' for s in samples
                             if s['source'].startswith(WATERSHED))
    watershed_summary = ('I3 两个 watershed 已完成原入口与全GPU实现，按公开算法变体验收；'
                         'marker分区差异及NPP+三个固定坡度的原生不一致保留详细记录。'
                         if watershed_complete else
                         'I3 两个 watershed 尚待完整合同资格，已有组件/文件流程证明不替代整例验收。')
    today = dt.datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()
    snapshot = (f'截至 {today}，本计划四模块 **{counts["PASSED"]}/26 整例通过、'
                f'{counts["PARTIAL"]} PARTIAL、{counts["FAILED"]} FAILED**：' +
                '、'.join(f'{m} {module_counts[m]["PASSED"]}/{sum(module_counts[m].values())}'
                         for m in module_counts) +
                '。' + watershed_summary + 'I4–I8 JPEG/JPEG2000 剩余整例目标仍未完成。'
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
            description = ('项目 HIP 严格下降/有向根图标签、GPU压紧与完整边界输出；'
                           + ('完整原入口、60输入四布局及固定提交冷验收通过；marker算法变体与三项NPP+原生差异明确保留；'
                              if sample['status'] == 'PASSED' else '完整资格尚待验收；')
                           + '[实测与日志](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/migration/reports/image-completion-IMG-02.md)')
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
