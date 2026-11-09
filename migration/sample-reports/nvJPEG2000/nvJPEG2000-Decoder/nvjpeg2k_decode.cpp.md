# nvJPEG2000/nvJPEG2000-Decoder::nvjpeg2k_decode.cpp

**FAILED / L1**

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvJPEG2000/nvJPEG2000-Decoder/nvjpeg2k_decode.h:52:10: fatal error: 'nvjpeg2k.h' file not found

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvJPEG2000/nvJPEG2000-Decoder/nvjpeg2k_decode.cpp](../../../../nvJPEG2000/nvJPEG2000-Decoder/nvjpeg2k_decode.cpp) |
| 实际库 / 后端 | — / — |
| 候选路线 | unresolved |
| 代码 | [rocm/ported/nvJPEG2000/nvJPEG2000-Decoder/nvjpeg2k_decode.cpp](../../../../rocm/ported/nvJPEG2000/nvJPEG2000-Decoder/nvjpeg2k_decode.cpp) |
| required cases | 0/2 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `06beb1ffb836585b92d1cbdef8ab8b5724d063dadc9902424cefd5ec5753b754` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：提供可在锁定 AMD 环境工作的 GPU JPEG2000 codec/实现，保留原例 bit depth、batch、输出与质量要求。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvJPEG2000/nvJPEG2000-Decoder/nvjpeg2k_decode.h:52:10: fatal error: 'nvjpeg2k.h' file not found

尝试库：—；实现 hash：`5e75c16055dcae6a19190bbe66406ed34b4c2706098b5ef76d81da9a386349f0`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/nvJPEG2000_nvJPEG2000-Decoder_nvjpeg2k_decode.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/nvJPEG2000_nvJPEG2000-Decoder_nvjpeg2k_decode.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG2000_nvJPEG2000-Decoder_nvjpeg2k_decode.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG2000_nvJPEG2000-Decoder_nvjpeg2k_decode.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG2000_nvJPEG2000-Decoder_nvjpeg2k_decode.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG2000_nvJPEG2000-Decoder_nvjpeg2k_decode.cpp)
