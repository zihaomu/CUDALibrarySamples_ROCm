#!/usr/bin/env python3
"""Publish two Git-anchored I5 resize subsets without full-sample promotion."""
import json
from experiment import ROOT, digest, write
from image_progress import record
from selected_proofs import anchored_seal, publication

CATALOG = ROOT / 'migration/samples.yaml'
REPORT = ROOT / 'migration/reports/image-jpeg-encoder-subset-qualifications.json'


def main():
    catalog = json.loads(CATALOG.read_text())
    qualifiers = json.loads(REPORT.read_text())
    integration = {x['source']: x for x in json.loads(
        (ROOT / 'migration/reports/image-jpeg-encoder-integration.json').read_text())}
    if len(qualifiers) != 2:
        raise ValueError('both original resize entries required')
    for q in qualifiers:
        proof = ROOT / q['evidence']
        sealed = json.loads((proof / 'qualification.json').read_text())
        sample = next(s for s in catalog['samples'] if s['id'] == q['sample_id'])
        if (not anchored_seal(proof, publication(proof), qualification=True) or
            q['status'] != 'PASSED' or q['contract_status'] != 'PARTIAL' or
            q['case_count'] != 9 or len(q['case_ids']) != 9 or
            any(not c['passed'] for c in q['checks']) or
            q['implementation'] != sample['implementation'] or
            q['implementation_sha256'] != digest(ROOT / q['implementation']) or
            any(digest(ROOT / name) != sha for name, sha in q['dependencies'].items()) or
            {k: v for k, v in q.items() if k not in {'qualification_id', 'evidence'}} != sealed or
            any(not anchored_seal(ROOT / ref, publication(ROOT / ref))
                for ref in q['evidence_references'])):
            raise ValueError('incomplete or unanchored I5 subset: ' + q['sample_id'])
        source = sample['source']
        products = sum(x['encoded_products'] for x in integration[source]['cases'])
        missing = ['I5/GPU-Huffman-entropy-and-bitstream-packing',
                   'I5/original-encoding-mode-tables-and-APP-COM-metadata',
                   'I4-I5/fixed-commit-cold-replay-and-independent-review']
        route = ('rocJPEG baseline hardware + project HIP progressive IDCT/chroma/RGB '
                 '+ project HIP JPEG color/downsample/FDCT/quant; '
                 'libjpeg-turbo CPU progressive entropy and JPEG encode entropy/headers')
        sample.update(status='PARTIAL', level='L4',
            reason_code='VALIDATED_I5_GPU_JPEG_FORWARD_SUBSET',
            actual_library=route,
            backend_library='rocJPEG + project HIP image decoder/forward encoder + libjpeg-turbo entropy',
            equivalence='HYBRID_CPU_GPU', selected_validation=q,
            required_cases=q['case_ids'] + missing, passed_cases=q['case_ids'],
            reason=f'七组原登记 CLI/数值流程及同输入 CUDA 数学对照通过；{products} 件重编码 JPEG '
                   '使用 AMD GPU 色彩转换、色度降采样、FDCT 与量化，CPU libjpeg-turbo 完成熵编码/头部；'
                   '四组预登记输入独立跨解码及物理 GPU trace 通过。完整 GPU Huffman、原编码模式/表/元数据复制和冷检出尚缺，故只算 PARTIAL。',
            cuda_comparison='PASSED',
            cuda_comparison_mode='HYBRID_GPU_FORWARD_TRANSFORM_CPU_ENTROPY',
            cuda_comparison_reason='既有七组同输入 CUDA 数学对照通过；I5 GPU FDCT 对独立 CPU JPEG 解码和固定门槛验收，不声称与 NVIDIA 私有编码 backend 字节一致。',
            active_batch='I5',
            retry_condition='完成 GPU 熵编码/Huffman、原编码模式/表/APP-COM 继承和冷检出后重做全入口资格；跨编码器不要求合法码流字节完全一致。',
            next_step='I5 GPU entropy/metadata/多实例编码；I6–I8 JPEG2000；I9 全局验收。',
            reproduce='HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh '
                      'env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 '
                      'python3 tools/moat/image_encoder_integration.py\n'
                      'python3 tools/moat/qualify_image_encoder_subset.py')
        if not any(x.get('qualification_id') == q['qualification_id'] for x in sample['attempts']):
            sample['attempts'].append(q)
        for ref in [q['evidence'], q['rocm_evidence'],
                    'migration/reports/image-jpeg-encoder.md',
                    'migration/reports/image-jpeg-encoder-integration.json',
                    'migration/reports/image-jpeg-encoder-runs.json',
                    'migration/reports/image-jpeg-encoder-trace.json',
                    'migration/reports/image-jpeg-encoder-negative.json']:
            if ref not in sample['evidence']:
                sample['evidence'].append(ref)
        record('I5', source+' 新 GPU 前向 JPEG 编码子集已绑定逐例主表；'
               f'{products} 件产品、七组原入口/CPU/CUDA 通过，整例仍 PARTIAL。',
               [q['evidence'], q['rocm_evidence']])
    write(CATALOG, catalog)
    write(ROOT / 'migration/reports/image-jpeg-encoder-publication.json',
          dict(status='PUBLISHED_PARTIAL', sample_count=2,
               sample_ids=[x['sample_id'] for x in qualifiers],
               evidence=str(REPORT.relative_to(ROOT)),
               scope='GPU forward color/FDCT/quant only; CPU entropy and sample gaps remain'))
    print('Published two I5 PARTIAL resize adapters')


if __name__ == '__main__':
    main()
