# MathDx/cuFFTDx/08_mixed_precision::mixed_precision_fft_2d.cu

**FAILED / L1**

build 失败：/opt/rocm/core-10.1/include/hip/amd_detail/amd_hip_cooperative_groups.h:412:11: error: use of undeclared identifier 'min'; did you mean 'fmin'?；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuFFTDx/08_mixed_precision/mixed_precision_fft_2d.cu:26:10: fatal error: 'cufftdx.hpp' file not found

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [MathDx/cuFFTDx/08_mixed_precision/mixed_precision_fft_2d.cu](../../../../../MathDx/cuFFTDx/08_mixed_precision/mixed_precision_fft_2d.cu) |
| 实际库 / 后端 | — / — |
| 候选路线 | unresolved device FFT |
| 代码 | [rocm/ported/MathDx/cuFFTDx/08_mixed_precision/mixed_precision_fft_2d.cu](../../../../../rocm/ported/MathDx/cuFFTDx/08_mixed_precision/mixed_precision_fft_2d.cu) |
| required cases | 0/2 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `46f867ad9bb8bf2483f2d44b0d871f77799d4f333401847fa04caa3c6ae365a9` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/opt/rocm/core-10.1/include/hip/amd_detail/amd_hip_cooperative_groups.h:412:11: error: use of undeclared identifier 'min'; did you mean 'fmin'?；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuFFTDx/08_mixed_precision/mixed_precision_fft_2d.cu:26:10: fatal error: 'cufftdx.hpp' file not found

尝试库：—；实现 hash：`7adc9b711b8dce80ba9216b8cd49aae873419b3c738d3f53e26d496695d18170`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuFFTDx_08_mixed_precision_mixed_precision_fft_2d.cu](../../../../reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuFFTDx_08_mixed_precision_mixed_precision_fft_2d.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuFFTDx_08_mixed_precision_mixed_precision_fft_2d.cu](../../../../reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuFFTDx_08_mixed_precision_mixed_precision_fft_2d.cu)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuFFTDx_08_mixed_precision_mixed_precision_fft_2d.cu](../../../../reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuFFTDx_08_mixed_precision_mixed_precision_fft_2d.cu)
