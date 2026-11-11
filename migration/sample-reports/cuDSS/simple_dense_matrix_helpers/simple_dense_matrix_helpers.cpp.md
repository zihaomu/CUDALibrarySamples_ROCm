# cuDSS/simple_dense_matrix_helpers::simple_dense_matrix_helpers.cpp

**PARTIAL / L3**

R9候选实现已完成构建并进入独立CPU/native CUDA及原始合同验收；尚未签发复合资格，不计整例通过。历史原生API自动移植失败保留。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/simple_dense_matrix_helpers/simple_dense_matrix_helpers.cpp](../../../../cuDSS/simple_dense_matrix_helpers/simple_dense_matrix_helpers.cpp) |
| 实际库 / 后端 | Project host matrix-descriptor C ABI + HIP device storage/pointer tables / Project HIP runtime adapter |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/simple_dense_matrix_helpers/simple_dense_matrix_helpers.cpp](../../../../rocm/ported/cuDSS/simple_dense_matrix_helpers/simple_dense_matrix_helpers.cpp) |
| required cases | 1/5 |
| CUDA baseline / comparison | PASSED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `9b41e9c37c3ae9f0f4b25e19ad1e4c08bd3e75d959b04daeb2d44420c3ba5743` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite-R9/current-build`, `rewrite-R9/frozen-inputs-and-original-contract`, `rewrite-R9/CPU-and-native-CUDA`, `rewrite-R9/negative-and-runtime`, `rewrite-R9/independent-review-and-qualification`。

实现方式：`API_PORT`。

恢复/扩展条件：完成当前源码完整原始合同、实际语言/CLI、独立CPU/native CUDA、故障及边界检查和固定提交独立复审后再签发资格。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuDSS/simple_dense_matrix_helpers/simple_dense_matrix_helpers.cpp:24:10: fatal error: 'cudss.h' file not found

尝试库：—；实现 hash：`cf6cdcf0a7cdaaf309f9664ab6e0873bc10fb4d8e3f76bbfbae00db9e2c8222a`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuDSS_simple_dense_matrix_helpers_simple_dense_matrix_helpers.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/cuDSS_simple_dense_matrix_helpers_simple_dense_matrix_helpers.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuDSS_simple_dense_matrix_helpers_simple_dense_matrix_helpers.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/cuDSS_simple_dense_matrix_helpers_simple_dense_matrix_helpers.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuDSS_simple_dense_matrix_helpers_simple_dense_matrix_helpers.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/cuDSS_simple_dense_matrix_helpers_simple_dense_matrix_helpers.cpp)
- [migration/reports/rewrite-R9.md](../../../reports/rewrite-R9.md)
- [migration/reports/rewrite-R9-helper-originals.json](../../../reports/rewrite-R9-helper-originals.json)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_dense_matrix_helpers__simple_dense_matrix_helpers.cpp/20261111T062641.870114Z-R9-cuda-original-6459d33c5d](../../../reports/evidence/rewrite/R9/cuDSS_simple_dense_matrix_helpers__simple_dense_matrix_helpers.cpp/20261111T062641.870114Z-R9-cuda-original-6459d33c5d)
