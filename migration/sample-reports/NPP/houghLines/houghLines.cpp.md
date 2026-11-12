# NPP/houghLines::houghLines.cpp

**PASSED / L4**

完整C++原例、19输入/有效参数/错误CLI及逐字节PPM和完整诊断线表、19运行合同与外设备空流拒绝、真实GPU Sobel/NMS/threshold/votes/peaks、45子记录干净检出与三范围独立复审通过。项目CPU逐线/逐峰/全PPM精确；当前NPP原生默认PPM差10627 RGB像素，五条真值各被双方两条线覆盖。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP/houghLines/houghLines.cpp](../../../../NPP/houghLines/houghLines.cpp) |
| 实际库 / 后端 | Project HIP C1 Canny plus GPU Hough votes and peak extraction / project HIP image Hough |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP/houghLines/houghLines.cpp](../../../../rocm/ported/NPP/houghLines/houghLines.cpp) |
| required cases | 26/26 |
| CUDA baseline / comparison | PASSED / OBSERVED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `2433c9caa3838ee4f32d31f3e1d1930c1b1b9add72883335c64928ba3e7d7b50` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`image-hough/raw-blank`, `image-hough/raw-cross`, `image-hough/raw-diagonal`, `image-hough/raw-noise-cross`, `image-hough/raw-odd-line`, `image-hough/synthetic-default`, `image-hough/synthetic-no-timing`, `image-hough/invalid-width`, `image-hough/invalid-height`, `image-hough/invalid-threshold`, `image-hough/invalid-lines`, `image-hough/invalid-canny`, `image-hough/truncated-raw`, `image-hough/help`, `image-hough/raw-option-low-vote-threshold`, `image-hough/raw-option-maximum-one-line`, `image-hough/raw-option-changed-canny-thresholds`, `image-hough/raw-option-combined-nondefault-timed`, `image-hough/raw-option-blank-low-threshold`, `image-hough/nineteen-runtime-contracts-and-independent-peaks`, `image-hough/foreign-device-empty-stream-rejection`, `image-hough/complete-native-PPM-and-declared-differences`, `image-hough/five-real-GPU-kernel-dispatches`, `image-hough/forty-five-child-cold-replay`, `image-hough/twenty-eight-qualification-and-archive-mutation-checks`, `image-hough/three-independent-fixed-source-reviews`。

实现方式：`DOCUMENTED_HOUGH_ACCUMULATOR_VARIANT`。

恢复/扩展条件：Canny/投票/峰/排序/布局或输入解析改变须重新资格与受影响入口回归。

CUDA 对照限制：当前5090原生与项目默认各10条线；部分rho偏1像素，red IoU0.23946。固定算法变体，不声称NPP逐位兼容。

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
python3 tools/moat/image_hough_options.py
python3 tools/moat/image_hough_runtime.py
python3 tools/moat/image_hough_trace.py
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
- [migration/reports/image-hough-options-contracts.json](../../../reports/image-hough-options-contracts.json)
- [migration/reports/image-hough-foreign-stream.json](../../../reports/image-hough-foreign-stream.json)
- [migration/reports/image-hough-cold.json](../../../reports/image-hough-cold.json)
- [migration/reports/image-hough-qualification-checks.json](../../../reports/image-hough-qualification-checks.json)
- [migration/reports/image-hough-qualification-check-contract-v2.json](../../../reports/image-hough-qualification-check-contract-v2.json)
- [migration/reports/image-hough-qualification-check-contract-v3.json](../../../reports/image-hough-qualification-check-contract-v3.json)
- [migration/reports/image-hough-qualification-check-contract-v4.json](../../../reports/image-hough-qualification-check-contract-v4.json)
- [migration/reports/image-hough-qualification-check-contract-v5.json](../../../reports/image-hough-qualification-check-contract-v5.json)
- [migration/reports/image-hough-qualification-check-contract-v6.json](../../../reports/image-hough-qualification-check-contract-v6.json)
- [migration/reports/image-hough-qualification-check-contract-v7.json](../../../reports/image-hough-qualification-check-contract-v7.json)
- [migration/reports/image-hough-review.json](../../../reports/image-hough-review.json)
- [migration/reports/image-hough-qualification.json](../../../reports/image-hough-qualification.json)
- [migration/reports/evidence/rewrite/I3/NPP_houghLines__houghLines.cpp/20261112T052835.898640Z-I3-composite-qualification-b4a1542b56](../../../reports/evidence/rewrite/I3/NPP_houghLines__houghLines.cpp/20261112T052835.898640Z-I3-composite-qualification-b4a1542b56)
- [migration/reports/evidence/rewrite/I3/Hough-Canny-GPU-and-complete-C__-build/20261112T043041.079819Z-I3-rocm-build-3164e51cae](../../../reports/evidence/rewrite/I3/Hough-Canny-GPU-and-complete-C__-build/20261112T043041.079819Z-I3-rocm-build-3164e51cae)
- [migration/reports/evidence/rewrite/I3/Hough-actual-device-allocation-and-stream-runtime/20261112T045917.456621Z-I3-rocm-runtime-f7e02f44f9](../../../reports/evidence/rewrite/I3/Hough-actual-device-allocation-and-stream-runtime/20261112T045917.456621Z-I3-rocm-runtime-f7e02f44f9)
- [migration/reports/evidence/rewrite/I3/Hough-actual-qualification-mutations/20261112T052522.441353Z-I3-CPU-validator-test-f935316728](../../../reports/evidence/rewrite/I3/Hough-actual-qualification-mutations/20261112T052522.441353Z-I3-CPU-validator-test-f935316728)
- [migration/reports/evidence/rewrite/I3/Hough-clean-fixed-checkout-all-CLI-CPU-runtime-trace/20261112T050047.079015Z-I3-host-cold-replay-6d00b5133f](../../../reports/evidence/rewrite/I3/Hough-clean-fixed-checkout-all-CLI-CPU-runtime-trace/20261112T050047.079015Z-I3-host-cold-replay-6d00b5133f)
- [migration/reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043345.473641Z-I3-rocm-original-35a534891d](../../../reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043345.473641Z-I3-rocm-original-35a534891d)
- [migration/reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043347.931133Z-I3-rocm-original-1e41c3fe88](../../../reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043347.931133Z-I3-rocm-original-1e41c3fe88)
- [migration/reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043350.176580Z-I3-rocm-original-e8379bf4e0](../../../reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043350.176580Z-I3-rocm-original-e8379bf4e0)
- [migration/reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043352.305562Z-I3-rocm-original-5b4fd2eca2](../../../reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043352.305562Z-I3-rocm-original-5b4fd2eca2)
- [migration/reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043354.414880Z-I3-rocm-original-551a399ad9](../../../reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043354.414880Z-I3-rocm-original-551a399ad9)
- [migration/reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043356.519374Z-I3-rocm-original-47557abfc6](../../../reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043356.519374Z-I3-rocm-original-47557abfc6)
- [migration/reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043358.691863Z-I3-rocm-original-e2b39c23cd](../../../reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043358.691863Z-I3-rocm-original-e2b39c23cd)
- [migration/reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043400.825703Z-I3-rocm-original-64dc383bdb](../../../reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043400.825703Z-I3-rocm-original-64dc383bdb)
- [migration/reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043402.754024Z-I3-rocm-original-823f07da57](../../../reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043402.754024Z-I3-rocm-original-823f07da57)
- [migration/reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043404.682017Z-I3-rocm-original-acb82d76f1](../../../reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043404.682017Z-I3-rocm-original-acb82d76f1)
- [migration/reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043406.613844Z-I3-rocm-original-7f77efb47f](../../../reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043406.613844Z-I3-rocm-original-7f77efb47f)
- [migration/reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043408.537883Z-I3-rocm-original-dd5ed17bfd](../../../reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043408.537883Z-I3-rocm-original-dd5ed17bfd)
- [migration/reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043410.461625Z-I3-rocm-original-127015a156](../../../reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043410.461625Z-I3-rocm-original-127015a156)
- [migration/reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043412.347524Z-I3-rocm-original-6a185d6f92](../../../reports/evidence/rewrite/I3/Hough-complete-C__-original-CLI/20261112T043412.347524Z-I3-rocm-original-6a185d6f92)
- [migration/reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044437.739554Z-I3-CPU-reference-6416bbd511](../../../reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044437.739554Z-I3-CPU-reference-6416bbd511)
- [migration/reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044439.106208Z-I3-CPU-reference-755254c51e](../../../reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044439.106208Z-I3-CPU-reference-755254c51e)
- [migration/reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044440.451040Z-I3-CPU-reference-03ced5580b](../../../reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044440.451040Z-I3-CPU-reference-03ced5580b)
- [migration/reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044441.800418Z-I3-CPU-reference-8d4c76adf3](../../../reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044441.800418Z-I3-CPU-reference-8d4c76adf3)
- [migration/reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044443.146330Z-I3-CPU-reference-68900293c4](../../../reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044443.146330Z-I3-CPU-reference-68900293c4)
- [migration/reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044444.467117Z-I3-CPU-reference-63d94fc0c0](../../../reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044444.467117Z-I3-CPU-reference-63d94fc0c0)
- [migration/reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044446.036423Z-I3-CPU-reference-e9f1e08d78](../../../reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044446.036423Z-I3-CPU-reference-e9f1e08d78)
- [migration/reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044447.604987Z-I3-CPU-reference-b589d40862](../../../reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044447.604987Z-I3-CPU-reference-b589d40862)
- [migration/reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044448.870117Z-I3-CPU-reference-85e1684d80](../../../reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044448.870117Z-I3-CPU-reference-85e1684d80)
- [migration/reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044450.147643Z-I3-CPU-reference-2ee9fdf569](../../../reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044450.147643Z-I3-CPU-reference-2ee9fdf569)
- [migration/reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044451.401384Z-I3-CPU-reference-c230731223](../../../reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044451.401384Z-I3-CPU-reference-c230731223)
- [migration/reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044452.685390Z-I3-CPU-reference-d031bb4c03](../../../reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044452.685390Z-I3-CPU-reference-d031bb4c03)
- [migration/reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044453.957915Z-I3-CPU-reference-e32647904e](../../../reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044453.957915Z-I3-CPU-reference-e32647904e)
- [migration/reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044455.241098Z-I3-CPU-reference-87396c24ee](../../../reports/evidence/rewrite/I3/Hough-complete-image-and-line-independent-CPU/20261112T044455.241098Z-I3-CPU-reference-87396c24ee)
- [migration/reports/evidence/rewrite/I3/Hough-complete-native-CUDA-project-HIP-CPU-comparison/20261112T044516.922448Z-I3-CPU-reference-99bff1e3cc](../../../reports/evidence/rewrite/I3/Hough-complete-native-CUDA-project-HIP-CPU-comparison/20261112T044516.922448Z-I3-CPU-reference-99bff1e3cc)
- [migration/reports/evidence/rewrite/I3/Hough-foreign-device-empty-stream-rejection/20261112T044214.998119Z-I3-rocm-runtime-75d3d45122](../../../reports/evidence/rewrite/I3/Hough-foreign-device-empty-stream-rejection/20261112T044214.998119Z-I3-rocm-runtime-75d3d45122)
- [migration/reports/evidence/rewrite/I3/Hough-full-entry-contract/20261112T035751.350843Z-I3-CPU-contract-6d4bb737da](../../../reports/evidence/rewrite/I3/Hough-full-entry-contract/20261112T035751.350843Z-I3-CPU-contract-6d4bb737da)
- [migration/reports/evidence/rewrite/I3/Hough-full-synthetic-real-GPU-Canny-votes-peaks-trace/20261112T043457.432843Z-I3-rocm-trace-6e89f2b97a](../../../reports/evidence/rewrite/I3/Hough-full-synthetic-real-GPU-Canny-votes-peaks-trace/20261112T043457.432843Z-I3-rocm-trace-6e89f2b97a)
- [migration/reports/evidence/rewrite/I3/Hough-runtime-independent-CPU-all-peaks/20261112T045925.314369Z-I3-CPU-reference-88840adc63](../../../reports/evidence/rewrite/I3/Hough-runtime-independent-CPU-all-peaks/20261112T045925.314369Z-I3-CPU-reference-88840adc63)
- [migration/reports/evidence/rewrite/I3/Hough-valid-nondefault-options-contract/20261112T043037.329027Z-I3-CPU-contract-465a96d913](../../../reports/evidence/rewrite/I3/Hough-valid-nondefault-options-contract/20261112T043037.329027Z-I3-CPU-contract-465a96d913)
- [migration/reports/evidence/rewrite/I3/Hough-valid-nondefault-original-options/20261112T044458.951397Z-I3-rocm-original-50779738e1](../../../reports/evidence/rewrite/I3/Hough-valid-nondefault-original-options/20261112T044458.951397Z-I3-rocm-original-50779738e1)
- [migration/reports/evidence/rewrite/I3/Hough-valid-nondefault-original-options/20261112T044502.732842Z-I3-rocm-original-83c5e9568e](../../../reports/evidence/rewrite/I3/Hough-valid-nondefault-original-options/20261112T044502.732842Z-I3-rocm-original-83c5e9568e)
- [migration/reports/evidence/rewrite/I3/Hough-valid-nondefault-original-options/20261112T044506.200558Z-I3-rocm-original-55f20154be](../../../reports/evidence/rewrite/I3/Hough-valid-nondefault-original-options/20261112T044506.200558Z-I3-rocm-original-55f20154be)
- [migration/reports/evidence/rewrite/I3/Hough-valid-nondefault-original-options/20261112T044509.645953Z-I3-rocm-original-394e6582c6](../../../reports/evidence/rewrite/I3/Hough-valid-nondefault-original-options/20261112T044509.645953Z-I3-rocm-original-394e6582c6)
- [migration/reports/evidence/rewrite/I3/Hough-valid-nondefault-original-options/20261112T044513.080972Z-I3-rocm-original-9385bab3d1](../../../reports/evidence/rewrite/I3/Hough-valid-nondefault-original-options/20261112T044513.080972Z-I3-rocm-original-9385bab3d1)
- [migration/reports/evidence/rewrite/I3/Hough-valid-options-independent-CPU/20261112T044501.153653Z-I3-CPU-reference-6192248c9a](../../../reports/evidence/rewrite/I3/Hough-valid-options-independent-CPU/20261112T044501.153653Z-I3-CPU-reference-6192248c9a)
- [migration/reports/evidence/rewrite/I3/Hough-valid-options-independent-CPU/20261112T044504.603704Z-I3-CPU-reference-ff2c308ca8](../../../reports/evidence/rewrite/I3/Hough-valid-options-independent-CPU/20261112T044504.603704Z-I3-CPU-reference-ff2c308ca8)
- [migration/reports/evidence/rewrite/I3/Hough-valid-options-independent-CPU/20261112T044508.067048Z-I3-CPU-reference-267a6ccfd5](../../../reports/evidence/rewrite/I3/Hough-valid-options-independent-CPU/20261112T044508.067048Z-I3-CPU-reference-267a6ccfd5)
- [migration/reports/evidence/rewrite/I3/Hough-valid-options-independent-CPU/20261112T044511.495586Z-I3-CPU-reference-7c7cd1717d](../../../reports/evidence/rewrite/I3/Hough-valid-options-independent-CPU/20261112T044511.495586Z-I3-CPU-reference-7c7cd1717d)
- [migration/reports/evidence/rewrite/I3/Hough-valid-options-independent-CPU/20261112T044514.912362Z-I3-CPU-reference-4e20cef9a7](../../../reports/evidence/rewrite/I3/Hough-valid-options-independent-CPU/20261112T044514.912362Z-I3-CPU-reference-4e20cef9a7)
- [migration/reports/evidence/rewrite/I3/NPP__houghLines_houghLines.cpp/20261111T181159.322261Z-I3-cuda-original-6e3b3023be](../../../reports/evidence/rewrite/I3/NPP__houghLines_houghLines.cpp/20261111T181159.322261Z-I3-cuda-original-6e3b3023be)
