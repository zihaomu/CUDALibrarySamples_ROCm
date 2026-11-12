# nvJPEG/nvJPEG-Encoder-MultipleInstances::nvJPEGEncMultipleInstances.cpp

**PARTIAL / L4**

原始 C++ 七组 CLI 通过：3张 BMP 自然排序、7次重复、2线程/4状态、Q75/90、420/444、优化 Huffman、硬件不可用/错误输入拒绝；16件JPEG产品独立跨解码与旧路径逐 RGB 字节、采样和量化表一致。非优化 baseline 用 GPU 完成色彩/FDCT/MCU/Huffman/pack/stuff，真实 GPU trace 有7图/84内核、2个独立HIP stream，改输入重放通过。-f 优化 Huffman 仍调用 CPU libjpeg；pinned buffer/事件重叠/自动标定与 GPU prefix 性能尚未完整验收，因此 PARTIAL。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp](../../../../nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp) |
| 实际库 / 后端 | Project HIP multi-stream baseline JPEG color/downsample/FDCT/quant/Huffman/pack/stuff; libjpeg-turbo standard markers and optimized -f fallback / project HIP full baseline JPEG encoder + libjpeg-turbo optimized Huffman fallback |
| 候选路线 | rocJPEG (decode only), RPP |
| 代码 | [rocm/ported/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp](../../../../rocm/ported/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp) |
| required cases | 9/14 |
| CUDA baseline / comparison | FAILED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `f417be2a36bed75baea893712db616416ea748157406dc489ffdf323b9fe8d7e` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`I5/natural-three`, `I5/repeat-seven`, `I5/optimized-444`, `I5/default-backend`, `I5/hardware-unavailable`, `I5/missing-input`, `I5/invalid-quality`, `I5/multi-stream-changed-input-replay`, `I5/sixteen-prior-JPEG-exact-decoded-RGB`, `I5/GPU-optimized-Huffman-table-generation`, `I5/pinned-host-device-workspace-and-event-overlap`, `I5/parallel-GPU-prefix-and-throughput`, `I5/original-auto-calibration-and-backend-selection-semantics`, `I9/fixed-commit-cold-replay-and-independent-review`。

实现方式：`GPU_BASELINE_WITH_EXPLICIT_OPTIMIZED_CPU_FALLBACK`。

恢复/扩展条件：完成 GPU 优化 Huffman 表、pinned host/device workspace/事件重叠、并行 prefix 吞吐和原自动标定/后端选择后，补原生CUDA对照与固定提交冷检出。

CUDA 对照限制：历史原生 nvJPEG 编码器 CUDA baseline 未成功构建；本阶段使用独立 libjpeg/Pillow 跨解码与量化表参考，不把它冒充同输入原始 CUDA 入口对照。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp:34:10: fatal error: 'nvjpeg.h' file not found

尝试库：—；实现 hash：`e35cde04b95951160320631e452c1c41ea50893bfbd7dd6669d0161ec9d26cbb`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 python3 tools/moat/image_encoder_instances_build.py
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 /opt/venv/bin/python tools/moat/image_encoder_instances_run.py
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 /opt/venv/bin/python tools/moat/image_encoder_instances_trace.py
build/image-cpu-venv/bin/python tools/moat/image_encoder_instances_full_compare.py
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/nvJPEG_nvJPEG-Encoder-MultipleInstances_nvJPEGEncMultipleInstances.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/nvJPEG_nvJPEG-Encoder-MultipleInstances_nvJPEGEncMultipleInstances.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG_nvJPEG-Encoder-MultipleInstances_nvJPEGEncMultipleInstances.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG_nvJPEG-Encoder-MultipleInstances_nvJPEGEncMultipleInstances.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG_nvJPEG-Encoder-MultipleInstances_nvJPEGEncMultipleInstances.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG_nvJPEG-Encoder-MultipleInstances_nvJPEGEncMultipleInstances.cpp)
- [migration/reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261112T092622.568541Z-I5-composite-subset-qualification-e8ef77900b](../../../reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261112T092622.568541Z-I5-composite-subset-qualification-e8ef77900b)
- [migration/reports/evidence/rewrite/I5/original-JPEG-encoder-concurrent-HIP-streams-and-changed-input/20261112T092401.701358Z-I5-rocm-trace-7b05ec56f3](../../../reports/evidence/rewrite/I5/original-JPEG-encoder-concurrent-HIP-streams-and-changed-input/20261112T092401.701358Z-I5-rocm-trace-7b05ec56f3)
- [migration/reports/image-jpeg-encoder.md](../../../reports/image-jpeg-encoder.md)
- [migration/reports/image-jpeg-encoder-instances-runs.json](../../../reports/image-jpeg-encoder-instances-runs.json)
- [migration/reports/image-jpeg-encoder-instances-trace.json](../../../reports/image-jpeg-encoder-instances-trace.json)
- [migration/reports/image-jpeg-entropy-prototype.md](../../../reports/image-jpeg-entropy-prototype.md)
- [migration/reports/image-jpeg-encoder-gpu-packing-runs.json](../../../reports/image-jpeg-encoder-gpu-packing-runs.json)
- [migration/reports/image-jpeg-encoder-gpu-packing-trace.json](../../../reports/image-jpeg-encoder-gpu-packing-trace.json)
- [migration/reports/evidence/rewrite/I5/GPU-Huffman-prefix-pack-stuff-build/20261112T093831.801126Z-I5-rocm-build-19a6241159](../../../reports/evidence/rewrite/I5/GPU-Huffman-prefix-pack-stuff-build/20261112T093831.801126Z-I5-rocm-build-19a6241159)
- [migration/reports/evidence/rewrite/I5/GPU-Huffman-pack-stuff-two-real-traces-and-input-change/20261112T093942.919441Z-I5-rocm-trace-329f7dedd1](../../../reports/evidence/rewrite/I5/GPU-Huffman-pack-stuff-two-real-traces-and-input-change/20261112T093942.919441Z-I5-rocm-trace-329f7dedd1)
- [migration/reports/evidence/rewrite/I5/GPU-JPEG-Huffman-prefix-pack-stuff-byte-parity/20261112T093902.336506Z-I5-rocm-prototype-200881a852](../../../reports/evidence/rewrite/I5/GPU-JPEG-Huffman-prefix-pack-stuff-byte-parity/20261112T093902.336506Z-I5-rocm-prototype-200881a852)
- [migration/reports/evidence/rewrite/I5/GPU-JPEG-Huffman-prefix-pack-stuff-byte-parity/20261112T093904.854345Z-I5-rocm-prototype-c88273b9db](../../../reports/evidence/rewrite/I5/GPU-JPEG-Huffman-prefix-pack-stuff-byte-parity/20261112T093904.854345Z-I5-rocm-prototype-c88273b9db)
- [migration/reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261112T101031.858636Z-I5-composite-subset-qualification-48ce947c56](../../../reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261112T101031.858636Z-I5-composite-subset-qualification-48ce947c56)
- [migration/reports/evidence/rewrite/I5/original-JPEG-encoder-concurrent-HIP-streams-and-changed-input/20261112T100631.107895Z-I5-rocm-trace-c6f9a5a6c2](../../../reports/evidence/rewrite/I5/original-JPEG-encoder-concurrent-HIP-streams-and-changed-input/20261112T100631.107895Z-I5-rocm-trace-c6f9a5a6c2)
- [migration/reports/image-jpeg-encoder-instances-full-comparison.json](../../../reports/image-jpeg-encoder-instances-full-comparison.json)
