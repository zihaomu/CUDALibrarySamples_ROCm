#!/usr/bin/env python3
"""Freeze source-level full encoder obligations without rewriting old subset contracts."""
import json
from experiment import ROOT, Experiment, digest, write
from image_completion_progress import record

PROFILE = ROOT/'migration/rewrite/image-completion-encoder-contract.json'

def main():
    if PROFILE.exists():
        raise ValueError('completion encoder contract already frozen')
    source = ROOT/'nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp'
    cmake = source.parent/'CMakeLists.txt'
    old = ROOT/'migration/rewrite/image-jpeg-encoder-instances-profile.json'
    inputs = json.loads(old.read_text())['inputs']
    cases = [
        dict(id='natural-three', args=['-j','2','-s','2','-b','gpu','-q','75'], count=3, quality=75, sampling=2, output=True),
        dict(id='repeat-seven', args=['-n','7','-j','2','-s','4','-b','gpu','-q','75'], count=7, quality=75, sampling=2, output=True),
        dict(id='optimized-444', args=['-j','2','-s','2','-b','gpu','-q','90','-p','-f'], count=3, quality=90, sampling=0, output=True),
        dict(id='quality-clamp-low', args=['-j','2','-s','2','-b','gpu','-q','0'], count=3, quality=1, sampling=2, output=True),
        dict(id='quality-clamp-high', args=['-j','2','-s','2','-b','gpu','-q','101'], count=3, quality=100, sampling=2, output=True),
        dict(id='download-no-write', args=['-j','2','-s','2','-b','gpu','-d'], count=3, quality=80, sampling=2, output=False),
        dict(id='device-only', args=['-j','2','-s','2','-b','gpu'], count=3, quality=80, sampling=2, output=False),
    ]
    obligations = [
        dict(feature='input', original='Required recursive BMP/BMP directory, natural order; n>0 truncates file list before cycling.', current_gap='Adapter does not truncate source list before state-driven image-count increase.'),
        dict(feature='quality', original='atoi then clamp to [1,100], default80.', current_gap='Adapter rejects q0/q101; historical invalid-quality case is a subset mismatch, not native parity.'),
        dict(feature='download', original='-d downloads; -o implies download+write; neither keeps encoded payload on device.', current_gap='Adapter always downloads and creates/removes a temporary file.'),
        dict(feature='auto-threads', original='Absent -j calibrates throughput; -j0 hardware_concurrency; user -j positive is fixed.', current_gap='Adapter uses min(2,image count), with no calibration.'),
        dict(feature='states-and-repeats', original='n clamped >=0, r>=1, s>=0; auto states=max(1,engines*2,threads); images>=states.', current_gap='Adapter rejects negative n/r and imposes undocumented fixed caps. Lifecycle still per-call.'),
        dict(feature='backend', original='AUTO enables available GPU/hardware; -b gpu,hardware or both. Report actual engines.', current_gap='AMD software GPU mapped; forced NVIDIA-only hardware capability remains unavailable and must be explicit.'),
        dict(feature='resource-pipeline', original='State-local streams and two image buffers; overlapping transfer and encode; single-input preallocation.', current_gap='Adapter has rotating streams but synchronous encode, per-image allocation and pageable host buffers.'),
        dict(feature='optimized', original='-f optimized Huffman; -p 4:4:4; default 4:2:0.', current_gap='Pixel chain/entropy implemented; lifetime, large-scale guards and production prefix still owed.'),
        dict(feature='help-errors', original='No args or -h anywhere prints usage. Missing input and negative states fail.', current_gap='Adapter only handles standalone -h; corrupt BMP and allocation-failure cleanup need complete verification.'),
    ]
    e = Experiment('I0','completion-encoder-source-contract','CPU-contract',sources=[__file__,source,cmake,old,*[ROOT/x['path'] for x in inputs]])
    checks = [dict(check='original-source-and-all-existing-fixtures-preserved', passed=all(digest(ROOT/x['path'])==x['sha256'] for x in inputs))]
    data = dict(status='FROZEN',scope='Full source obligations plus first seven bounded native probes; NOT a full qualification matrix.',
                source=str(source.relative_to(ROOT)),source_sha256=digest(source),cmake_sha256=digest(cmake),
                original_lines='parse/main 850-1030; state/worker/autocalibration reviewed in full source',
                input_profile=str(old.relative_to(ROOT)),inputs=inputs,native_probe_cases=cases,obligations=obligations,
                acceptance=dict(original_immutable=True,all_products_decodable=True,geometry_sampling_quality_exact=True,
                    gpu_entropy_required=True,device_only_no_payload_download=True,async_overlap_trace_required=True,
                    byte_equality_to_native_required=False,pixel_tolerance='Not frozen yet: native pilot is observation only; freeze independent retained set before final candidate qualification.'),
                outstanding_matrix=['automatic-calibration','j0 and state-count interplay','n-lower-than-input-count',
                    'r0/n-negative clamps','help anywhere','backend hardware-only behavior','large/mixed inputs',
                    'corrupt BMP','allocation/worker failure cleanup','held-out fixtures','performance distributions'])
    write(e.path/'contract.json',data)
    data['evidence']=e.finish('OBSERVED',dict(status='FROZEN',checks=checks))
    write(PROFILE,data)
    record('IMG-00','冻结多实例 encoder 原始 CLI/下载/线程/状态/资源义务；明确旧 q0 拒绝用例与原始夹取语义不同。七组 CUDA 探测先只作观察，不签发整例。',[str(PROFILE.relative_to(ROOT)),data['evidence']])
    print(data['evidence'])

if __name__=='__main__':main()
