# cuBLASLt/LtDgemmPresetAlgo::main.cpp

**FAILED / L1**

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtDgemmPresetAlgo/sample_cublasLt_LtDgemmPresetAlgo.cu:54:11: error: unknown type name 'cublasLtMatmulTile_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtDgemmPresetAlgo/sample_cublasLt_LtDgemmPresetAlgo.cu:54:41: error: use of undeclared identifier 'CUBLASLT_MATMUL_TILE_16x16'

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLASLt/LtDgemmPresetAlgo/main.cpp](../../../../cuBLASLt/LtDgemmPresetAlgo/main.cpp) |
| 实际库 / 后端 | — / — |
| 候选路线 | hipBLASLt |
| 代码 | [rocm/ported/cuBLASLt/LtDgemmPresetAlgo/main.cpp](../../../../rocm/ported/cuBLASLt/LtDgemmPresetAlgo/main.cpp) |
| required cases | 0/2 |
| CUDA baseline / comparison | PASSED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `6eb8d322391e85b921c11547cbb51b07caf4a3e9ca97edc264fbc29878efe6ea` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtDgemmPresetAlgo/sample_cublasLt_LtDgemmPresetAlgo.cu:54:11: error: unknown type name 'cublasLtMatmulTile_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtDgemmPresetAlgo/sample_cublasLt_LtDgemmPresetAlgo.cu:54:41: error: use of undeclared identifier 'CUBLASLT_MATMUL_TILE_16x16'

尝试库：hipblaslt；实现 hash：`58b6497a9bba4f9f13c321685159eba8bfc7cb23c6f740db31425bea92d97ca1`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp](../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp](../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp)
- [migration/reports/evidence/20261109T085205.912828Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp](../../../reports/evidence/20261109T085205.912828Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp)
- [migration/reports/evidence/20261109T085546.110648Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp](../../../reports/evidence/20261109T085546.110648Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp)
- [migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp](../../../reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtDgemmPresetAlgo_main.cpp](../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtDgemmPresetAlgo_main.cpp)
