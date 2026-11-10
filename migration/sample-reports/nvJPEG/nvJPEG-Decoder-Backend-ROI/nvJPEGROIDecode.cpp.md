# nvJPEG/nvJPEG-Decoder-Backend-ROI::nvJPEGROIDecode.cpp

**PARTIAL / L4**

使用 rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode；7 个预登记case通过独立CPU与同输入CUDA。锁定rocJPEG的HYBRID创建返回-12；原始12图中2张progressive由明确标注的libjpeg CPU fallback解码。GPU格式/ROI/缩放/Lanczos/水印和真实CLI已验证，CPU编码不声称AMDGPU JPEG encoder支持。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp](../../../../nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp) |
| 实际库 / 后端 | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode / rocJPEG/HIP runtime + libjpeg-turbo |
| 候选路线 | rocJPEG (decode only), RPP |
| 代码 | [rocm/ported/nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp](../../../../rocm/ported/nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp) |
| required cases | 7/9 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `47fa1a5507565755fbc431714c54f1db61727eba775c064ef2b6f69df4516166` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches9_11/original-corpus`, `batches9_11/formats-scale`, `batches9_11/roi-boundary`, `batches9_11/batch-multi-instance`, `batches9_11/invalid-cli`, `batches9_11/postprocess`, `batches9_11/python-integration`, `batches9_11/native-progressive-GPU-backend`, `batches9_11/decoupled-pipeline-and-native-backend-enums`。

实现方式：`HYBRID_CPU_GPU`。

恢复/扩展条件：缺失范围：native-progressive-GPU-backend,decoupled-pipeline-and-native-backend-enums；需要真实后端/完整harness并重做验收。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.h:38:10: fatal error: 'nvjpeg.h' file not found

尝试库：—；实现 hash：`d9391ab181562e3e84f96f78f7c1a9fd43448f7fc588944896a5e140f9bb6a95`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches9_11_run.py b10
OPENBLAS_NUM_THREADS=1 python3 tools/migration/batches9_11_validate.py b10 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/nvJPEG_nvJPEG-Decoder-Backend-ROI_nvJPEGROIDecode.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/nvJPEG_nvJPEG-Decoder-Backend-ROI_nvJPEGROIDecode.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG_nvJPEG-Decoder-Backend-ROI_nvJPEGROIDecode.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG_nvJPEG-Decoder-Backend-ROI_nvJPEGROIDecode.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG_nvJPEG-Decoder-Backend-ROI_nvJPEGROIDecode.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG_nvJPEG-Decoder-Backend-ROI_nvJPEGROIDecode.cpp)
- [migration/reports/evidence/20261110T043132.627099Z/batches9_11-rocm/nvJPEG_nvJPEG-Decoder-Backend-ROI_nvJPEGROIDecode.cpp](../../../reports/evidence/20261110T043132.627099Z/batches9_11-rocm/nvJPEG_nvJPEG-Decoder-Backend-ROI_nvJPEGROIDecode.cpp)
- [migration/reports/batches9_11-validation.json](../../../reports/batches9_11-validation.json)
- [migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvJPEG_nvJPEG-Decoder-Backend-ROI_nvJPEGROIDecode.cpp](../../../reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvJPEG_nvJPEG-Decoder-Backend-ROI_nvJPEGROIDecode.cpp)
