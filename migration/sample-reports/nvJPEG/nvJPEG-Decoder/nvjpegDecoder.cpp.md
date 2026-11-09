# nvJPEG/nvJPEG-Decoder::nvjpegDecoder.cpp

**PARTIAL / L3**

硬件 backend 对原仓库 64×64 baseline cat JPEG 解码 RGB，通过独立 Pillow/libjpeg 对照（最大像素误差 2）；原始所有输入/格式、batch/多实例/CLI 未覆盖，保留 PARTIAL。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp](../../../../nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp) |
| 实际库 / 后端 | rocJPEG / rocJPEG |
| 候选路线 | rocJPEG (decode only), RPP |
| 代码 | [rocm/probes/rocjpeg_decode.cpp](../../../../rocm/probes/rocjpeg_decode.cpp) |
| required cases | 1/2 |
| CUDA baseline / comparison | FAILED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `6f39206e88ab6d10d43a06bd766166ccca415e42bafe911b03192da47b63b36d` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`gpu-subset-probe`, `original-full-functional-contract`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvJPEG/nvJPEG-Decoder/nvjpegDecoder.h:42:10: fatal error: 'nvjpeg.h' file not found

尝试库：—；实现 hash：`60b6bdb7eb2e4a398eb3035a0fa79756c3cadad15cdad2a21452d35ccd75cf8c`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python tools/migration/probes.py rocjpeg_decode
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/nvJPEG_nvJPEG-Decoder_nvjpegDecoder.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/nvJPEG_nvJPEG-Decoder_nvjpegDecoder.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG_nvJPEG-Decoder_nvjpegDecoder.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG_nvJPEG-Decoder_nvjpegDecoder.cpp)
- [migration/reports/native-probes.json](../../../reports/native-probes.json)
- [migration/reports/evidence/20261109T084040.925641Z/native-probes/rocjpeg_decode](../../../reports/evidence/20261109T084040.925641Z/native-probes/rocjpeg_decode)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG_nvJPEG-Decoder_nvjpegDecoder.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG_nvJPEG-Decoder_nvjpegDecoder.cpp)
