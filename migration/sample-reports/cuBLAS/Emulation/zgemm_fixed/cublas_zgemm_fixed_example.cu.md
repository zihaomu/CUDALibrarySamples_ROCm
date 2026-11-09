# cuBLAS/Emulation/zgemm_fixed::cublas_zgemm_fixed_example.cu

**FAILED / L1**

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu:54:5: error: unknown type name 'cudaEmulationMantissaControl_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu:54:47: error: use of undeclared identifier 'CUDA_EMULATION_MANTISSA_CONTROL_FIXED'

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLAS/Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu](../../../../../cuBLAS/Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu) |
| 实际库 / 后端 | — / — |
| 候选路线 | hipBLAS, rocBLAS |
| 代码 | [rocm/ported/cuBLAS/Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu](../../../../../rocm/ported/cuBLAS/Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu) |
| required cases | 0/2 |
| CUDA baseline / comparison | PASSED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `d8383c8a1da5aacceee3b5213599570c2c7a226d886d54e978d920fed714ef1e` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu:54:5: error: unknown type name 'cudaEmulationMantissaControl_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu:54:47: error: use of undeclared identifier 'CUDA_EMULATION_MANTISSA_CONTROL_FIXED'

尝试库：—；实现 hash：`0d8b1632e27682f6b519576f6f894b72a36c667c7694c3688ff2d780c3ae587f`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu](../../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu](../../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu](../../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu](../../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu](../../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu)
- [migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu](../../../../reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu)
- [migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu](../../../../reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu)
