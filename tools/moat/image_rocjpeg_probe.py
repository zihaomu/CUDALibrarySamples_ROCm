#!/usr/bin/env python3
"""Run real rocJPEG file decoding in the locked environment; retain unsupported files."""
import json
from pathlib import Path
from experiment import ROOT, Experiment, write, digest
from snapshot import capture
from image_progress import record

def main():
    source = ROOT/'rocm/probes/image/rocjpeg_decode.cpp'
    inputs = ROOT/'nvJPEG/nvJPEG-Decoder/input_images'
    files = sorted(p for p in inputs.iterdir() if p.is_file())
    e = Experiment('I0', 'rocJPEG-original-file-decode', 'rocm-probe', sources=[__file__, source, *files])
    write(e.path/'backend.observed.json', capture())
    core = Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core')
    overlay = ROOT/'build/rocm-sdk-overlay'
    binary = e.path/'decode'
    outputs = e.path/'outputs'
    command = ['hipcc', '--rocm-path='+str(overlay), '--hip-path='+str(overlay),
               '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'), '--offload-arch=gfx1201',
               '-std=c++17', '-O2', '-I/opt/rocm/core-10.1/include', str(source),
               '-L'+str(core/'lib'), '-Wl,-rpath,'+str(core/'lib'), '-lrocjpeg', '-o', str(binary)]
    rc = e.command(command, 'compile-actual-rocJPEG-probe', timeout=300)
    rows = []
    if rc == 0:
        write(e.path/'binary.json', dict(sha256=digest(binary)))
        rc = e.command([str(binary), str(inputs), str(outputs)], 'decode-original-JPEG-files', timeout=300)
        for line in (e.path/'logs/0002-decode-original-JPEG-files.stdout.log').read_text().splitlines():
            if line.startswith('{'): rows.append(json.loads(line))
    result = dict(status='OBSERVED' if rc == 0 else 'FAILED', return_code=rc,
                  input_files={str(p.relative_to(ROOT)):digest(p) for p in files}, results=rows,
                  outputs={str(p.relative_to(e.path)):dict(sha256=digest(p),bytes=p.stat().st_size)
                           for p in outputs.glob('*')},
                  scope='Actual library capabilities only. CPU/native pixel comparison and final GPU codec qualification remain separate.')
    write(e.path/'decode-result.json', result)
    ref = e.finish('OBSERVED' if rc == 0 else 'PROBE_FAILED')
    write(ROOT/'migration/reports/image-I0-rocJPEG-files.json', dict(**result, evidence=ref))
    successful = sum(r.get('decode') == 0 for r in rows)
    record('I0', f'rocJPEG原始JPEG逐文件实际解码调查完成：{successful}/{len(files)}文件取得GPU输出；失败格式和HYBRID状态逐项保留，尚未作数值资格。', [ref])
    print(json.dumps(result))
    return rc

if __name__ == '__main__': raise SystemExit(main())
