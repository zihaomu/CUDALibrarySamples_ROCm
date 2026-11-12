#!/usr/bin/env python3
"""Exercise both resize entrypoints with the I5 GPU forward JPEG path."""
import json
import sys
from pathlib import Path
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

sys.path.insert(0, str(ROOT / 'tools/migration'))
from batches9_11_spec import GROUPS

REPORT = ROOT / 'migration/reports/image-jpeg-encoder-integration.json'
SOURCES = ('nvJPEG/Image-Resize/imageResize.cpp',
           'nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp')


def main():
    core = Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core')
    native = Path('/opt/rocm/core-10.1')
    jpeg = ROOT / 'build/cpu-codecs'
    overlay = ROOT / 'build/rocm-sdk-overlay'
    rows = []
    for source in SOURCES:
        frontend = ROOT / 'rocm/ported' / source
        deps = [frontend, ROOT / 'rocm/common/image/jpeg_decoder_v3.hpp',
                ROOT / 'rocm/common/image/jpeg_encoder_gpu.hpp',
                ROOT / 'rocm/common/image/progressive_jpeg.hpp',
                ROOT / 'rocm/common/batches_runtime.hpp',
                ROOT / 'migration/rewrite/image-jpeg-encoder-gpu-profile.json']
        e = Experiment('I5', source, 'rocm-original-entry-integration',
                       sources=[__file__, *deps, ROOT / 'tools/migration/batch10_case.py',
                                ROOT / 'tools/migration/batch10_reference.py',
                                ROOT / 'tools/moat/image_encoder_reference.py'])
        write(e.path / 'backend.observed.json', capture())
        binary = e.path / 'sample'
        cmd = ['hipcc', '--rocm-path=' + str(overlay), '--hip-path=' + str(overlay),
               '--rocm-device-lib-path=' + str(core / 'lib/llvm/amdgcn/bitcode'),
               '--offload-arch=gfx1201', '-std=c++17', '-O2', '-D__HIP_PLATFORM_AMD__',
               '-x', 'hip', str(frontend), '-o', str(binary),
               '-I' + str(ROOT / 'rocm/common'), '-I' + str(jpeg / 'include'),
               '-I' + str(core / 'include'), '-I' + str(native / 'include'),
               *['-I' + str(native / 'include' / n) for n in
                 ['hipblas', 'hipsolver', 'hipsparse', 'rocblas', 'rocsolver', 'rocsparse']],
               '-L' + str(jpeg / 'lib'), '-L' + str(core / 'lib'),
               '-Wl,-rpath,' + str(jpeg / 'lib'), '-Wl,-rpath,' + str(core / 'lib'),
               '-lamdhip64', '-lrocjpeg', '-ljpeg']
        rc = e.command(cmd, 'build-original-resize-entry', timeout=300)
        cases = []
        if rc == 0:
            for case in GROUPS['b10'][source]:
                folder = e.path / case
                folder.mkdir()
                run_rc = e.command([sys.executable,
                    str(ROOT / 'tools/migration/batch10_case.py'),
                    '--binary', str(binary), '--source', source,
                    '--case', case, '--output', str(folder)],
                    'original-' + case, timeout=600)
                validation_path = e.path / ('cpu-validation-' + case + '.json')
                cpu_rc = e.command([str(ROOT / 'build/image-cpu-venv/bin/python'),
                    str(ROOT / 'tools/moat/image_encoder_reference.py'),
                    '--source', source, '--case', case,
                    '--folder', str(folder), '--out', str(validation_path)],
                    'independent-CPU-' + case, timeout=600)
                validation = (json.loads(validation_path.read_text())
                              if validation_path.is_file() else
                              dict(status='FAILED', checks=[], cpu_return_code=cpu_rc))
                case_metadata = (json.loads((folder / 'case.json').read_text())
                                 if (folder / 'case.json').is_file() else {})
                products = [item for item in case_metadata.get('outputs', [])
                            if item['metadata'].get('postprocess')]
                encoder_claims = all(item['metadata'].get('gpu_software_encode') == 1 and
                                     item['metadata'].get('cpu_entropy_encode') == 1
                                     for item in products)
                row = dict(case=case, return_code=run_rc,
                           status=validation['status'], validation=validation,
                           output_count=len(case_metadata.get('outputs', [])),
                           encoded_products=len(products),
                           encoder_claims=encoder_claims)
                cases.append(row)
                write(e.path / ('validation-' + case + '.json'), row)
                print(source, case, run_rc, row['status'], len(products), flush=True)
        checks = [dict(check='original-C++-entry-build', passed=rc == 0),
                  dict(check='seven-original-case-groups', passed=len(cases) == 7),
                  dict(check='all-original-case-commands-and-independent-CPU-oracle',
                       passed=all(x['return_code'] == 0 and x['status'] == 'PASSED'
                                  for x in cases)),
                  dict(check='postprocess-JPEG-actually-uses-GPU-FDCT',
                       passed=sum(x['encoded_products'] for x in cases) > 0 and
                              all(x['encoder_claims'] for x in cases))]
        status = 'PASSED_SUBSET' if all(c['passed'] for c in checks) else 'FAILED'
        result = dict(source=source, status=status, checks=checks, cases=cases,
                      binary_sha256=digest(binary) if binary.is_file() else None,
                      dependencies={str(p.relative_to(ROOT)): digest(p) for p in deps},
                      experiment_id=e.id)
        write(e.path / 'integration.json', result)
        result['evidence'] = e.finish('EXECUTED' if status == 'PASSED_SUBSET' else
                                      'NUMERIC_MISMATCH', dict(status=status, checks=checks))
        rows.append(result)
        write(REPORT, rows)
        record('I5', source+' GPU DCT/量化+CPU entropy 原始七组流程与独立CPU验收：'+
               status+'；progressive 输出/metadata 和 GPU Huffman 尚未验收。',
               [result['evidence']])
    return int(any(x['status'] != 'PASSED_SUBSET' for x in rows))


if __name__ == '__main__':
    raise SystemExit(main())
