# cuPQC::example_sha3.cu

**PASSED / L4**

SHA2 one thread; SHA3 cooperative 32-lane wave, one GPU kernel; original input plus padding/rate boundaries；14 个输入与独立 hashlib 精确一致

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuPQC/example_sha3.cu](../../../cuPQC/example_sha3.cu) |
| 实际库 / 后端 | HIP runtime + custom device SHA implementation / HIP/gfx1201 |
| 候选路线 | custom HIP SHA2/SHA3, unresolved post-quantum device APIs |
| 代码 | [rocm/cuPQC/sha3_256.hip](../../../rocm/cuPQC/sha3_256.hip) |
| required cases | 14/14 |
| CUDA baseline / comparison | BLOCKED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `5e6bb6816f8f63a6d0e8372111413baa8e4c17c28707a13fd46a621cd4050d29` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original`, `length-0`, `length-1`, `length-55`, `length-56`, `length-63`, `length-64`, `length-65`, `length-135`, `length-136`, `length-137`, `length-271`, `length-272`, `length-1000`。

实现方式：`HYBRID_HIP`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA SHA 检查使用同一自有实现；NVIDIA cuPQC vendor SDK 基线不可用，两者范围分别记录。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuPQC/example_sha3.cu:21:10: fatal error: 'cuhash.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_R

尝试库：—；实现 hash：`448eb02fae998022a37e9061211df36f93b105c216775b52c1e0f6e26e5005f7`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuPQC_example_sha3.cu](../../reports/evidence/20261109T083217.050455Z/original-rocm/cuPQC_example_sha3.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuPQC_example_sha3.cu](../../reports/evidence/20261109T084256.329631Z/original-rocm/cuPQC_example_sha3.cu)
- [migration/reports/evidence/20261109T084621.449957Z/hash-rocm/sha3](../../reports/evidence/20261109T084621.449957Z/hash-rocm/sha3)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuPQC_example_sha3.cu](../../reports/evidence/20261109T084857.451692Z/original-cuda/cuPQC_example_sha3.cu)
- [migration/reports/additional-comparison.json](../../reports/additional-comparison.json)
