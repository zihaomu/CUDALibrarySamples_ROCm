# NPP/opencvBenchmark::opencvBenchmark.cpp

**PASSED / L4**

完整四算子C++原例、6 CLI、独立CPU全量产品/四行OpenCV统计、5090原生同输入与同构建OpenCV对照、18设备合同、真实GPU trace、35项反例及19子证据固定提交冷检出、三份独立复审通过。Gaussian/Canny为明确项目算法变体；NPP原生未输出像素，不宣称NPP逐像素等价；计时仅观察。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP/opencvBenchmark/opencvBenchmark.cpp](../../../../NPP/opencvBenchmark/opencvBenchmark.cpp) |
| 实际库 / 后端 | Project HIP Gaussian/Canny/resize/RGB gray plus pinned OpenCV 4.12 CPU benchmark / project HIP image benchmark |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP/opencvBenchmark/opencvBenchmark.cpp](../../../../rocm/ported/NPP/opencvBenchmark/opencvBenchmark.cpp) |
| required cases | 14/14 |
| CUDA baseline / comparison | PASSED / OBSERVED |
| 性能 | OBSERVED_NOT_QUALIFIED |
| 原始源码 SHA256 | `0332d73b327bbf76726b6eb13e38bbf68110baff7f923f328dbaabbca54fb30e` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`image-benchmark/small`, `image-benchmark/odd-half`, `image-benchmark/original-default`, `image-benchmark/invalid-dimensions`, `image-benchmark/missing-input`, `image-benchmark/unknown-option`, `image-benchmark/matched-OpenCV4.12-and-four-HIP-build`, `image-benchmark/all-four-independent-CPU-and-printed-metrics`, `image-benchmark/original-5090-and-algorithm-variants`, `image-benchmark/eighteen-device-contracts`, `image-benchmark/real-four-operation-trace`, `image-benchmark/thirty-five-reader-counterexamples`, `image-benchmark/nineteen-child-fixed-commit-cold-replay`, `image-benchmark/three-independent-reviews`。

实现方式：`DOCUMENTED_IMAGE_ALGORITHM_VARIANTS`。

恢复/扩展条件：四算子数学政策、共享HIP核、CPU oracle、OpenCV版本/动态库、CLI或实验门改变需重新资格。

CUDA 对照限制：5090原生与ROCm同输入/4096×2048/20×5/OpenCV4.12。NPP不输出产品像素；Gaussian原生vsOpenCV均差1.70、项目0.00（原始尺寸），Canny计数同546308但掩码不保证相同。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/opencvBenchmark/opencvBenchmark.cpp:34:10: fatal error: 'npp.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALib

尝试库：—；实现 hash：`b13ac23af0be4505194eacf6a2e4d3d4511cdfdc5726de2f4a2663fc8222c45e`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python3 tools/moat/image_benchmark_contracts.py
python3 tools/moat/image_benchmark_deps.py
python3 tools/moat/image_benchmark_build.py
python3 tools/moat/image_benchmark_run.py
build/image-cpu-venv/bin/python tools/moat/image_benchmark_reference.py
python3 tools/moat/image_benchmark_native_comparison.py
python3 tools/moat/image_benchmark_runtime.py
python3 tools/moat/image_benchmark_trace.py
python3 tools/moat/image_benchmark_cold.py
python3 tools/moat/qualify_image_benchmark.py
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/NPP_opencvBenchmark_opencvBenchmark.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/NPP_opencvBenchmark_opencvBenchmark.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP_opencvBenchmark_opencvBenchmark.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/NPP_opencvBenchmark_opencvBenchmark.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP_opencvBenchmark_opencvBenchmark.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/NPP_opencvBenchmark_opencvBenchmark.cpp)
- [migration/reports/image-benchmark.md](../../../reports/image-benchmark.md)
- [migration/reports/image-benchmark-contracts.json](../../../reports/image-benchmark-contracts.json)
- [migration/reports/image-I3-rocm-OpenCV.json](../../../reports/image-I3-rocm-OpenCV.json)
- [migration/reports/image-benchmark-build.json](../../../reports/image-benchmark-build.json)
- [migration/reports/image-benchmark-runs.json](../../../reports/image-benchmark-runs.json)
- [migration/reports/image-benchmark-validation.json](../../../reports/image-benchmark-validation.json)
- [migration/reports/image-benchmark-native-comparison.json](../../../reports/image-benchmark-native-comparison.json)
- [migration/reports/image-benchmark-runtime.json](../../../reports/image-benchmark-runtime.json)
- [migration/reports/image-benchmark-trace.json](../../../reports/image-benchmark-trace.json)
- [migration/reports/image-benchmark-negative.json](../../../reports/image-benchmark-negative.json)
- [migration/reports/image-benchmark-cold.json](../../../reports/image-benchmark-cold.json)
- [migration/reports/evidence/rewrite/I3/NPP_opencvBenchmark__opencvBenchmark.cpp/20261112T074053.375259Z-I3-composite-qualification-ad2742c777](../../../reports/evidence/rewrite/I3/NPP_opencvBenchmark__opencvBenchmark.cpp/20261112T074053.375259Z-I3-composite-qualification-ad2742c777)
- [migration/reports/evidence/rewrite/I3/NPP-opencvBenchmark-full-native-default/20261111T182242.064805Z-I3-cuda-original-a496dad9bb](../../../reports/evidence/rewrite/I3/NPP-opencvBenchmark-full-native-default/20261111T182242.064805Z-I3-cuda-original-a496dad9bb)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-all-four-actual-GPU-kernel-traces/20261112T061221.830455Z-I3-rocm-trace-1a89755682](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-all-four-actual-GPU-kernel-traces/20261112T061221.830455Z-I3-rocm-trace-1a89755682)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-complete-original-CLI/20261112T061117.241930Z-I3-rocm-original-80f5434d27](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-complete-original-CLI/20261112T061117.241930Z-I3-rocm-original-80f5434d27)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-complete-original-CLI/20261112T061120.055544Z-I3-rocm-original-ded2a762ad](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-complete-original-CLI/20261112T061120.055544Z-I3-rocm-original-ded2a762ad)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-complete-original-CLI/20261112T061122.474001Z-I3-rocm-original-a3458ca46b](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-complete-original-CLI/20261112T061122.474001Z-I3-rocm-original-a3458ca46b)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-complete-original-CLI/20261112T061127.645369Z-I3-rocm-original-48b36e7151](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-complete-original-CLI/20261112T061127.645369Z-I3-rocm-original-48b36e7151)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-complete-original-CLI/20261112T061129.639226Z-I3-rocm-original-e94347a94e](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-complete-original-CLI/20261112T061129.639226Z-I3-rocm-original-e94347a94e)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-complete-original-CLI/20261112T061131.639388Z-I3-rocm-original-87f7d1be6b](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-complete-original-CLI/20261112T061131.639388Z-I3-rocm-original-87f7d1be6b)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-fixed-Git-cold-four-operations-and-CPU/20261112T073608.903658Z-I3-host-cold-replay-947f7840c5](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-fixed-Git-cold-four-operations-and-CPU/20261112T073608.903658Z-I3-host-cold-replay-947f7840c5)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-four-HIP-operations-and-original-C__-CLI-build/20261112T061100.216767Z-I3-rocm-build-1f299febbf](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-four-HIP-operations-and-original-C__-CLI-build/20261112T061100.216767Z-I3-rocm-build-1f299febbf)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-independent-four-operation-CPU/20261112T061142.072482Z-I3-CPU-reference-42a5fa4b43](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-independent-four-operation-CPU/20261112T061142.072482Z-I3-CPU-reference-42a5fa4b43)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-independent-four-operation-CPU/20261112T061143.419217Z-I3-CPU-reference-35f91a2a0a](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-independent-four-operation-CPU/20261112T061143.419217Z-I3-CPU-reference-35f91a2a0a)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-independent-four-operation-CPU/20261112T061144.753101Z-I3-CPU-reference-3b52d898dc](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-independent-four-operation-CPU/20261112T061144.753101Z-I3-CPU-reference-3b52d898dc)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-independent-four-operation-CPU/20261112T061147.857851Z-I3-CPU-reference-4164617835](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-independent-four-operation-CPU/20261112T061147.857851Z-I3-CPU-reference-4164617835)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-independent-four-operation-CPU/20261112T061149.193614Z-I3-CPU-reference-b186686eab](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-independent-four-operation-CPU/20261112T061149.193614Z-I3-CPU-reference-b186686eab)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-independent-four-operation-CPU/20261112T061150.560065Z-I3-CPU-reference-9635b29507](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-independent-four-operation-CPU/20261112T061150.560065Z-I3-CPU-reference-9635b29507)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-original-CLI-contract/20261112T060923.250526Z-I3-CPU-contract-7eb6a4ae0d](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-original-CLI-contract/20261112T060923.250526Z-I3-CPU-contract-7eb6a4ae0d)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-original-CUDA-and-HIP-sealed-semantics/20261112T061704.756281Z-I3-CPU-comparison-0fbcaea16c](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-original-CUDA-and-HIP-sealed-semantics/20261112T061704.756281Z-I3-CPU-comparison-0fbcaea16c)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-sealed-reader-counterexamples/20261112T073237.928177Z-I3-CPU-negative-5b56d4c016](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-sealed-reader-counterexamples/20261112T073237.928177Z-I3-CPU-negative-5b56d4c016)
- [migration/reports/evidence/rewrite/I3/OpenCV-benchmark-three-kernel-device-and-stream-contracts/20261112T061210.603243Z-I3-rocm-runtime-25f70fa5b7](../../../reports/evidence/rewrite/I3/OpenCV-benchmark-three-kernel-device-and-stream-contracts/20261112T061210.603243Z-I3-rocm-runtime-25f70fa5b7)
- [migration/reports/evidence/rewrite/I3/OpenCV-private-native-core-imgproc-dependency/20261111T182002.363914Z-I3-CPU-native-setup-d6a8d00729](../../../reports/evidence/rewrite/I3/OpenCV-private-native-core-imgproc-dependency/20261111T182002.363914Z-I3-CPU-native-setup-d6a8d00729)
- [migration/reports/evidence/rewrite/I3/benchmark-matched-private-OpenCV-4.12/20261112T060931.475676Z-I3-rocm-setup-9380f08fd5](../../../reports/evidence/rewrite/I3/benchmark-matched-private-OpenCV-4.12/20261112T060931.475676Z-I3-rocm-setup-9380f08fd5)
