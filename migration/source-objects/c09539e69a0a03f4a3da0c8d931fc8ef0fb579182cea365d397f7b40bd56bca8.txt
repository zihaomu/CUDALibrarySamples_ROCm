#!/usr/bin/env python3
"""Publish measured watershed implementation gaps without claiming full support."""
import json

from audit import check as audit_check
from experiment import ROOT, digest, write
from image_progress import record


def load(name):
    return json.loads((ROOT / 'migration/reports' / name).read_text())


def seal(reference):
    directory = ROOT / reference
    if not directory.is_dir() or audit_check(directory):
        raise ValueError('unsealed watershed evidence: ' + reference)


def main():
    profile = json.loads((ROOT / 'migration/rewrite/image-watershed-profile.json').read_text())
    build = load('image-watershed-build.json')
    runs = load('image-watershed-runs.json')
    cpu = load('image-watershed-reference.json')
    native = load('image-watershed-native-comparison.json')
    negative = load('image-watershed-negative.json')
    trace = load('image-watershed-trace.json')
    if (len(profile['samples']) != 2 or build['status'] != 'BUILT' or
        any(digest(ROOT / p) != sha for p, sha in build['dependencies'].items())):
        raise ValueError('current fully built watershed sources required')
    if not (len(runs) == len(cpu) == len(negative) == 2):
        raise ValueError('complete watershed report rows required')
    for row in runs + cpu + negative:
        seal(row['evidence'])
    for row in [build, native, trace]:
        seal(row['evidence'])
    if (any(r['status'] != 'EXECUTED' for r in runs) or
        any(r['status'] != 'PASSED' for r in cpu + negative) or
        native['status'] != 'OBSERVED_ALGORITHM_VARIANT' or len(native['rows']) != 22 or
        trace['status'] != 'PASSED' or
        not all(c['passed'] for c in trace['checks'])):
        raise ValueError('watershed project result or native gap not fully evidenced')
    catalog = json.loads((ROOT / 'migration/samples.yaml').read_text())
    for sample in profile['samples']:
        sample_id = sample['sample_id']
        family = sample_id.split('/')[0]
        run = next(r for r in runs if r['sample_id'] == sample_id)
        ref = next(r for r in cpu if r['sample_id'] == sample_id)
        neg = next(r for r in negative if r['family'] == family)
        native_rows = [r for r in native['rows'] if r['family'] == family]
        seg = [r for r in native_rows if r['product'].startswith('Segmented_') or
               '_Segments_8Way_' in r['product']]
        lowest = min(r['equal_fraction'] for r in seg)
        record_row = next(r for r in catalog['samples'] if r['id'] == sample_id)
        required = ['original-products-and-names', 'independent-project-CPU-all-output-bytes',
                    'missing-input-rejection', 'real-HIP-kernel-trace',
                    'NPP-native-algorithm-parity', 'fixed-commit-cold-and-independent-review']
        passed = required[:3] + (required[3:4] if family == 'NPP+' else [])
        record_row.update(status='PARTIAL', level='L3', reason_code='SEMANTIC_GAP',
            actual_library='Project HIP eight-neighbor gradient descent and root-label compression',
            backend_library='project HIP image watershed',
            equivalence='ALGORITHM_VARIANT',
            reason=f'完整原始入口及 {len(sample["inputs"])} 张图/{len(sample["products"])} 件产品已在 AMD GPU 执行，'
                   f'独立 NumPy 模型逐字节一致，缺图拒绝通过；原生 NPP 最低分割像素一致率 {lowest:.4f}，'
                   '平台区归属和边界语义未达到原例等价，当前只能算部分实现。',
            required_cases=required, passed_cases=passed,
            cuda_baseline='PASSED', cuda_comparison='OBSERVED_ALGORITHM_VARIANT',
            cuda_comparison_mode='ALGORITHM_VARIANT',
            cuda_comparison_reason='原始5090完整输入/产品与HIP逐像素对照见 image-watershed-native-comparison.json；'
                                   '标签ID与分割边界均有显著差异。',
            active_batch='I3',
            retry_condition='重写分桶浸没、平台区、压紧标签和边界模式；预登记原生分区/边界/像素阈值后重新独立验收及冷检出。',
            next_step='I3 原生语义收口；I4–I8 JPEG/JPEG2000 完整入口。',
            reproduce='python3 tools/moat/image_watershed_contracts.py\n'
                      'python3 tools/moat/image_watershed_build.py\n'
                      'python3 tools/moat/image_watershed_run.py\n'
                      'python3 tools/moat/image_watershed_reference.py\n'
                      'python3 tools/moat/image_watershed_native_compare.py\n'
                      'python3 tools/moat/image_watershed_negative.py\n'
                      'python3 tools/moat/image_watershed_trace.py')
        record_row.pop('selected_validation', None)
        for evidence in [build['evidence'], run['evidence'], ref['evidence'],
                         neg['evidence'], native['evidence'], trace['evidence'],
                         'migration/reports/image-watershed.md']:
            if evidence not in record_row['evidence']:
                record_row['evidence'].append(evidence)
    write(ROOT / 'migration/samples.yaml', catalog)
    lines = ['# Watershed：HIP 实验与未收口语义', '',
        '两个原始入口已运行所有原图，22 件输出与独立项目 CPU 模型逐字节一致。'
        '这只证明项目八邻域下降算法正确执行；NPP 的浸没/平台区与边界语义仍有明显差异，'
        '因此两项保持 **PARTIAL**，不列入整例通过数。', '',
        '| 模块 | 原图/产品 | 项目 CPU | 原生分割最小一致率 | 当前状态 |',
        '| --- | ---: | --- | ---: | --- |']
    for sample in profile['samples']:
        family = sample['sample_id'].split('/')[0]
        rows = [r for r in native['rows'] if r['family'] == family and
                (r['product'].startswith('Segmented_') or '_Segments_8Way_' in r['product'])]
        lines.append(f'| {family} | {len(sample["inputs"])}/{len(sample["products"])} | '
                     f'全部逐字节一致 | {min(r["equal_fraction"] for r in rows):.2%} | PARTIAL |')
    lines += ['', 'NPP+ 原生边界模式的最低逐像素一致率为 '
              f'{min(r["equal_fraction"] for r in native["rows"] if r["family"] == "NPP+" and "Boundaries" in r["product"]):.2%}。'
              '原生标签 ID 不能直接比较，邻域分区一致率见完整 JSON。', '',
              '证据： [合同](../rewrite/image-watershed-profile.json)、'
              '[AMD 执行](image-watershed-runs.json)、[独立 CPU](image-watershed-reference.json)、'
              '[22 产品原生比较](image-watershed-native-comparison.json)、'
              '[缺图拒绝](image-watershed-negative.json)、[真实 GPU trace](image-watershed-trace.json)。', '',
              '下一步：实现分桶浸没/平台区分配，对 5090 原例预固定可接受的分割、'
              '边界和标签分区阈值后重做完整资格。']
    (ROOT / 'migration/reports/image-watershed.md').write_text('\n'.join(lines) + '\n')
    record('I3', '两个 watershed 完整 HIP 文件流程已实现并验证，但原生分割/边界差异较大，'
           '主表和算子支持表改为 PARTIAL；待浸没与平台区算法重写，不计入整例通过。',
           ['migration/reports/image-watershed.md', native['evidence']])
    print('Published watershed PARTIAL 2/2')


if __name__ == '__main__':
    main()
