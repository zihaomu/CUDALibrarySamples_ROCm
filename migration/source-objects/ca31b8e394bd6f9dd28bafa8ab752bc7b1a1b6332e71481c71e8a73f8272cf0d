#!/usr/bin/env python3
"""Pre-register the first real JP2 codeblock MQ comparison before capture."""
import json
from experiment import ROOT, Experiment, digest, write
from image_progress import record

SOURCE = ROOT / 'nvJPEG2000/nvJPEG2000-Decoder/images/2k_image_lossless/2k_lossless.jp2'
LOCK = ROOT / 'migration/rewrite/image-j2k-openjpeg-reference-lock.json'
PROFILE = ROOT / 'migration/rewrite/image-j2k-real-mq-profile.json'


def main():
    if PROFILE.exists():
        raise ValueError('real-codeblock MQ contract already frozen')
    lock = json.loads(LOCK.read_text())
    profile = dict(status='FROZEN', phase='I6', original_jp2=str(SOURCE.relative_to(ROOT)),
                   original_jp2_sha256=digest(SOURCE), OpenJPEG_commit=lock['commit'],
                   selection='first actually decoded MQ-coded segment in first selected codeblock, one instrumented OpenJPEG CPU decode of the original JP2',
                   gates=dict(original_full_image_CPU_decode_success=True,
                              segment_bytes_and_context_symbol_pairs_frozen_before_HIP_replay=True,
                              GPU_all_MQ_symbols_bit_exact=True, physical_GPU1_trace=True),
                   scope='Real original-JP2 MQ arithmetic segment only. Context generation, EBCOT passes, packet parsing, full GPU decoder and original entrypoint still owed.')
    e = Experiment('I6', 'first-original-JP2-real-MQ-segment-contract', 'CPU-contract',
                   sources=[__file__, SOURCE, LOCK], parent=lock['evidence'].split('/')[-1])
    write(e.path / 'profile.json', profile)
    profile['evidence'] = e.finish('PASSED', dict(status='FROZEN', checks=[
        dict(check='original-JP2-input-SHA', passed=bool(profile['original_jp2_sha256'])),
        dict(check='pinned-OpenJPEG-reference', passed=lock['status'] == 'PINNED')]))
    write(PROFILE, profile)
    record('I6', '真实原始2k_lossless.jp2首个MQ码块段预登记：先捕获CPU码流/context+bit，再HIP逐bit核对；未实现完整码块。',
           [profile['evidence'], str(PROFILE.relative_to(ROOT))])
    print(profile['evidence'])


if __name__ == '__main__':
    main()
