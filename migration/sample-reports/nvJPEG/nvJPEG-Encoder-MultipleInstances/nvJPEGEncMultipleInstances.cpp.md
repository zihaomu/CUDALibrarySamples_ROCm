# nvJPEG/nvJPEG-Encoder-MultipleInstances::nvJPEGEncMultipleInstances.cpp

**PARTIAL / L4**

48项入口子集通过：原40项加8组大图24产品，含65535长轴；64位索引、29组容量预检、实测prefix阈值128/64及24组边界证据齐备。窄图CPU上采样模式修订经6个新保留输入验证，原失败独立保留。完整编码质量CPU/native保留集、无profiler性能分布/峰值内存和冷构建待完成，保持PARTIAL；最大方图仅验证索引和容量拒绝，不声称实际编码。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp](../../../../nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp) |
| 实际库 / 后端 | Project HIP wide-index baseline/optimized JPEG, measured checked serial/tiled prefix, pinned buffers and event-driven slots; CPU markers/DHT design / HIP async full baseline/optimized JPEG + CPU libjpeg-turbo DHT/header design |
| 候选路线 | rocJPEG (decode only), RPP |
| 代码 | [rocm/ported/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp](../../../../rocm/ported/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp) |
| required cases | 48/51 |
| CUDA baseline / comparison | PASSED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `f417be2a36bed75baea893712db616416ea748157406dc489ffdf323b9fe8d7e` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`IMG-01/natural-three`, `IMG-01/repeat-seven`, `IMG-01/optimized-444`, `IMG-01/quality-clamp-low`, `IMG-01/quality-clamp-high`, `IMG-01/download-no-write`, `IMG-01/device-only`, `IMG-01/truncate-before-state-expansion`, `IMG-01/negative-n-zero-r-clamps`, `IMG-01/single-input-repeats`, `IMG-01/auto-calibration`, `IMG-01/help-anywhere`, `IMG-01/hardware-unavailable`, `IMG-01/negative-states`, `IMG-01/missing-input`, `IMG-01/all33-JPEG-byte-exact`, `IMG-01/trace-repeat-seven`, `IMG-01/trace-optimized-444`, `IMG-01/trace-device-only`, `IMG-01/changed-input-replay`, `IMG-01/runtime-n0-s0-j1`, `IMG-01/runtime-threads-exceed-states`, `IMG-01/runtime-states-exceed-threads`, `IMG-01/runtime-three-runs`, `IMG-01/runtime-j0-hardware-concurrency`, `IMG-01/runtime-gpu-and-unavailable-hardware`, `IMG-01/runtime-mixed-size-slot-growth-reuse`, `IMG-01/runtime-single-large-repeated`, `IMG-01/runtime-truncated-BMP`, `IMG-01/runtime-DIB-length-beyond-file`, `IMG-01/runtime-zero-width-BMP`, `IMG-01/runtime-invalid-numeric-CLI`, `IMG-01/runtime-empty-directory`, `IMG-01/runtime-output-path-is-file`, `IMG-01/runtime-write-failure-after-GPU`, `IMG-01/runtime-truncated-last-mixed-input`, `IMG-01/prepared-standard`, `IMG-01/prepared-optimized-repeated`, `IMG-01/prepared-device-only`, `IMG-01/prepared-input-lifecycle`, `IMG-01/entry-65500x1-s1`, `IMG-01/entry-65500x1-s2`, `IMG-01/entry-1x65500-s1`, `IMG-01/entry-1x65500-s2`, `IMG-01/entry-4097x4095-s1`, `IMG-01/entry-4097x4095-s2`, `IMG-01/entry-65535x1-maximum-axis`, `IMG-01/entry-1x65535-maximum-axis`, `IMG-01/held-out-native-CPU-equivalence`, `IMG-01/performance-distributions-peak-memory`, `IMG-10/committed-cold-rebuild-final-review`。

实现方式：`GPU_ASYNC_JPEG_WITH_BOUNDED_CPU_THREAD_CALIBRATION`。

恢复/扩展条件：Full held-out native/CPU encoder pixel equivalence; nonprofiled latency/throughput distributions and peak memory; committed cold rebuild and final review. Maximum square geometry is capacity-preflight evidence, not a full allocation/encoding claim.

CUDA 对照限制：原始CUDA构建及80项新编码质量矩阵运行成功；当前生产编码器在Q1/420渐变图的局部重建误差未达冻结门槛，系数诊断指向DC量化舍入边界。独立舍入候选验证中；不能把80项运行成功当作完整三方通过。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp:34:10: fatal error: 'nvjpeg.h' file not found

尝试库：—；实现 hash：`e35cde04b95951160320631e452c1c41ea50893bfbd7dd6669d0161ec9d26cbb`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 /opt/venv/bin/python tools/moat/image_encoder_instances_v2.py build
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 /opt/venv/bin/python tools/moat/image_encoder_instances_v2.py run
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 /opt/venv/bin/python tools/moat/image_encoder_instances_v2_trace.py
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 /opt/venv/bin/python tools/moat/image_encoder_instances_v2_compare.py
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
- [migration/reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261112T111813.647313Z-I5-composite-subset-qualification-f5bc6c8843](../../../reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261112T111813.647313Z-I5-composite-subset-qualification-f5bc6c8843)
- [migration/reports/evidence/rewrite/I5/original-JPEG-encoder-concurrent-HIP-streams-and-changed-input/20261112T111658.917395Z-I5-rocm-trace-b3bbf722d3](../../../reports/evidence/rewrite/I5/original-JPEG-encoder-concurrent-HIP-streams-and-changed-input/20261112T111658.917395Z-I5-rocm-trace-b3bbf722d3)
- [migration/reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261113T031657.268240Z-I5-composite-subset-qualification-fd52687b9f](../../../reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261113T031657.268240Z-I5-composite-subset-qualification-fd52687b9f)
- [migration/reports/evidence/rewrite/I5/async-original-entry-multithread-trace/20261113T031215.898114Z-I5-rocm-trace-c01c1ac536](../../../reports/evidence/rewrite/I5/async-original-entry-multithread-trace/20261113T031215.898114Z-I5-rocm-trace-c01c1ac536)
- [migration/reports/evidence/rewrite/I0/completion-encoder-original-natural-three/20261113T024100.571136Z-I0-cuda-native-c221dd0932](../../../reports/evidence/rewrite/I0/completion-encoder-original-natural-three/20261113T024100.571136Z-I0-cuda-native-c221dd0932)
- [migration/reports/image-completion-IMG-01.md](../../../reports/image-completion-IMG-01.md)
- [migration/reports/image-encoder-instances-v2-runs.json](../../../reports/image-encoder-instances-v2-runs.json)
- [migration/reports/image-encoder-instances-v2-comparison.json](../../../reports/image-encoder-instances-v2-comparison.json)
- [migration/reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261113T034424.399537Z-I5-composite-subset-qualification-ff819aa0cd](../../../reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261113T034424.399537Z-I5-composite-subset-qualification-ff819aa0cd)
- [migration/reports/evidence/rewrite/I5/async-original-entry-multithread-trace/20261113T033948.008552Z-I5-rocm-trace-178ac12203](../../../reports/evidence/rewrite/I5/async-original-entry-multithread-trace/20261113T033948.008552Z-I5-rocm-trace-178ac12203)
- [migration/reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261113T044153.180027Z-I5-composite-subset-qualification-e9111050ed](../../../reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261113T044153.180027Z-I5-composite-subset-qualification-e9111050ed)
- [migration/reports/evidence/rewrite/I5/async-original-entry-multithread-trace/20261113T041703.076751Z-I5-rocm-trace-a56f853ce5](../../../reports/evidence/rewrite/I5/async-original-entry-multithread-trace/20261113T041703.076751Z-I5-rocm-trace-a56f853ce5)
- [migration/reports/image-encoder-quality-cpu.json](../../../reports/image-encoder-quality-cpu.json)
- [migration/reports/image-encoder-Q1-diagnosis.json](../../../reports/image-encoder-Q1-diagnosis.json)
