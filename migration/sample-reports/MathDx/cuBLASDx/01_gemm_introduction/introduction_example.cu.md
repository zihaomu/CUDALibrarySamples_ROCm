# MathDx/cuBLASDx/01_gemm_introduction::introduction_example.cu

**PASSED / L4**

使用HIP cooperative device FP64 GEMM (shared, register-accumulate, register-store phases)；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。仅登记profile/规模/执行方式通过，不外推其它dtype、规模、网格或性能；内部数据重分配/CPU布局编排与项目GPU算法已公开。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu](../../../../../MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu) |
| 实际库 / 后端 | HIP cooperative device FP64 GEMM (shared, register-accumulate, register-store phases) / HIP cooperative device FP64 GEMM (shared, register-accumulate, register-store phases) |
| 候选路线 | rocWMMA, Composable Kernel |
| 代码 | [rocm/ported/MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu](../../../../../rocm/ported/MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu) |
| required cases | 6/6 |
| CUDA baseline / comparison | FAILED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `2b4a07e4a4980fd1e3f22688af5438cdd9a33f5ec1ac251f9291987775563dd2` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches12_15/original`, `batches12_15/irregular`, `batches12_15/changed-values`, `batches12_15/boundary`, `batches12_15/repeat`, `batches12_15/singular-or-empty`。

实现方式：`API_PORT_WITH_EXECUTION_ADAPTER`。

恢复/扩展条件：扩展其它dtype、规模、线程块/进程网格、多节点或性能需新增登记case并重验。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu:24:10: fatal error: 'cublasdx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sa

尝试库：—；实现 hash：`bce9150b18c0121cbc3ddd2797d03e373c168a131be9c21fb94eb7abb50c43a3`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2,1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches12_15_run.py b14
OPENBLAS_NUM_THREADS=2 python3 tools/migration/batches12_15_validate.py b14 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu](../../../../reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu](../../../../reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu](../../../../reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu)
- [migration/reports/evidence/20261110T051610.903463Z/batches12_15-rocm/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu](../../../../reports/evidence/20261110T051610.903463Z/batches12_15-rocm/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu)
- [migration/reports/batches12_15-validation.json](../../../../reports/batches12_15-validation.json)
- [migration/reports/evidence/20261110T051436.908488Z/batches12_15-cuda/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu](../../../../reports/evidence/20261110T051436.908488Z/batches12_15-cuda/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu)
- [migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu](../../../../reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu)
