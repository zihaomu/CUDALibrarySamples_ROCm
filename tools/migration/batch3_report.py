#!/usr/bin/env python3
"""Render the completed third batch with explicit numerical and execution scope."""
import collections,json
from catalog import ROOT
from batch3_spec import ALL
from run import evidence_directory
from validate_blas import observed

rows=json.loads((ROOT/'migration/reports/batch3-validation.json').read_text())
cat=json.loads((ROOT/'migration/samples.yaml').read_text());counts=collections.Counter(s['status'] for s in cat['samples'])
scope={
 'cg':'原始 490000 行/2447200 nnz，加 23×23 变输入、31×31 非零初值；CSR、CPU CG、制造解、Ax−b、收敛阈值、迭代上限。',
 'bicgstab':'同等规模及变体；独立无预条件 CPU BiCGSTAB；保留 GPU ILU0/SpSV 算法，检查真实残差。',
 'gpsvInterleavedBatch':'2 个 4×4 五对角系统；原始、变化 RHS、对角占优；六个 interleaved 输入与输出布局、逐 batch CPU 求解/残差。',
 'gesvdjBatched':'2 个 3×2 矩阵；原始、扰动、秩亏；逐 batch 奇异值、SVD 重构、完整 U/V 正交性和 info。',
 'syevjBatched':'2 个 3×3 矩阵；原始未排序、排序开启、扰动；特征值 multiset、W/V 原配对残差、正交性和 info。',
 'syevdx':'3×3；索引 1..2、值域 (2.5,4.5]、全量、空区间 (10,11]；meig、返回谱、残差、正交性。',
 'sygvdx':'3×3、itype=1；索引 1..2、值域 (0.2,0.7]、全量、空区间；meig、Ax=λBx、B 正交性。',
 'graph_capture':'原始 65536 元素/1000 次 SpVV 捕获，加稀疏小向量与符号抵消；真实 kernel 节点、三次输入变化 replay、CPU dot。',
}
text='# 第三批：稀疏 3 → solver 4 → Graph Capture 1\n\n'
qualified=[r for r in rows if r['status']==r['cuda_comparison']=='PASSED']
text+=f'**{len(qualified)}/8 个样例、{sum(len(r["cases"]) for r in qualified)}/26 个预登记输入 case 通过 ROCm／独立 CPU／CUDA 三方验收。** 总通过样例 158 → {counts["PASSED"]}，PARTIAL 14 → {counts["PARTIAL"]}；按模块去重的算子/功能族 87 → 91，仍为 9 个已验收模块。其余 464 FAILED、2 UNSUPPORTED、1 BLOCKED 保留。batch/选择区间不会重复增加数学算子数，图捕获按功能族统计。\n\n'
text+='| 样例 | 实际 AMD 库 / 后端 | 输入 case | 数值与运行语义 | 三方结果 |\n| --- | --- | ---: | --- | --- |\n'
for r in rows:
 s=next(s for s in cat['samples'] if s['source']==r['source']);kind=r['source'].split('/')[1]
 text+=f'| [{kind}](../sample-reports/{r["source"]}.md) | {s["actual_library"]} / {s["backend_library"]} | {len(r["cases"])} | {scope[kind]} | {r["status"]} / CUDA {r["cuda_comparison"]} |\n'
text+='''
## 实现中的关键修正

CG、BiCGSTAB、gpsv 的 CUDA 构建补链 cuBLAS，AMD 对应链接 hipSPARSE + hipBLAS。原始 CSR 生成、IC0/ILU0 预条件、SpMV/SpSV 与 BLAS 迭代计算保留在 GPU；CPU 参考使用 SciPy 独立无预条件求解器。检查真正的 `||b−Ax||₂`，同时核对原例相对于初始残差的停止阈值和迭代预算。

BiCGSTAB 两个变体最初独立生成 RHS 时，两端 SpMV 累加顺序产生末位差异；初次 CPU 数值检查均通过，但 bitwise 输入 hash 不同，因此当时没有提升为 PASSED。[初次对照证据](batch3-initial-comparison.json) 单独保留。最终将 AMD 实际生成的 RHS 固定成共享 fixture，CUDA 读取相同字节；仍另行检查两端 GPU 原生生成的 RHS 与独立 CSR 乘法一致。36 个 CSR/向量输入 buffer 可按确定性生成规则或固定 RHS fixture 恢复并逐文件核对 SHA256。

`syevjBatched` 原例关闭排序，验证器比较特征值集合，并用原始列配对检查 `AV=VΛ`；没有单独重排 W 破坏对应关系。SVD 同时检查完整 U/V 的正交性与重构，秩亏输入也通过。

`syevdx`、`sygvdx` 只读取并输出实际 `meig` 个特征值和相应列；修正原例读取未返回结果、用全谱比较子集的显示逻辑。索引区间为 1-based 闭区间，数值区间为 `(vl,vu]`；空区间必须返回 0 个结果。原始矩阵与求解 API 保留。

Graph 原例只计时且未初始化 X/Y，不能凭运行成功验收。新端口保留原始向量规模和 1000 次 SpVV 捕获，初始化确定性输入，并将 scalar pointer mode 改为 device；标量回传在实际 graph launch 后、同一 stream 上执行。对照 CUDA 使用相同输入及执行方式。捕获后检查真实图节点类型，再复用同一个 executable 连续三次重放：原输入、修改 Y、Y 清零。图中没有用于计算 dot 的 host callback。本批结果不用于性能速度比。

## 实际图证据

| 输入 case | AMD 节点 / GPU kernel 节点 | 捕获 SpVV 调用 | 三次实际 replay 输出 |
| --- | ---: | ---: | --- |
'''
graph=next(r for r in rows if '/graph_capture/' in r['source'])
for c in graph['runs']:
 o=observed(evidence_directory(c['evidence'])/'run.log')
 text+=f'| {c["case"]} | {int(o["graph_nodes"][0])} / {int(o["graph_kernels"][0])} | {int(o["capture_calls"][0])} | '+', '.join(str(o['replay_'+str(i)][0]) for i in range(3))+' |\n'
text+='''
三种 case 各执行三次 replay（共 9 次），每次输出均与 CPU dot 及 CUDA 检查一致；修改输入后输出确实变化。[完整数值和语义结果](batch3-validation.json) 包含逐项误差与阈值。

## 环境、反向检查与边界

AMD 使用锁定的 ROCm 10.1.0 foundation、gfx1201 R9700，HIP 7.16 为预期组件版本；镜像身份保存在每批 environment 和项目锁。稀疏使用 HIP ordinal 2 → 物理 GPU0。solver 启动前该卡被其它任务预约，动态 guard 拒绝分配；solver/graph 改用空闲的 HIP ordinal 1 → 物理 GPU2，物理 GPU3 始终排除。[预约变化证据](../environments/batch3-reservation-change.json)。CUDA 为 nvidia-5090x2 的 RTX 5090、CUDA 13.4.92 / sm_120，环境与命令随每次运行保存。

[24 个反向检查](batch3-negative-checks.json) 全部拒绝：8 个样例各注入一次有限值错误和 NaN；另含 W/V 不配对、两种 solver 的错误 meig、空图、无 GPU kernel、零捕获调用、伪造重复结果与只重放一次。检查基于实际输出副本执行，不将正确程序退出码当作数值正确性。[36 个输入身份重建结果](batch3-input-regeneration.json) 全部通过。

本批没有提升 Xgeev 三例与 gesvdaStridedBatched：前者仍需确认 AMD 路线没有 CPU 兼容回退，后者仍需确认近似 SVD 算法及 residual norm 语义；单凭数值相似不算原功能通过。它们与 nvCOMP/nvJPEG 两个原始功能子集共 6 项仍为 PARTIAL。其它模块的失败原因与恢复条件见[首页矩阵](../../README.md#模块支持矩阵)及逐例页面。历史 GEMM 性能资格仍为 BLOCKED。

## 复现

源码观察副本位于 `rocm/ported`；CUDA 对应副本按 hash 封存在 `migration/source-objects`，原始 CUDA 源码和构建定义不变。CPU 参考使用项目 `build/python-reference` 中的 NumPy 2.3.4 / SciPy 1.16.3。先选择当时空闲、未预约的物理 GPU；下例 ordinal 1 在本批映射物理 GPU2，每次启动仍由 guard 检查。

```bash
python3 tools/migration/restore_observations.py
HIP_VISIBLE_DEVICES=1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batch3_run.py sparse solver graph
python3 tools/migration/package_batch3_cuda.py
scp build/batch3-cuda-sources.tar.gz build/batch3-sparse-fixtures.tar nvidia-5090x2:/home/zihaomu/cuda_samples_on_rocm_compare/build/
ssh nvidia-5090x2 'cd /home/zihaomu/cuda_samples_on_rocm_compare && tar xf build/batch3-cuda-sources.tar.gz && tar xf build/batch3-sparse-fixtures.tar && CUDA_VISIBLE_DEVICES=0 python3 tools/migration/batch3_run.py sparse solver graph --backend cuda --fixture-root build/batch3-sparse-fixtures'
python3 tools/migration/collect_batch3_cuda.py
OPENBLAS_NUM_THREADS=1 python3 tools/migration/batch3_validate.py sparse solver graph --qualify
OPENBLAS_NUM_THREADS=1 python3 tools/migration/batch3_negative_checks.py
python3 tools/migration/regenerate_batch3_inputs.py
```

上述 GPU 重跑后，需重新归档、生成报告并封存当前源码，才能更新发布证据。纯离线核对已有交付一致性：`python3 tools/migration/final_validate.py`。各例的精确命令、输入 hash、源码 hash 和环境见 [ROCm 运行记录](batch3-rocm.json)、[CUDA 运行记录](batch3-cuda.json)及[数值验收](batch3-validation.json)。
'''
(ROOT/'migration/reports/batch3.md').write_text(text)
print('Rendered batch 3 report')
