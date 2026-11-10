# MathDx/cuRANDDx/01_introduction::philox_thread_api.cu

**PARTIAL / L4**

使用rocRAND device Philox4x32-10 + HIP/OCML explicit 53-bit Box-Muller lognormal；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。使用真实rocRAND Philox设备引擎，CPU整数oracle逐word验证counter/subsequence；分布使用显式53-bit Box-Muller。ROCm normal头与当前overlay不兼容，且不声称原例NVIDIA LEGACY host/device逐位相等。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [MathDx/cuRANDDx/01_introduction/philox_thread_api.cu](../../../../../MathDx/cuRANDDx/01_introduction/philox_thread_api.cu) |
| 实际库 / 后端 | rocRAND device Philox4x32-10 + HIP/OCML explicit 53-bit Box-Muller lognormal / rocRAND device Philox4x32-10 + HIP/OCML explicit 53-bit Box-Muller lognormal |
| 候选路线 | rocRAND device API |
| 代码 | [rocm/ported/MathDx/cuRANDDx/01_introduction/philox_thread_api.cu](../../../../../rocm/ported/MathDx/cuRANDDx/01_introduction/philox_thread_api.cu) |
| required cases | 6/7 |
| CUDA baseline / comparison | FAILED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `a983f749cf1cc449d8143db346837aa06e5383603bc56bfcea543ea88f1a4f22` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches12_15/original`, `batches12_15/irregular`, `batches12_15/changed-values`, `batches12_15/boundary`, `batches12_15/repeat`, `batches12_15/singular-or-empty`, `batches12_15/NVIDIA-LEGACY-bitwise-host-device-lognormal-contract`。

实现方式：`API_PORT_WITH_EXECUTION_ADAPTER`。

恢复/扩展条件：未完成合同：NVIDIA-LEGACY-bitwise-host-device-lognormal-contract；补实现/真实后端并重验。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuRANDDx/01_introduction/philox_thread_api.cu:22:10: fatal error: 'curanddx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_wor

尝试库：—；实现 hash：`f362994f340cf3ce4d4ce7cf6c3fc2ac0a5cd4dea912827c4ccceb71d578f701`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2,1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches12_15_run.py b14
OPENBLAS_NUM_THREADS=2 python3 tools/migration/batches12_15_validate.py b14 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuRANDDx_01_introduction_philox_thread_api.cu](../../../../reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuRANDDx_01_introduction_philox_thread_api.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuRANDDx_01_introduction_philox_thread_api.cu](../../../../reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuRANDDx_01_introduction_philox_thread_api.cu)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuRANDDx_01_introduction_philox_thread_api.cu](../../../../reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuRANDDx_01_introduction_philox_thread_api.cu)
- [migration/reports/evidence/20261110T051610.903463Z/batches12_15-rocm/MathDx_cuRANDDx_01_introduction_philox_thread_api.cu](../../../../reports/evidence/20261110T051610.903463Z/batches12_15-rocm/MathDx_cuRANDDx_01_introduction_philox_thread_api.cu)
- [migration/reports/batches12_15-validation.json](../../../../reports/batches12_15-validation.json)
- [migration/reports/evidence/20261110T051436.908488Z/batches12_15-cuda/MathDx_cuRANDDx_01_introduction_philox_thread_api.cu](../../../../reports/evidence/20261110T051436.908488Z/batches12_15-cuda/MathDx_cuRANDDx_01_introduction_philox_thread_api.cu)
- [migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/MathDx_cuRANDDx_01_introduction_philox_thread_api.cu](../../../../reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/MathDx_cuRANDDx_01_introduction_philox_thread_api.cu)
