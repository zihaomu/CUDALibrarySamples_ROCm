# cuBLAS/Emulation/bf16x9_gemmEx::cublas_GemmEx_example.cu

**FAILED / L1**

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu:125:45: error: use of undeclared identifier 'CUBLAS_EMULATION_STRATEGY_EAGER'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu:129:45: error: use of undeclared identifier 'CUBLAS_COMPUTE_32F_EMULATED_16BFX9'

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLAS/Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu](../../../../../cuBLAS/Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu) |
| 实际库 / 后端 | — / — |
| 候选路线 | hipBLAS, rocBLAS |
| 代码 | [rocm/ported/cuBLAS/Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu](../../../../../rocm/ported/cuBLAS/Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu) |
| required cases | 0/2 |
| CUDA baseline / comparison | PASSED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `854409bfea208703e71c180c681218ab75dfa1546a6dda1a1ab3aa1e324ebc50` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu:125:45: error: use of undeclared identifier 'CUBLAS_EMULATION_STRATEGY_EAGER'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu:129:45: error: use of undeclared identifier 'CUBLAS_COMPUTE_32F_EMULATED_16BFX9'

尝试库：—；实现 hash：`9bcc2427f4cb194f6919b684335fc4a146c0e7abc393e5f52a8670944ae4989e`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu](../../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu](../../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu](../../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu](../../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu](../../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu)
- [migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu](../../../../reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu)
- [migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu](../../../../reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu)
