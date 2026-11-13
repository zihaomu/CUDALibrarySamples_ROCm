#!/usr/bin/env python3
"""Integrate validated arithmetic; all affected production proofs need refresh."""
import json
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_encoder_math_binding import BUILD,current,sealed

def main():
    b=json.loads(BUILD.read_text());current(b)
    proof=ROOT/'migration/reports/image-encoder-math-binding.json';accepted=json.loads(proof.read_text());sealed(accepted)
    if accepted['status']!='PASSED' or len(accepted['cases'])!=80:raise ValueError('fresh independent mathematical matrix required')
    candidate=ROOT/'build/image-encoder-math-candidate/common/image/jpeg_wide_transform.hpp'
    wide=ROOT/'rocm/common/image/jpeg_wide_transform.hpp';legacy=ROOT/'rocm/common/image/jpeg_encoder_gpu.hpp'
    text=candidate.read_text();old=legacy.read_text()
    first=text.index('__global__ void rgb_to_plane(');end=text.index('\n__global__ void forward_dct_quantize',first)
    color=text[first:end]
    color=color.replace('    const auto position=pixel_index(index,pw,ph);\n    if(!position.valid)return;\n    const int x=int(position.x),y=int(position.y),scale=channel==0?1:sampling;',
                        '    if(index>=size_t(pw)*ph)return;\n    const int x=int(index%pw),y=int(index/pw),scale=channel==0?1:sampling;')
    first=old.index('__global__ void rgb_to_plane(');end=old.index('\n__global__ void forward_dct_quantize',first)
    updated=old[:first]+color+old[end:]
    normalizer='''  float normalizer = (u ? 1.0f : 0.7071067811865475f) *
                     (v ? 1.0f : 0.7071067811865475f) * 0.25f;
  coefficients[index] = static_cast<short>(__float2int_rn(sum * normalizer / quant[frequency]));'''
    replacement='''  const float normalizer = (!u && !v) ? 0.125f :
      (u ? 1.0f : 0.7071067811865475f) * (v ? 1.0f : 0.7071067811865475f) * 0.25f;
  const float scaled = sum * normalizer / quant[frequency];
  const int whole = __float2int_rz(scaled);
  const float fraction = scaled - float(whole);
  coefficients[index] = static_cast<short>(whole + (fraction >= 0.5f ? 1 : (fraction <= -0.5f ? -1 : 0)));'''
    if updated.count(normalizer)!=1 or wide.read_text()==text:raise ValueError('unexpected/already-integrated production arithmetic')
    updated=updated.replace(normalizer,replacement)
    e=Experiment('I5','encoder-mathematical-arithmetic-integration','source-integration',sources=[__file__,BUILD,proof,candidate,wide,legacy])
    before={str(p.relative_to(ROOT)):digest(p) for p in [wide,legacy]}
    wide.write_text(text);legacy.write_text(updated)
    for p in [wide,legacy]:(e.path/('after-'+p.name)).write_text(p.read_text())
    row=dict(status='IMPLEMENTED_NOT_REQUALIFIED',before=before,after={str(p.relative_to(ROOT)):digest(p) for p in [wide,legacy]},evidence_references=[accepted['evidence'],b['evidence']],
        remaining='Refresh production build and 48-case subset, shared serial/resize closures, historical mathematical matrices, performance/memory, cold rebuild and full entry qualification. No sample support promotion.')
    write(e.path/'result.json',row);row['evidence']=e.finish('EXECUTED');write(ROOT/'migration/reports/image-encoder-math-integration.json',row)
    record('IMG-01','有理数颜色/精确DC已接入工作区宽索引及串行共享核心；新80项独立数学资格已通过，但旧生产/resize证明待刷新，当前不升级样例或声称完整入口通过。',[row['evidence']]);print(row['status'])

if __name__=='__main__':main()
