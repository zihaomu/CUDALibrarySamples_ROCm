#!/usr/bin/env python3
"""Refresh the current section without changing the chronological evidence log."""
import collections,datetime,fcntl,json,pathlib
from catalog import ROOT
DOC=ROOT.parent/'doc/cuda_samples_on_rocm_design.md'
cat=json.loads((ROOT/'migration/samples.yaml').read_text());counts=collections.Counter(s['status'] for s in cat['samples']);audit=json.loads((ROOT/'migration/build-audit.json').read_text());r=ROOT/'migration/reports'
text='''## 12. 当前实施快照（工具刷新）

本节替代设计阶段的未开始快照。逐步过程保留在第 11 节；整例成功、部分功能、路线失败分别报告，不将执行过计划解释为所有功能均已迁移成功。

'''
text+='更新时间：'+datetime.datetime.now(datetime.timezone.utc).isoformat()+'。\n\n'
text+=f'清单为 **{len(cat["samples"])} 个独立可执行/脚本源入口**（563 C/C++、76 Fortran/Python），逐例均有实际尝试记录。当前：'+ '；'.join(f'`{k}` {counts[k]}' for k in ['PASSED','PARTIAL','FAILED','BLOCKED','UNSUPPORTED','NOT_STARTED','IN_PROGRESS'])+'。\n\n'
text+=f'M0 静态审计覆盖全部 477 个构建定义和 866 个源文件，记录 {len(audit["declarations"])} 个声明、{sum(bool(s.get("build_bindings")) for s in cat["sources"])} 个源文件构建绑定；{len(audit["unresolved_declarations"])} 个 SDK/测试生成输入/条件变体表达式逐项归类，不重复膨胀入口数量。这不是全部 SDK 条件配置均已生成运行的声明。\n\n'
text+='''| 里程碑 | 实际结果与边界 |
| --- | --- |
| M0 | 完成入口清单、静态构建审计、30 库级表与逐例报告、ROCm/CUDA 锁、runner、fixture、证据结构。 |
| M1 | 16/16 个原始 profile + 共 95 个必需用例，ROCm/独立 CPU 参考/CUDA 共享输入对照通过。包含原始非 SPD info 行为和真实 GPU FFT scaling；LU 无 pivot 路径显式补身份 pivots。 |
| M2 | 全部 224 个基础数学 C/C++ 入口已尝试；BLAS 三方、稀疏 expected、全部 generator 分布检查逐项附报告。未通过的 API/signature、算法或执行结果保留 FAILED/PARTIAL。 |
| M3 | hipCOMP 源码构建、LZ4 GPU 往返通过；RPP U8 resize 能力探针通过；rocJPEG baseline 与 CPU libjpeg 最大像素差 2，后两者不代表整个原始样例通过。hipTensor 已建成，gfx1201 FP32 contraction 返回 ARCH_MISMATCH；保留 FP32 的 rocBLAS + HIP 排列替代通过原始 extents/模式，全部有限值和 32 CPU 抽样点及小尺寸全量检查。hipSPARSELt 的 gfx1201 kernel 缺失有实机与锁定源码架构 gate 证据，2 例限定为 UNSUPPORTED。 |
| M4 | 两卡 hipBLAS + RCCL GEMM 探针通过；3D C2C/real-pair 保留原始双 GPU descriptor，1D Xt 缺口由两卡 hipFFT + RCCL + HIP 合并实现。3 个多卡 FFT 同输入 CUDA 全量对照通过。原始 MPI/多节点与分布式高级 API 缺口逐例保留，单卡不冒充多卡。 |
| M5 | 所有 MathDx/特殊 SDK 入口已实际构建/前端尝试；SHA2/32-lane SHA3 各 14 输入与 hashlib 及同实现 CUDA 精确对照；cuPQC vendor SDK 基线缺失另记。cuDSS simple C++ 及 2 个 Fortran 原始入口改用 CPU 稀疏符号图分析 + rocSOLVER CSRRF GPU 数值分解/求解并通过残差，未转 dense，未覆盖高级 API。其余 Fortran/Python 只做前端/绑定尝试，原样复制不计为已实现代码。 |

报告入口在 `CUDALibrarySamples_ROCm/migration/reports/`；全部入口详情在 `migration/sample-reports/`。失败不等于整个 ROCm 或硬件不支持；只有确定版本能力缺失时才用 UNSUPPORTED。未替换的 NVIDIA API、未实现的 AMD 算法改写与缺失 SDK/输入分别给出证据和恢复条件。

AMD 使用 immutable ROCm 10.1.0 foundation 和项目 overlay。**HIP ordinal 2 → 物理 GPU0，ordinal 3 → 物理 GPU1**，按 PCI 地址校验，物理 GPU3 禁用；共享预约动态读取。早期误将 HIP ordinal0 当成物理 GPU0 的批次已在第 11 节说明，仅作历史调试记录，不用于最终验收。两机器时钟存在约两分钟偏差，使用 run ID 与 source/input hash 关联。

复现 M1：

```bash
cd /home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm
HIP_VISIBLE_DEVICES=2 tools/migration/run_rocm.sh
python3 tools/migration/compare.py
python3 tools/migration/render.py
```

新增 54 个双端专项对照通过（36 RNG、2 SHA、3 callback、3 双卡 FFT、2 HSH Lt、8 solver）；M1/BLAS 三方对照另记，不重复计入入口完成率。JIT callback 分别经离线 SPIR-V 与 HIPRTC 运行时 SPIR-V 路径，保留 device callback 融合，272240 个语义输出全部通过 CPU 和 CUDA 检查。

**性能结果为 BLOCKED**：已执行 6 个 FP32/FP64 GEMM profile，但 AMD 卡存在其它任务，实际空闲 gate 失败。不报告合格速度比；原始计时、三组统计、CPU 误差与恢复条件在 `migration/reports/performance-comparison.md/json`。

专项原始 profile、native probes、Fortran/Python、分布检查和性能复现命令分别保存在逐例详情及证据 `commands.json`。CPU 参考依赖在 `build/python-reference`，native 依赖在 `build/`，不修改共享 foundation。小型日志已归档，最终源码/fixture 身份在 `migration/source-tree.json`，CUDA 观测副本可从内容对象恢复。全部批次的终态结果不等于全部 API 已迁移；失败与未实现能力保留在本次交付中。

'''
batch=r/'batch2-validation.json'
if batch.exists():
 rows=json.loads(batch.read_text());good=[x for x in rows if x['status']=='PASSED'];text+='第二批：'+str(len(good))+'/17 样例、'+str(sum(len(x['cases']) for x in good))+' 个输入 case 通过独立 CPU，CUDA 对照 '+str(sum(x['cuda_comparison']=='PASSED' for x in rows))+'/17。覆盖稀疏 3、BLAS 8、tensor 4、solver 2；tensor 保留原始规模，全部语义输出检查，加小尺寸/非零系数/零系数。27 个共享大/小输入 buffer 可按 seed=20261109 重建并逐文件核对 SHA256。原生 rotmg 重复缩放 H 错误由项目 HIP GPU 修正；原生失败与精确失败源码另存。详细见 `migration/reports/batch2.md` 与 `rotmg-scale-fix.md`。CUDA 侧 cuTENSOR 2.8.1 仅安装在项目 build overlay，单独锁定 library/wheel hash。\n\n'
batch=r/'batch3-validation.json'
if batch.exists():
 rows=json.loads(batch.read_text());good=[x for x in rows if x['status']==x['cuda_comparison']=='PASSED'];text+='第三批：'+str(len(good))+'/8 样例、'+str(sum(len(x['cases']) for x in good))+' 个输入 case 三方通过。稀疏3项 → solver4项 → Graph Capture1项依次完成。CG/BiCGSTAB 保留原始700×700网格，独立CSR/CPU求解/真实残差/收敛检查；BiCG变体共享捕获RHS消除生成顺序造成的末位差异，36个输入buffer可重建或按固定fixture核对hash。solver按batch和实际meig检查，含秩亏、未排序配对及索引/值域/全量/空区间。原规模SpVV图含2000个GPU kernel节点，三次输入变化replay通过；24个数值/图语义反向检查全部拒绝。AMD稀疏用物理GPU0，之后该卡被预约，guard阻止启动，solver/graph改用HIP ordinal1→物理GPU2。报告：`migration/reports/batch3.md`。\n\n'
live=r/'batches4-8-progress.json'
if live.exists():
 summary=json.loads(live.read_text());text+='第四至第八批实时结果：'+'；'.join(x['batch']+' '+str(x['samples_passed'])+'/'+str(x['samples_required'])+' 样例、'+str(x['cases_passed'])+'/'+str(x['cases_required'])+' cases' for x in summary['batches'])+'。完整逐例路线、限制和日志入口见 `migration/reports/batches4-8.md`；B8三项CUDA原生新API缺失，兼容数学对照与原始API基线分开记录。\n\n'
with DOC.with_suffix('.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);body=DOC.read_text();start=body.index('## 12.');end=body.index('## 附录 A',start);body=body[:start]+text+body[end:];body=body.replace('HIP_VISIBLE_DEVICES=0 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh','HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh');DOC.write_text(body.rstrip()+'\n')
print('Current design snapshot refreshed')
