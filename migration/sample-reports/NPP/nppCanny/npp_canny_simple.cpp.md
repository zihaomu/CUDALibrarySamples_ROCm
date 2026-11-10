# NPP/nppCanny::npp_canny_simple.cpp

**PARTIAL / L4**

使用HIP three-channel Sobel/NMS/connected hysteresis kernels；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。GPU三通道最大梯度/Sobel/NMS/滞后连接已全像素验收；原生NPP C3梯度与NMS tie策略及原例OpenCV文件CLI未完成逐像素等价。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP/nppCanny/npp_canny_simple.cpp](../../../../NPP/nppCanny/npp_canny_simple.cpp) |
| 实际库 / 后端 | HIP three-channel Sobel/NMS/connected hysteresis kernels / HIP three-channel Sobel/NMS/connected hysteresis kernels |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP/nppCanny/npp_canny_simple.cpp](../../../../rocm/ported/NPP/nppCanny/npp_canny_simple.cpp) |
| required cases | 6/7 |
| CUDA baseline / comparison | FAILED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `baf56fa10d093239368ac3feb40874b3d76f9a9d97824697ea8851d196a68eb4` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches12_15/original`, `batches12_15/irregular`, `batches12_15/changed-values`, `batches12_15/boundary`, `batches12_15/repeat`, `batches12_15/singular-or-empty`, `batches12_15/native-NPP-C3-gradient-tie-and-file-CLI-equivalence`。

实现方式：`API_PORT_WITH_EXECUTION_ADAPTER`。

恢复/扩展条件：未完成合同：native-NPP-C3-gradient-tie-and-file-CLI-equivalence；补实现/真实后端并重验。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/nppCanny/npp_canny_simple.cpp:33:10: fatal error: 'opencv2/opencv.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/

尝试库：—；实现 hash：`7adbac6cac499239424949127761525e82d9128380500cadd717b0283b1b8c50`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2,1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches12_15_run.py b15
OPENBLAS_NUM_THREADS=2 python3 tools/migration/batches12_15_validate.py b15 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/evidence/20261110T051547.561861Z/batches12_15-rocm/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261110T051547.561861Z/batches12_15-rocm/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/batches12_15-validation.json](../../../reports/batches12_15-validation.json)
- [migration/reports/evidence/20261110T051436.908488Z/batches12_15-cuda/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261110T051436.908488Z/batches12_15-cuda/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/evidence/20261110T053436.400711Z/batches12_15-rocm/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261110T053436.400711Z/batches12_15-rocm/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/evidence/20261110T053230.152526Z/batches12_15-cuda/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261110T053230.152526Z/batches12_15-cuda/NPP_nppCanny_npp_canny_simple.cpp)
