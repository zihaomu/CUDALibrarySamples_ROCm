#!/usr/bin/env python3
"""Generate the fixed MQ state transition table from pinned OpenJPEG v2.5.4."""
import json
import re
from experiment import ROOT, Experiment, digest, write
from image_progress import record

SOURCE = ROOT / 'build/openjpeg-v2.5.4/src/lib/openjp2/mqc.c'
LOCK = ROOT / 'migration/rewrite/image-j2k-openjpeg-reference-lock.json'
TARGET = ROOT / 'rocm/backends/codec/jpeg2000/mq_states.hpp'
LICENSE = ROOT / 'rocm/backends/codec/jpeg2000/OPENJPEG-LICENSE'
REPORT = ROOT / 'migration/reports/image-j2k-mq-table.json'


def main():
    lock = json.loads(LOCK.read_text())
    if digest(SOURCE) != lock['files']['src/lib/openjp2/mqc.c']:
        raise ValueError('unpinned OpenJPEG MQ table source')
    raw = SOURCE.read_text().split('static const opj_mqc_state_t mqc_states[47 * 2] = {', 1)[1].split('};', 1)[0]
    rows = re.findall(r'\{(0x[0-9a-f]+),\s*([01]),\s*&mqc_states\[(\d+)\],\s*&mqc_states\[(\d+)\]\}', raw)
    if len(rows) != 94 or any(int(x) >= 94 for row in rows for x in row[2:]):
        raise ValueError('unexpected OpenJPEG MQ transition table')
    text = '''// SPDX-License-Identifier: BSD-2-Clause
// Numeric MQ probability and transition table derived from OpenJPEG v2.5.4,
// commit 6c4a29b00211eb0430fa0e5e890f1ce5c80f409f, src/lib/openjp2/mqc.c.
// Original copyright and redistribution terms: OPENJPEG-LICENSE.
#pragma once
#include <hip/hip_runtime.h>
#include <stdint.h>
namespace image_j2k_mq {
struct State { uint32_t qeval; uint32_t mps; uint32_t nmps; uint32_t nlps; };
__device__ __constant__ State states[94] = {
''' + ''.join(f'    {{{a}, {b}, {c}, {d}}},\n' for a, b, c, d in rows) + '''};
} // namespace image_j2k_mq
'''
    TARGET.write_text(text)
    LICENSE.write_bytes((ROOT / 'build/openjpeg-v2.5.4/LICENSE').read_bytes())
    e = Experiment('I6', 'OpenJPEG-MQ-fixed-transition-table-and-license', 'source-derivation',
                   sources=[__file__, SOURCE, LOCK, LICENSE, TARGET],
                   parent=lock['evidence'].split('/')[-1])
    result = dict(status='DERIVED', entries=len(rows), source_sha256=digest(SOURCE),
                  table_sha256=digest(TARGET), license_sha256=digest(LICENSE),
                  source_commit=lock['commit'])
    evidence = e.finish('PASSED', dict(status='PASSED', checks=[
        dict(check='94-bounded-MQ-states', passed=len(rows) == 94),
        dict(check='matching-BSD-license', passed=digest(LICENSE) == lock['license_sha256'])]))
    result['evidence'] = evidence
    write(REPORT, result)
    record('I6', '固定 OpenJPEG 2.5.4 的94项 MQ 状态表及 BSD 许可，派生 HIP 只读表；尚未实现或通过整图解码。',
           [evidence, str(REPORT.relative_to(ROOT))])
    print(evidence)


if __name__ == '__main__':
    main()
