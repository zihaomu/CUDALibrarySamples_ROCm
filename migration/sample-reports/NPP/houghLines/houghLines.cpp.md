# NPP/houghLines::houghLines.cpp

**PARTIAL / L3**

19个完整C++ CLI及逐字节PPM/逐峰CPU、11项GPU运行合同、原生5090对照和真实kernel trace通过；低阈值1196峰由项目诊断CSV完整核对。项目与NPP默认PPM有10627 RGB像素差异，五条真值都覆盖。固定提交冷检出、三范围复审、组合资格Git锚定尚未完成，因此仅PARTIAL。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP/houghLines/houghLines.cpp](../../../../NPP/houghLines/houghLines.cpp) |
| 实际库 / 后端 | Project HIP C1 Canny and Hough accumulator/peak kernels / project HIP image Hough |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP/houghLines/houghLines.cpp](../../../../rocm/ported/NPP/houghLines/houghLines.cpp) |
| required cases | 5/8 |
| CUDA baseline / comparison | PASSED / OBSERVED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `2433c9caa3838ee4f32d31f3e1d1930c1b1b9add72883335c64928ba3e7d7b50` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`hough/14-frozen-CLI-and-PPM`, `hough/5-valid-nondefault-CLI`, `hough/11-runtime-and-independent-peaks`, `hough/native-complete-PPM-comparison`, `hough/real-Canny-vote-peak-kernel-trace`, `hough/cold-clean-checkout`, `hough/three-independent-reviews`, `hough/sealed-qualification-and-Git-publication`。

实现方式：`DOCUMENTED_HOUGH_ACCUMULATOR_VARIANT`。

恢复/扩展条件：固定源码冷检出、独立复审和组合资格通过后才升级PASSED。

CUDA 对照限制：原始NPP与项目均检出10条线且五真值覆盖，部分rho偏1像素；red IoU 0.23946，不声称逐像素相同。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/houghLines/houghLines.cpp:33:10: fatal error: 'npp.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySample

尝试库：—；实现 hash：`1ca4206b5b60078e10655a5703bf1dfac511104c9e902de6a7ccd54ac8e381d1`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python3 tools/moat/image_hough_contracts.py
python3 tools/moat/image_hough_build.py
python3 tools/moat/image_hough_run.py
build/image-cpu-venv/bin/python tools/moat/image_hough_reference.py
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/NPP_houghLines_houghLines.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/NPP_houghLines_houghLines.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP_houghLines_houghLines.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/NPP_houghLines_houghLines.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP_houghLines_houghLines.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/NPP_houghLines_houghLines.cpp)
- [migration/reports/image-hough.md](../../../reports/image-hough.md)
- [migration/reports/image-hough-contracts.json](../../../reports/image-hough-contracts.json)
- [migration/reports/image-hough-build.json](../../../reports/image-hough-build.json)
- [migration/reports/image-hough-runs.json](../../../reports/image-hough-runs.json)
- [migration/reports/image-hough-validation.json](../../../reports/image-hough-validation.json)
- [migration/reports/image-hough-options.json](../../../reports/image-hough-options.json)
- [migration/reports/image-hough-runtime.json](../../../reports/image-hough-runtime.json)
- [migration/reports/image-hough-runtime-validation.json](../../../reports/image-hough-runtime-validation.json)
- [migration/reports/image-hough-trace.json](../../../reports/image-hough-trace.json)
- [migration/reports/image-hough-native-comparison.json](../../../reports/image-hough-native-comparison.json)
