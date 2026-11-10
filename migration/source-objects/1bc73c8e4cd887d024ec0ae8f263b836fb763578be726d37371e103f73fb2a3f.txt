#!/usr/bin/env python3
"""Generate per-entrypoint, family and root status pages from observed evidence."""
import collections,json,os,pathlib,re,subprocess
from catalog import ROOT,CANDIDATES,BASE
from operator_support import write_reports,render_overview
from support_log_index import write_index
STATES=['PASSED','PARTIAL','FAILED','BLOCKED','UNSUPPORTED','NOT_STARTED','IN_PROGRESS']
def link(label,target,parent):return '['+str(label).replace('|','/')+']('+os.path.relpath(target,parent).replace(' ','%20')+')'
def safe(text):return str(text or '—').replace('|','/').replace('\n',' ')
def display_library(value):
 names={x.lower():x for x in ['hipBLAS','hipBLASLt','hipSPARSE','hipSPARSELt','hipSOLVER','hipFFT','hipRAND','hipTensor','hipCOMP','rocBLAS','rocSPARSE','rocSOLVER','rocFFT','rocRAND','rocJPEG']}
 return re.sub(r'\b(?:'+ '|'.join(names)+r')\b',lambda m:names[m[0].lower()],value,flags=re.I)
def detail_path(s):return ROOT/'migration/sample-reports'/(s['source']+'.md')
def render():
 cat=json.loads((ROOT/'migration/samples.yaml').read_text());decisions=json.loads((ROOT/'migration/ecosystem-decisions.json').read_text());operators=write_reports(cat);write_index(cat);groups=collections.defaultdict(list)
 for s in cat['samples']:groups[s['family']].append(s)
 counts=collections.Counter(s['status'] for s in cat['samples']);totals='；'.join(f'{k}: {counts[k]}' for k in STATES)
 for s in cat['samples']:
  q=detail_path(s);q.parent.mkdir(parents=True,exist_ok=True);lines=['# '+s['id'],'',f'**{s["status"]} / {s["level"]}**','',s['reason'],'', '| 字段 | 当前记录 |','| --- | --- |',f'| 原始入口 | {link(s["source"],ROOT/s["source"],q.parent)} |',f'| 实际库 / 后端 | {safe(s.get("actual_library"))} / {safe(s.get("backend_library"))} |',f'| 候选路线 | {safe(", ".join(s["candidate_libraries"]))} |',f'| 代码 | {link(s["implementation"],ROOT/s["implementation"],q.parent) if s.get("implementation") else "无实现"} |',f'| required cases | {len(s["passed_cases"])}/{len(s["required_cases"])} |',f'| CUDA baseline / comparison | {s["cuda_baseline"]} / {s["cuda_comparison"]} |',f'| 性能 | {s["benchmark"]} |',f'| 原始源码 SHA256 | `{s["source_sha256"]}` |','', '编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。','']
  if s['required_cases']:lines+=['必需用例：'+', '.join('`'+x+'`' for x in s['required_cases'])+'。','']
  lines+=['实现方式：`'+s.get('equivalence','未登记')+'`。','', '恢复/扩展条件：'+s.get('retry_condition','见当前失败原因')+'','']
  if s.get('cuda_comparison_reason'):lines+=['CUDA 对照限制：'+s['cuda_comparison_reason'],'']
  if s.get('cuda_vendor_comparison')=='BLOCKED':lines+=['CUDA SHA 检查使用同一自有实现；NVIDIA cuPQC vendor SDK 基线不可用，两者范围分别记录。','']
  if s.get('original_port'):
   a=s['original_port'];lines+=['## 原始 API 自动移植稿最近一次尝试','', '该记录与上表选定的手写/替代实现分别保留。','',safe(a.get('reason')),'', '尝试库：'+safe(', '.join(a.get('attempted_libraries',[])))+'；实现 hash：`'+a.get('implementation_sha256','')+'`。','']
  lines+=['## 复现与证据','', '从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。','']
  if s.get('reproduce'):lines+=[('在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。' if s.get('reason_code') in {'VALIDATED_BATCH2','VALIDATED_BATCH3','VALIDATED_B4_B8','VALIDATED_B9_B11','VALIDATED_B9_B11_SUBSET'} else '在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：'),'', '```bash',s['reproduce'],'```','']
  elif s.get('implementation','') and not s['implementation'].startswith('rocm/ported/') and s['implementation'].endswith('sample.cpp') and s['family']!='cuDSS':
   f=str(pathlib.Path(s['implementation']).parent.relative_to('rocm'));lines+=['```bash','HIP_VISIBLE_DEVICES=2 tools/migration/run_rocm.sh --filter '+f,'```','']
  else:lines+=['具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。','']
  lines += ['- '+link(e,ROOT/e,q.parent) for e in dict.fromkeys(s['evidence'])]
  q.write_text('\n'.join(line.rstrip() for line in lines).rstrip()+'\n')
  # Keep the established M1 implementation README entry points.
  if (s.get('implementation') or '').endswith('/sample.cpp') and not s['implementation'].startswith('rocm/ported/'):
   r=(ROOT/s['implementation']).parent/'README.md';r.write_text('# '+s['id']+' 的 ROCm 实现\n\n'+s['reason']+'\n\n'+link('逐例状态、命令与证据',q,r.parent)+'\n')
 for family in CANDIDATES:
  p=ROOT/family/'README.md';samples=groups[family];c=collections.Counter(s['status'] for s in samples);a='<!-- ROCM-MIGRATION:START -->';b='<!-- ROCM-MIGRATION:END -->'
  rows=[a,'## ROCm 迁移实时状态','',f'{len(samples)} 个独立源入口；'+ '，'.join(f'{state} {c[state]}' for state in STATES)+ '。','', '候选库：'+', '.join(CANDIDATES[family])+'。候选不等于已使用；基础探针成功也不等于整库迁移成功。','',decisions[family]['reason'],'','| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |','| --- | --- | --- | --- | --- | --- |']
  for s in samples:
   libs=(s.get('actual_library') or '未验证使用库')+(' / '+s['backend_library'] if s.get('actual_library') and s.get('backend_library') else '');ev='；'.join(link('记录',ROOT/e,p.parent) for e in s['evidence'][-2:]) or '—';label=str(pathlib.Path(s['source']).relative_to(family));rows.append('| '+link(label,ROOT/s['source'],p.parent)+' · '+link('详情',detail_path(s),p.parent)+' | '+safe(libs)+' | '+s['level']+' / '+s['status']+' | '+safe(s['reason'])+' | '+s['cuda_baseline']+' / '+s['cuda_comparison']+' | '+ev+' |')
  rows+=['','生成来源：'+link('migration/samples.yaml',ROOT/'migration/samples.yaml',p.parent)+'；执行 `python3 tools/migration/render.py` 更新。',b]
  content=p.read_text() if p.exists() else '# '+family+'\n'
  if a in content:content=content.split(a)[0]+content.split(b,1)[1].lstrip('\n')
  prefix=content.rstrip();original=subprocess.run(['git','show',BASE+':'+str(p.relative_to(ROOT))],cwd=ROOT,capture_output=True)
  if original.returncode==0 and original.stdout.decode().replace('\r\n','\n').rstrip()==prefix:prefix=original.stdout.decode().rstrip('\r\n')
  p.write_bytes((prefix+'\n\n'+'\n'.join(rows)+'\n').encode())
 p=ROOT/'README.md';content=p.read_text();upstream=content.split('## 上游 CUDA Library Samples 说明',1)[1];intro='''[![License](https://img.shields.io/badge/License-Apache_2.0-yellowgreen.svg)](https://opensource.org/licenses/Apache-2.0)

# CUDA Library Samples on ROCm

对照 NVIDIA CUDA Library Samples，逐例选择 AMD/ROCm 生态中适合的库并实现。每例公开实际使用库、实现程度、正确性结果、CUDA 对照及失败原因。保留 CUDA 原始源码作为参考；AMD 实验固定 ROCm 10.1.0 / Radeon AI PRO R9700（gfx1201），CUDA 对照使用双 RTX 5090 机器。

[B9–B11 实时进度](migration/reports/batches9-11.md) · [B4–B8 验收](migration/reports/batches4-8.md) · [后续批次计划与能力边界](migration/roadmap.md) · [支持方式与详细日志总表](migration/reports/support-log-index.md) · [模块支持矩阵](#模块支持矩阵) · [已验收算子](#已验收算子与验证范围) · [未通过的具体原因](#未通过和不支持的具体原因) · [设计与实施日志](migration/design.md) · [执行交付报告](migration/reports/plan-execution.md) · [逐例清单](migration/samples.yaml) · [环境锁](migration/environments/project.lock.json)

## 当前结果

'''
 intro+=f'上游固定为 `{BASE}`。静态审计覆盖 **866 个源文件、477 个构建定义、{len(cat["samples"])} 个独立可执行/脚本源入口**。链接辅助文件、外部 SDK binding、架构/静态链接/通信变体另存元数据，不重复计入入口分母；没有在所有专有 SDK 条件下展开并执行每个构建配置。\n\n'+totals+'。\n\n'
 intro+='`PASSED` 只表示该行明确登记的原始功能和必需用例通过，不能推及整库、其它精度/规模或性能。`PARTIAL` 包括已运行但尚无独立数值验收的端口；`FAILED` 保留真实失败日志和重试条件。不存在“HIPIFY 退出成功即迁移成功”的统计。\n\n'
 intro+='专项证据：[M1 双端数值对照](migration/reports/m1-comparison.json)、[BLAS 三方对照](migration/reports/blas-three-way.json)、[稀疏 expected 检查](migration/reports/sparse-original-validation.json)、[新增双端数值/分布对照](migration/reports/additional-comparison.json)、[AMD 生态探针](migration/reports/native-probes.json)、[选型与缺口](migration/reports/ecosystem-decisions.md)、[最终一致性检查](migration/reports/final-validation.json)。**M0–M5 已逐批执行并记录结果；按逐例登记范围的成功率为 '+f'{100*counts["PASSED"]/len(cat["samples"]):.2f}%'+ '，失败/部分完成仍在分母。**\n\n'
 intro+='性能仅选择 6 个 GEMM profile；AMD GPU 有其它任务，空闲资格检查失败，因此 [性能报告](migration/reports/performance-comparison.md) 标为 BLOCKED，仅保留原始计时，不发布合格速度比。\n\n'
 if (ROOT/'migration/reports/batch2-validation.json').exists():
  batch=json.loads((ROOT/'migration/reports/batch2-validation.json').read_text());qualified=[r for r in batch if r['status']=='PASSED'];intro+='**第二批已收口：'+str(len(qualified))+'/17 个样例、'+str(sum(len(r['cases']) for r in qualified))+' 个输入 case。** [详细验收报告](migration/reports/batch2.md) 包含稀疏 3 项、BLAS 8 项、tensor 4 项与 solver 2 项的 CPU/CUDA 对照、原始规模与边界检查。`rotmg` 的原生缩放错误及项目 GPU 修正[单独记录](migration/reports/rotmg-scale-fix.md)；大张量 fixture 支持按 seed 和 SHA256 完整重建。\n\n'
 if (ROOT/'migration/reports/batch3-validation.json').exists():
  batch=json.loads((ROOT/'migration/reports/batch3-validation.json').read_text());qualified=[r for r in batch if r['status']==r['cuda_comparison']=='PASSED'];intro+='**第三批已收口：'+str(len(qualified))+'/8 个样例、'+str(sum(len(r['cases']) for r in qualified))+' 个输入 case，ROCm/独立 CPU/CUDA 三方通过。** [第三批详细验收与复现](migration/reports/batch3.md) 覆盖 CG、BiCGSTAB、五对角批量求解、4 项 solver 与 SpVV Graph Capture/Replay；包含 meig/未排序配对检查、2000 个实际 GPU 图节点、输入变化重放，以及 24 项反向检查。\n\n'
 live=ROOT/'migration/reports/batches4-8-progress.json'
 if live.exists():
  progress=json.loads(live.read_text());intro+='**B4–B8：'+str(sum(x['samples_passed'] for x in progress['batches']))+'/26 个样例、'+str(sum(x['cases_passed'] for x in progress['batches']))+'/92 个预登记用例验收通过。** [逐例实际库、限制与详细日志](migration/reports/batches4-8.md)。3项CUDA新API在已安装SDK缺失，原生基线保持FAILED，兼容CUDA数学基线通过。\n\n| 批次 | 样例通过 | 用例通过 |\n| --- | ---: | ---: |\n'
  for row in progress['batches']:intro+='| '+row['batch']+' | '+str(row['samples_passed'])+'/'+str(row['samples_required'])+' | '+str(row['cases_passed'])+'/'+str(row['cases_required'])+' |\n'
  intro+='\n'
 live911=ROOT/'migration/reports/batches9-11-progress.json'
 if live911.exists():
  progress=json.loads(live911.read_text());intro+='**B9–B11实施结果：** '+'；'.join(x['batch']+' '+str(x['samples_passed'])+'/'+str(x['samples_required'])+' 整例通过、'+str(x['samples_partial'])+' 部分支持' for x in progress['batches'])+'。[逐例支持方式、缺口与日志](migration/reports/batches9-11.md)。CPU progressive fallback、完整NVBENCH框架与cuDSS配置/查询缺口保留PARTIAL。\n\n'
 intro+=render_overview(operators)
 intro+='## 模块支持矩阵\n\n下表覆盖全部 30 个库级模块。“已验收算子族”按上文口径去重；“通过/总入口”是原始 sample 数，二者分别统计。部分完成、失败、明确不支持、前置条件阻塞分别列出；每个模块链接包含全部原始样例的实际库、代码、逐例原因和证据。候选库不计为实际使用库。\n\n| 模块 | 实际/候选 AMD 路线 | 已验收算子族 | 通过/总入口 | 部分 | 失败 | 不支持 | 阻塞 | 当前范围及未通过原因 |\n| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |\n'
 for family in CANDIDATES:
  items=groups[family];c=collections.Counter(s['status'] for s in items);actual=sorted({display_library(s['actual_library']+(' → '+s['backend_library'] if s.get('backend_library') and s['backend_library'].lower() not in s['actual_library'].lower() else '')) for s in items if s.get('actual_library') and s['level'] in {'L2','L3','L4'}});route='; '.join(actual) if actual else '候选：'+', '.join(CANDIDATES[family]);intro+='| '+link(family,ROOT/family/'README.md',ROOT)+' | '+safe(route)+' | '+str(operators['modules'][family]['verified_operator_family_count'])+' | '+str(c['PASSED'])+'/'+str(len(items))+' | '+str(c['PARTIAL'])+' | '+str(c['FAILED'])+' | '+str(c['UNSUPPORTED'])+' | '+str(c['BLOCKED'])+' | '+safe(decisions[family]['reason'])+' |\n'
 reasons=collections.Counter((s['status'],s['reason_code']) for s in cat['samples'] if s['status']!='PASSED')
 intro+='''
## 未通过和不支持的具体原因

“本项目尚未实现/验收”与“锁定版本和硬件确实不支持”分别记录。当前只有 hipSPARSELt 的 2 个样例满足后者的证据条件；其它失败需按 API、构建、数值或执行错误继续定位，不能泛化为 ROCm 不支持。

| 当前结论 | 入口数 | 具体原因 | 证据与恢复条件 |
| --- | ---: | --- | --- |
'''
 for status,code,reason,evidence in [
  ('FAILED','BUILD_ERROR','自动移植稿未完成 API/枚举/类型/链接适配。例如 Lt grouped/scale/layout、FP4 观察代码、MathDx device DSL 和特殊 SDK 仍有编译缺口；不据此宣称硬件不支持。','各模块 README 列出首个有效编译错误；需完成保持原语义的 AMD 改写再验收。'),
  ('FAILED','BINDING_OR_FRONTEND_MIGRATION_REQUIRED','Fortran/Python 的 NVIDIA module、CUDA Fortran device 语法或 Python vendor 绑定尚未改写；前端/import 尝试失败。','[语言资格记录](migration/reports/languages.json)；需补 AMD C ABI/ISO_C_BINDING 或真实 GPU Python 绑定。'),
  ('FAILED','RUNTIME_ERROR','已编译但执行失败：包括原始 Xgetrf 路径、BSR SDDMM、SELL SpSV，以及 tensor cache/einsum/padding 场景；具体参数/架构/实现原因见逐例日志。','[原始 profile 尝试](migration/reports/original-rocm-latest.json)；修复失败调用，重新做独立数值检查。'),
  ('FAILED','TIMEOUT','cuTENSOR trinary contraction 在记录的时限内未结束，未获得合格结果。','[逐例报告](migration/sample-reports/cuTENSOR/contraction_trinary.cu.md)；定位执行/规模问题后重跑。'),
  ('PARTIAL','INDEPENDENT_VALIDATION_PENDING','剩余为 Xgeev 三例与 gesvdaStridedBatched：需排除 CPU 兼容执行，或确认近似算法和 residual norm 语义，并补齐对应独立验收。第三批稀疏与图捕获已通过。','逐例 required cases 保留缺项；补 CPU/数学参考和边界检查，返回 0 不能代替验收。'),
  ('PARTIAL','SEMANTIC_GAP','LZ4 和 JPEG 仅完成上述子集，尚未保留完整原样例的 API、输入和执行流程。','[能力探针](migration/reports/native-probes.json)、[JPEG 像素对照](migration/reports/rocjpeg-cpu.json)；补完整原始功能。'),
  ('UNSUPPORTED','HW_UNSUPPORTED','锁定 ROCm 10.1.0 hipSPARSELt/gfx1201 缺 Tensile kernel bundle；实际运行报错且固定源码的架构 gate 拒绝该目标。','[实测与源码证据](cuSPARSELt/README.md)；需匹配 kernel bundle、新实现或受支持 GPU，不能以 dense GEMM 替代。'),
  ('BLOCKED','ENV_MISSING_DEP','nvJPEG Python 测试的 imports 已通过，但 AMD decoder 可执行文件/完整 CLI 测试前置条件尚未实现。','[逐例报告](migration/sample-reports/nvJPEG/nvJPEG-Decoder/tests/test_decoder.py.md)；补 GPU 可执行文件后执行原始测试。')]:
  intro+=f'| {status} / `{code}` | {reasons[(status,code)]} | {reason} | {evidence} |\n'
 intro+='\n已验收模块内部也保留具体限制：hipTensor FP32 原生 contraction 的架构 gate 失败由 rocBLAS + HIP 保持精度的路线补足；hipFFT 单 batch 1D Xt 缺口由两卡分解/通信/合并补足。cuFFTMp/cuBLASMp/cuSOLVERMp/cuTENSORMg/Mp 的原始分布式算法，以及 MathDx 的设备内融合仍未完成；JPEG2000/TIFF 未找到并实现完整 AMD GPU codec 路线。上述原因在模块矩阵中逐项展示。\n\n'
 intro+='''
## 构建与复现

先核对物理 GPU 占用及共享预约；**HIP ordinal 2 对应物理 GPU0**，ordinal 3 对应物理 GPU1。项目 `device_guard.py` 按 PCI 地址校验；物理 GPU3 排除计算，预约卡也会拒绝。历史使用错误 ordinal 的结果已标记，不能用于验收。

```bash
HIP_VISIBLE_DEVICES=2 tools/migration/run_rocm.sh
python3 tools/migration/compare.py
python3 tools/migration/render.py
```

M1 的独立 CMake/CTest（在锁定 ROCm 10.1.0 容器中，并先运行 guard）：

```bash
python tools/migration/device_guard.py
cmake -S rocm -B build/rocm -DCMAKE_BUILD_TYPE=Release
cmake --build build/rocm -j2
ctest --test-dir build/rocm --output-on-failure
```

原始 profile 批量构建：`bulk_run.py --families cuBLAS cuSPARSE ...`；先在锁定容器中运行 `bootstrap_sdk.py` 建项目 overlay。hipCOMP/hipTensor 的锁定源码重建使用 `bash tools/migration/build_optional.sh`。`python3 tools/migration/restore_observations.py` 从归档恢复 CUDA 输出观测/fixture 适配副本，原始 CUDA 树保持不变。每例复现链接在库级表中的“详情”；命令、原始日志、source/fixture hash 和环境随证据保存。[最终源码与 fixture 身份](migration/source-tree.json) 包含可恢复的内容寻址源码；大输出保留于 artifacts，输入生成方法/hash 在报告中。

## 状态解释

`NOT_STARTED` 未开始；`IN_PROGRESS` 实施中；`PARTIAL` 部分功能或仅运行通过；`PASSED` 登记的必需正确性用例全部通过；`FAILED` 实际尝试失败；`BLOCKED` 前置条件缺失；`UNSUPPORTED` 有指定版本/硬件的必要能力缺失证据。L0 无实现、L1 有源码、L2 编译通过、L3 AMD 执行通过、L4 必需正确性用例通过。性能单独登记。

## 上游 CUDA Library Samples 说明'''
 p.write_text(intro+upstream);print(totals)
if __name__=='__main__':render()
