#!/usr/bin/env python3
"""Inventory current image source/proof dependencies and explicit completion gaps."""
import json,re
from collections import Counter,defaultdict
from pathlib import Path
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

REPORT=ROOT/'migration/reports/image-completion-inventory.json'

def closure(path):
    seen={};missing=[];todo=[path]
    while todo:
        file=todo.pop()
        if file in seen:continue
        seen[file]=digest(file)
        for name in re.findall(r'^\s*#\s*include\s*"([^"]+)"',file.read_text(errors='replace'),re.M):
            candidates=[file.parent/name,ROOT/'rocm/common'/name,ROOT/'rocm'/name]
            found=next((p.resolve() for p in candidates if p.is_file()),None)
            if found is not None and found.is_relative_to(ROOT):todo.append(found)
            else:missing.append(dict(including=str(file.relative_to(ROOT)),include=name))
    return {str(p.relative_to(ROOT)):sha for p,sha in sorted(seen.items())},missing

def gaps(s):
    src=s['source']
    if s['status']=='PASSED' and s.get('active_batch') in ('IMG-01','IMG-02'):
        return ['IMG-10'],['当前完整资格已发布；最终26入口集中回归及依赖整理后按实际源码重验','保持资格中声明的算法/平台差异与历史失败记录']
    if 'Encoder-MultipleInstances' in src:
        if s.get('reason_code')=='VALIDATED_I5_ASYNC_GPU_JPEG_INSTANCES_SUBSET':
            return ['IMG-01'],['完整保留集的native/独立CPU像素等价门槛','j0/大尺寸混合输入/IO与线程异常组合','64位transform索引、单图预分配与性能计时合同','当前提交冷检出和最终复审；并行prefix/异步slot/15 CLI/33产品已验']
        return ['IMG-01'],['生产并行 prefix/溢出检查','pinned buffer、可复用 workspace、双缓冲与事件重叠','下载开关、质量夹取、原始自动线程标定','原生 CUDA 和保留输入复合验收']
    if 'watershedSegmentation' in src:
        return ['IMG-02'],['当前分区/边界与 native 大幅差异尚未解释','平台区、相同高度、4/8 邻域和区域拓扑','完整原图产品及局部边界验收']
    if s['family']=='nvJPEG2000':
        phases=['IMG-07','IMG-08','IMG-09'] if 'Encoder' in src else ['IMG-06','IMG-08','IMG-09']
        return phases,['GPU Tier1/MQ/HT 与完整码块系数链未完成','Part1/HT/NLT3、位深符号/浮点等源码必需模式','真实完整原图、tile/ROI/流水线和错误合同','既有 SDK/构建失败是历史证据，不能代替当前算法缺口']
    if s['family']=='nvJPEG':
        if 'Image-Resize' in src:
            return ['IMG-03','IMG-04','IMG-05'],['progressive 解码仍有 CPU 熵/系数阶段','progressive 编码、源量化表和 APP/COM 继承','resize/watermark 全参数组合和全产品验证']
        return ['IMG-03','IMG-04'],['progressive 解码仍有 CPU 熵/系数阶段','完整 backend/ROI/输出格式/自动标定/批处理合同','原始入口与 Python 调用、真实多 slot 调度复验']
    if src=='NPP/distanceTransform/distanceTransform.cpp':
        return ['IMG-10'],['旧资格覆盖数学用例；原始六个 RAW 文件完整入口仍需实现/验收','六原图输出集合、Voronoi/dtype/所有原模式']
    return ['IMG-10'],['保留现有资格；按原始源码复核完整 CLI/条件分支/文件流程','共享核心变更后重跑受影响用例；最终冷构建复验']

def main():
    catalog=ROOT/'migration/samples.yaml';old=ROOT/'migration/rewrite/image-contracts.json'
    samples=[s for s in json.loads(catalog.read_text())['samples'] if s['family'] in ('NPP','NPP+','nvJPEG','nvJPEG2000')]
    oldrows={x['sample_id']:x for x in json.loads(old.read_text())['samples']}
    if len(samples)!=26 or set(x['id'] for x in samples)!=set(oldrows):raise ValueError('26 stable IDs required')
    rows=[];users=defaultdict(list);deps={};checks=[]
    for s in samples:
        prior=oldrows[s['id']];source=ROOT/s['source'];impl=ROOT/s['implementation'];proof=s.get('selected_validation',{})
        original={name:dict(sha256=digest(ROOT/name),bytes=(ROOT/name).stat().st_size) for name in prior['source_files']}
        intact=all(original[name]['sha256']==value['sha256'] for name,value in prior['source_files'].items())
        checks.append(dict(check='unchanged-original-'+s['id'],passed=intact and digest(source)==s['source_sha256']))
        includes,missing=closure(impl)
        for name,sha in includes.items():users[name].append(s['id']);deps[name]=sha
        proofdeps=proof.get('dependencies',{})
        drift=[name for name,sha in proofdeps.items() if not (ROOT/name).is_file() or digest(ROOT/name)!=sha]
        stage,remaining=gaps(s)
        rows.append(dict(sample_id=s['id'],family=s['family'],catalog_status=s['status'],source=s['source'],
            source_files=original,implementation=s['implementation'],local_include_closure=includes,
            unresolved_quoted_includes=missing,selected_proof_kind=proof.get('kind',proof.get('batch')),
            selected_proof_evidence=proof.get('evidence'),selected_proof_dependencies=proofdeps,
            selected_proof_dependency_drift=drift,required_cases=s.get('required_cases',[]),passed_cases=s.get('passed_cases',[]),
            completion_stages=stage,remaining=remaining,
            original_CLI_token_hints=prior.get('CLI_token_hints',[]),original_conditionals=prior.get('conditional_compilation',[]),
            original_literal_image_paths=prior.get('literal_image_paths',[]),
            semantic_matrix_status='VALIDATED' if s['status']=='PASSED' and s.get('active_batch') in ('IMG-01','IMG-02') else 'IN_PROGRESS' if 'Encoder-MultipleInstances' in s['source'] else 'NOT_YET_REAUDITED',
            semantic_contract='migration/rewrite/image-completion-encoder-contract.json' if 'Encoder-MultipleInstances' in s['source'] else 'migration/rewrite/image-watershed-completion-contract.json' if 'watershedSegmentation' in s['source'] else None))
    e=Experiment('I0','image-completion-26-source-dependency-gap-ledger','CPU-contract',sources=[__file__,catalog,old,*[ROOT/n for n in deps]])
    data=dict(status='IN_PROGRESS',scope='Static dependency/gap audit, not full CLI qualification. Token hints may include false positives; Python dynamic imports and build-time defines require semantic review.',
        sample_count=26,counts=dict(Counter(s['status'] for s in samples)),samples=rows,
        reverse_local_include_users=dict(sorted(users.items())),checks=checks,
        remaining_IMG00=['26-source full default/CLI/error/conditional semantic matrix','held-out fixtures and numeric thresholds',
                         'actual SDK loader identities for all families','dependency review for dynamic/Python/external sources'])
    write(e.path/'inventory.json',data)
    data['evidence']=e.finish('OBSERVED' if all(c['passed'] for c in checks) else 'CONTRACT_AUDIT_FAILED',dict(status='OBSERVED',checks=checks))
    write(REPORT,data)
    lines=['# 图像完整实现：逐入口缺口与依赖账本','','本表记录当前主表和剩余工程义务。13 项旧整例资格保留；新计划完整源码语义复核尚未结束，不能将静态 token 清单视为完整 CLI 合同。',
           '',f"统计：{data['counts']}。机器可读的源码 SHA、include 反向依赖、证明和漂移结果见 [inventory JSON](image-completion-inventory.json)。",'',
           '| 原始入口 | 主表状态 | 后续阶段 | 明确欠项 |','| --- | --- | --- | --- |']
    for row in rows:
        lines.append('| `'+row['sample_id']+'` | '+row['catalog_status']+' | '+', '.join(row['completion_stages'])+' | '+'；'.join(row['remaining'])+' |')
    lines+=['','## 已冻结合同','',
        '[多实例 JPEG encoder](../rewrite/image-completion-encoder-contract.json)：原始质量夹取、下载开关、自动标定/状态/双缓冲等义务，七组初始 CUDA 探测。旧 q0 拒绝用例保留历史，但不作为原始语义兼容证明。','',
        '## 仍待完成的 IMG-00 工作','',*['- '+x for x in data['remaining_IMG00']],'',
        '本次证据：`'+data['evidence']+'`。当前资格以 `samples.yaml` 为准；组件实验不会自动升级样例。','']
    (ROOT/'migration/reports/image-completion-IMG-00.md').write_text('\n'.join(lines))
    record('IMG-00','更新26入口当前资格、源码SHA、本地include反向依赖与算法欠项账本；当前'+str(data['counts'])+'。全部入口语义矩阵和保留验收集仍未完成，阶段保持IN_PROGRESS。',[str(REPORT.relative_to(ROOT)),'migration/reports/image-completion-IMG-00.md',data['evidence']])
    print(data['counts'],data['evidence'])

if __name__=='__main__':main()
