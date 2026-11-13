#!/usr/bin/env python3
"""Strengthen structural validation before any new candidate quality result."""
import json
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

def main():
    previous=ROOT/'migration/rewrite/image-encoder-math-variant-profile.json'
    dest=ROOT/'migration/rewrite/image-encoder-math-variant-v2-profile.json'
    if dest.exists():raise ValueError('strict contract already frozen')
    value=json.loads(previous.read_text());value.pop('evidence',None)
    value['mathematics']['MCU_padding']='Encode all interleaved MCU slots. Outside ceil(component_width/8) x ceil(component_height/8), all 64 quantized coefficients are zero. Independent entropy decode must check absolute DC after prediction and every AC for these dummy blocks.'
    value['mathematics']['oracle_precision_gate']='80-digit Decimal cosine/DCT versus float64 on nine adversarial 8x8 blocks: max absolute difference <= 1e-9.'
    value['required']+=['Complete strict SOI-to-EOI baseline entropy decode; no trailing bytes, missing EOI, invalid stuffing, extra entropy, malformed tables or non-one final pad bits. All MCU slots checked including dummy blocks.',
                        'Independent libjpeg full decode and coefficient read must produce no recovery warning. Missing EOI and truncated entropy must be rejected by validation.',
                        'AC error budget is 0.01 unquantized DCT units, not multiplied by quant. Exact ties-away claimed only for DC; AC is bounded approximation.']
    value['structural_amendment']=dict(previous=str(previous.relative_to(ROOT)),sha256=digest(previous),reason='MOAT review found tolerant libjpeg truncation and omitted MCU padding blocks. Add strict entropy and warning gates before new candidate AMD execution/quality results. Frozen pixels, numerical limits, weights and case IDs unchanged; native reference execution may use identical v1 inputs.')
    e=Experiment('I5','encoder-mathematical-strict-structure-contract','CPU-contract',sources=[__file__,previous])
    write(e.path/'profile.json',value);value['evidence']=e.finish('OBSERVED');write(dest,value)
    record('IMG-01','数学合同v2补充完整EOI/零警告/全部MCU填充块检查，数值门槛和新保留输入不变；修订在候选AMD质量结果之前冻结，v1保留。',[str(dest.relative_to(ROOT)),value['evidence']]);print(value['evidence'])

if __name__=='__main__':main()
