#!/usr/bin/env python3
"""Freeze acceptance gates before connecting optimized Huffman to the original CLI."""
import json
from experiment import ROOT, Experiment, digest, write
from image_progress import record

PROFILE = ROOT / 'migration/rewrite/image-jpeg-encoder-instances-opt-profile.json'

def main():
    if PROFILE.exists():
        raise ValueError('optimized multi-instance contract already frozen')
    old = json.loads((ROOT/'migration/rewrite/image-jpeg-encoder-instances-full-gpu-profile.json').read_text())
    pilot = json.loads((ROOT/'migration/reports/image-jpeg-opt-huffman-runs.json').read_text())
    if old['status'] != 'FROZEN' or len(old['prior_products']) != 16 or len(pilot) != 5 or any(x['status'] != 'PASSED' for x in pilot):
        raise ValueError('prior products or isolated GPU pilot missing')
    inputs = old['inputs']
    if any(digest(ROOT/x['path']) != x['sha256'] for x in inputs):
        raise ValueError('frozen BMP input drift')
    e = Experiment('I5', 'optimized-Huffman-original-multi-instance-integration-contract',
                   'CPU-contract', sources=[__file__, *[ROOT/x['path'] for x in inputs]])
    contract = dict(status='FROZEN', phase='I5', inputs=inputs,
                    previous_products=old['prior_products'],
                    gates=dict(seven_original_CLI_groups=True,
                               all_sixteen_independently_decodable=True,
                               geometry_sampling_quantization_exact=True,
                               baseline_thirteen_old_RGB_exact=True,
                               optimized_three_RGB_exact_vs_same_GPU_FDCT_plain=True,
                               optimized_DHT_differs_from_plain=True,
                               optimized_branch_cpu_entropy_false=True,
                               optimized_branch_GPU_histogram_and_encode_trace=True,
                               changed_input_replay=True),
                    limits='No whole-entry PASSED until pinned memory, async overlap, original scheduler, parallel prefix and native CUDA baseline are checked.')
    write(e.path/'contract.json',contract)
    contract['evidence'] = e.finish('OBSERVED',dict(status='FROZEN',checks=[dict(
        check='16-prior-products-three-frozen-BMP-and-isolated-GPU-pilot',passed=True)]))
    write(PROFILE,contract)
    record('I5','原始多实例 -f GPU 优化 Huffman 接入验收合同已冻结：16 产品独立解码、13 baseline 旧 RGB 精确、3 优化产品与同源 GPU FDCT plain RGB 精确；GPU 直方图/熵编码 trace 必须通过。',[contract['evidence'],str(PROFILE.relative_to(ROOT))])
    print(contract['evidence'])

if __name__ == '__main__':
    main()
