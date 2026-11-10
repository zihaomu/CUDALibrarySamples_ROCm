# cuBLAS/Level-3/gemm3m::cublas_gemm3m_example.cu

**PASSED / L4**

原始数据/精度/布局与登记扩展用例通过 AMD、独立 CPU、相同输入 CUDA 验收；真实执行语义、反向检查及独立复审完成。实际路线：hipBLAS/rocBLAS three real SGEMMs + HIP complex split/merge。性能未验收。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLAS/Level-3/gemm3m/cublas_gemm3m_example.cu](../../../../../cuBLAS/Level-3/gemm3m/cublas_gemm3m_example.cu) |
| 实际库 / 后端 | hipBLAS/rocBLAS three real SGEMMs + HIP complex split/merge / rocBLAS |
| 候选路线 | hipBLAS, rocBLAS |
| 代码 | [rocm/ported/cuBLAS/Level-3/gemm3m/cublas_gemm3m_example.cu](../../../../../rocm/ported/cuBLAS/Level-3/gemm3m/cublas_gemm3m_example.cu) |
| required cases | 7/7 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `13ab21f67975f30a1291375dc49de336f3d0994c3721390283e22e19a82865e6` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite/original`, `rewrite/changed-values`, `rewrite/irregular`, `rewrite/layout`, `rewrite/repeat`, `rewrite/boundary`, `rewrite/independent-negative-checks`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Level-3/gemm3m/cublas_gemm3m_example.cu:88:18: error: use of undeclared identifier 'cublasCgemm3m'

尝试库：—；实现 hash：`54f01e76d908d715496b068e5cb1e27a84f49d54d65cbd17330641fdf5e5ed44`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Level-3_gemm3m_cublas_gemm3m_example.cu](../../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Level-3_gemm3m_cublas_gemm3m_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Level-3_gemm3m_cublas_gemm3m_example.cu](../../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Level-3_gemm3m_cublas_gemm3m_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Level-3_gemm3m_cublas_gemm3m_example.cu](../../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Level-3_gemm3m_cublas_gemm3m_example.cu)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuBLAS_Level-3_gemm3m_cublas_gemm3m_example.cu](../../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuBLAS_Level-3_gemm3m_cublas_gemm3m_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Level-3_gemm3m_cublas_gemm3m_example.cu](../../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Level-3_gemm3m_cublas_gemm3m_example.cu)
- [migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Level-3_gemm3m_cublas_gemm3m_example.cu](../../../../reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Level-3_gemm3m_cublas_gemm3m_example.cu)
- [migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_gemm3m_cublas_gemm3m_example.cu](../../../../reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_gemm3m_cublas_gemm3m_example.cu)
- [migration/reports/evidence/rewrite/R1/cuBLAS_Level-3_gemm3m__cublas_gemm3m_example.cu/20261110T083832.851647Z-R1-composite-qualification-6dce52aae0](../../../../reports/evidence/rewrite/R1/cuBLAS_Level-3_gemm3m__cublas_gemm3m_example.cu/20261110T083832.851647Z-R1-composite-qualification-6dce52aae0)
- [migration/reports/rewrite-first-qualification.json](../../../../reports/rewrite-first-qualification.json)
- [migration/reports/rewrite-first-negative.json](../../../../reports/rewrite-first-negative.json)
- [migration/reports/rewrite-evidence-errata.json](../../../../reports/rewrite-evidence-errata.json)
