# NPP+/floodFill::floodFillVariousRegionTypesNPPPlus.cpp

**PASSED / L4**

完整五模式/两原图/五RGB产品C++入口；29全量输入、4流程20RGB、72运行合同、18CLI、60基础验收器与16资格门反例、真实GPU trace、36子记录冷检出及独立复审通过。项目固定seed八连通/内边界与原生NPP+的分区和元数据差异单列；项目GPU对独立CPU逐字节精确。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp](../../../../NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp) |
| 实际库 / 后端 | Project HIP fixed-seed RGB flood fill and shared GPU connectivity / project HIP image flood fill |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp](../../../../rocm/ported/NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp) |
| required cases | 39/39 |
| CUDA baseline / comparison | PASSED / OBSERVED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `b607b3cc985c64e4504fa62a9e08f0fd296821737726f87d90d74653c683eb5c` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`image-flood/exact-original`, `image-flood/gradient-original`, `image-flood/gradient-boundary-original`, `image-flood/range-original`, `image-flood/range-boundary-original`, `image-flood/constant-all-region`, `image-flood/equal-region-with-hole`, `image-flood/hole-boundary`, `image-flood/diagonal-eight-connectivity`, `image-flood/fixed-gradient-independent-ramp`, `image-flood/fixed-gradient-boundary-independent-ramp`, `image-flood/range-independent-noise-771183`, `image-flood/range-boundary-independent-noise-771183`, `image-flood/seed-outside-absolute-range`, `image-flood/gradient-upper-saturation`, `image-flood/gradient-lower-saturation`, `image-flood/one-pixel`, `image-flood/single-row`, `image-flood/single-column`, `image-flood/fill-color-already-present-mode0`, `image-flood/fill-color-already-present-mode2`, `image-flood/fill-color-already-present-mode4`, `image-flood/changed-full-original-mode0`, `image-flood/changed-full-original-mode1`, `image-flood/changed-full-original-mode2`, `image-flood/changed-full-original-mode3`, `image-flood/changed-full-original-mode4`, `image-flood/large-irregular-structured-range`, `image-flood/inclusive-fixed-gradient-limits`, `image-flood/four-original-workflows-twenty-RGB-products`, `image-flood/seventy-two-runtime-memory-and-stream-cases`, `image-flood/eighteen-CLI-and-error-cases`, `image-flood/full-real-GPU-trace`, `image-flood/independent-CPU-and-native-comparison`, `image-flood/sixty-acceptance-reader-checks`, `image-flood/sixteen-archive-provenance-and-publication-reader-checks`, `image-flood/exact-padding-counterexample-fixed`, `image-flood/thirty-six-child-cold-checkout`, `image-flood/independent-review`。

实现方式：`ALGORITHM_VARIANT_EXACT_PROJECT_FIXED_SEED_8_CONNECTED`。

恢复/扩展条件：修改连接、边界、输入布局、元数据或接口须重签合同与复验。

CUDA 对照限制：五原始产品与当前NPP+逐像素/region字段差异完整记录；不声称vendor逐字节一致。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp:42:10: fatal error: 'nppPlus/nppPlus.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_samp

尝试库：—；实现 hash：`fe19a590d9e1099b485cd5682c436a0b2071117ffebe99962e7623587bc80f8e`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python3 tools/moat/image_flood_contracts.py
python3 tools/moat/image_flood_build.py
python3 tools/moat/image_flood_run.py
python3 tools/moat/image_flood_frontend_build.py
python3 tools/moat/image_flood_originals.py
python3 tools/moat/image_flood_runtime.py
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/evidence/20261110T051547.561861Z/batches12_15-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261110T051547.561861Z/batches12_15-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/batches12_15-validation.json](../../../reports/batches12_15-validation.json)
- [migration/reports/evidence/20261110T051436.908488Z/batches12_15-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261110T051436.908488Z/batches12_15-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/evidence/20261110T053436.400711Z/batches12_15-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261110T053436.400711Z/batches12_15-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/evidence/20261110T053230.152526Z/batches12_15-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261110T053230.152526Z/batches12_15-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/image-flood.md](../../../reports/image-flood.md)
- [migration/reports/evidence/rewrite/I3/NPP__floodFill__floodFillVariousRegionTypesNPPPlus.cpp/20261112T035123.857880Z-I3-composite-qualification-0c2958e5dc](../../../reports/evidence/rewrite/I3/NPP__floodFill__floodFillVariousRegionTypesNPPPlus.cpp/20261112T035123.857880Z-I3-composite-qualification-0c2958e5dc)
- [migration/reports/evidence/rewrite/I3/FloodFill-all29-real-device-dispatch-trace/20261112T032830.020403Z-I3-rocm-trace-fb0791eb96](../../../reports/evidence/rewrite/I3/FloodFill-all29-real-device-dispatch-trace/20261112T032830.020403Z-I3-rocm-trace-fb0791eb96)
- [migration/reports/evidence/rewrite/I3/FloodFill-clean-checkout-complete-RGB-runtime-CLI-trace/20261112T032927.151752Z-I3-host-cold-replay-f21d7ab95b](../../../reports/evidence/rewrite/I3/FloodFill-clean-checkout-complete-RGB-runtime-CLI-trace/20261112T032927.151752Z-I3-host-cold-replay-f21d7ab95b)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-CLI-independent-CPU/20261112T032826.087556Z-I3-CPU-reference-92ef892b1b](../../../reports/evidence/rewrite/I3/FloodFill-complete-CLI-independent-CPU/20261112T032826.087556Z-I3-CPU-reference-92ef892b1b)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032750.012706Z-I3-rocm-CLI-aae5d70103](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032750.012706Z-I3-rocm-CLI-aae5d70103)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032752.147310Z-I3-rocm-CLI-1cfd70eac6](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032752.147310Z-I3-rocm-CLI-1cfd70eac6)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032754.082582Z-I3-rocm-CLI-281676d4ee](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032754.082582Z-I3-rocm-CLI-281676d4ee)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032756.015191Z-I3-rocm-CLI-e1d537eff3](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032756.015191Z-I3-rocm-CLI-e1d537eff3)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032757.927552Z-I3-rocm-CLI-0a3946b178](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032757.927552Z-I3-rocm-CLI-0a3946b178)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032759.825297Z-I3-rocm-CLI-2b520d2a8a](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032759.825297Z-I3-rocm-CLI-2b520d2a8a)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032801.740692Z-I3-rocm-CLI-f4307cd039](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032801.740692Z-I3-rocm-CLI-f4307cd039)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032803.655655Z-I3-rocm-CLI-b756460f19](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032803.655655Z-I3-rocm-CLI-b756460f19)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032805.519925Z-I3-rocm-CLI-fd440f6696](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032805.519925Z-I3-rocm-CLI-fd440f6696)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032807.417953Z-I3-rocm-CLI-cbd9d0466b](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032807.417953Z-I3-rocm-CLI-cbd9d0466b)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032809.346489Z-I3-rocm-CLI-267ecfdea0](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032809.346489Z-I3-rocm-CLI-267ecfdea0)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032811.244987Z-I3-rocm-CLI-963ea92be5](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032811.244987Z-I3-rocm-CLI-963ea92be5)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032813.125158Z-I3-rocm-CLI-8fac2cf5e5](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032813.125158Z-I3-rocm-CLI-8fac2cf5e5)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032815.027020Z-I3-rocm-CLI-716d3d2740](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032815.027020Z-I3-rocm-CLI-716d3d2740)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032816.918888Z-I3-rocm-CLI-280adc0af4](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032816.918888Z-I3-rocm-CLI-280adc0af4)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032818.877008Z-I3-rocm-CLI-b3023d7699](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032818.877008Z-I3-rocm-CLI-b3023d7699)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032820.857701Z-I3-rocm-CLI-ef288189c6](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032820.857701Z-I3-rocm-CLI-ef288189c6)
- [migration/reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032822.757939Z-I3-rocm-CLI-cc307c7000](../../../reports/evidence/rewrite/I3/FloodFill-complete-original-CLI/20261112T032822.757939Z-I3-rocm-CLI-cc307c7000)
- [migration/reports/evidence/rewrite/I3/FloodFill-five-mode-original-file-workflow-contracts/20261111T182147.977319Z-I3-CPU-contract-04a6b2abbc](../../../reports/evidence/rewrite/I3/FloodFill-five-mode-original-file-workflow-contracts/20261111T182147.977319Z-I3-CPU-contract-04a6b2abbc)
- [migration/reports/evidence/rewrite/I3/FloodFill-fixed-complete-runtime-arguments-alias-streams/20261111T184741.537835Z-I3-rocm-runtime-c6825b3a19](../../../reports/evidence/rewrite/I3/FloodFill-fixed-complete-runtime-arguments-alias-streams/20261111T184741.537835Z-I3-rocm-runtime-c6825b3a19)
- [migration/reports/evidence/rewrite/I3/FloodFill-fixed-exact-last-row-padding-counterexample/20261111T185159.117890Z-I3-rocm-contract-probe-354c9ab01a](../../../reports/evidence/rewrite/I3/FloodFill-fixed-exact-last-row-padding-counterexample/20261111T185159.117890Z-I3-rocm-contract-probe-354c9ab01a)
- [migration/reports/evidence/rewrite/I3/FloodFill-fixed-runtime-storage-and-stream-obligations/20261111T184701.926333Z-I3-CPU-contract-d8cd1bf154](../../../reports/evidence/rewrite/I3/FloodFill-fixed-runtime-storage-and-stream-obligations/20261111T184701.926333Z-I3-CPU-contract-d8cd1bf154)
- [migration/reports/evidence/rewrite/I3/FloodFill-four-complete-originals-independent-CPU/20261111T184737.035874Z-I3-CPU-reference-d493dfe224](../../../reports/evidence/rewrite/I3/FloodFill-four-complete-originals-independent-CPU/20261111T184737.035874Z-I3-CPU-reference-d493dfe224)
- [migration/reports/evidence/rewrite/I3/FloodFill-frozen-complete-RGB-and-boundary-contracts/20261111T181141.472226Z-I3-CPU-contract-06f2821c15](../../../reports/evidence/rewrite/I3/FloodFill-frozen-complete-RGB-and-boundary-contracts/20261111T181141.472226Z-I3-CPU-contract-06f2821c15)
- [migration/reports/evidence/rewrite/I3/FloodFill-full-RGB-GPU-backend-build/20261111T184705.604796Z-I3-rocm-build-8994ea81f0](../../../reports/evidence/rewrite/I3/FloodFill-full-RGB-GPU-backend-build/20261111T184705.604796Z-I3-rocm-build-8994ea81f0)
- [migration/reports/evidence/rewrite/I3/FloodFill-full-five-workflow-C__-build/20261111T184721.211118Z-I3-rocm-build-255448be41](../../../reports/evidence/rewrite/I3/FloodFill-full-five-workflow-C__-build/20261111T184721.211118Z-I3-rocm-build-255448be41)
- [migration/reports/evidence/rewrite/I3/FloodFill-full-native-CPU-HIP-and-metadata-comparison/20261112T032629.115960Z-I3-CPU-reference-67e9160223](../../../reports/evidence/rewrite/I3/FloodFill-full-native-CPU-HIP-and-metadata-comparison/20261112T032629.115960Z-I3-CPU-reference-67e9160223)
- [migration/reports/evidence/rewrite/I3/FloodFill-full-runtime-storage-and-stream-independent-CPU/20261111T184748.494425Z-I3-CPU-reference-b4160111f6](../../../reports/evidence/rewrite/I3/FloodFill-full-runtime-storage-and-stream-independent-CPU/20261111T184748.494425Z-I3-CPU-reference-b4160111f6)
- [migration/reports/evidence/rewrite/I3/FloodFill-independent-complete-RGB-CPU/20261111T184716.905244Z-I3-CPU-reference-453b5eda43](../../../reports/evidence/rewrite/I3/FloodFill-independent-complete-RGB-CPU/20261111T184716.905244Z-I3-CPU-reference-453b5eda43)
- [migration/reports/evidence/rewrite/I3/FloodFill-original-CLI-and-malformed-file-contracts/20261112T032745.159503Z-I3-CPU-contract-e4008fb9dc](../../../reports/evidence/rewrite/I3/FloodFill-original-CLI-and-malformed-file-contracts/20261112T032745.159503Z-I3-CPU-contract-e4008fb9dc)
- [migration/reports/evidence/rewrite/I3/FloodFill-qualification-and-cold-archive-validator-checks/20261112T034743.636243Z-I3-CPU-validator-test-3b569ed53c](../../../reports/evidence/rewrite/I3/FloodFill-qualification-and-cold-archive-validator-checks/20261112T034743.636243Z-I3-CPU-validator-test-3b569ed53c)
- [migration/reports/evidence/rewrite/I3/FloodFill-real-core-validator-mutations/20261111T184924.859738Z-I3-CPU-validator-test-3ff03081b8](../../../reports/evidence/rewrite/I3/FloodFill-real-core-validator-mutations/20261111T184924.859738Z-I3-CPU-validator-test-3ff03081b8)
- [migration/reports/evidence/rewrite/I3/FloodFill-real-dispatch-and-full-pixels-independent-CPU/20261112T032834.886182Z-I3-CPU-reference-f616f52b6d](../../../reports/evidence/rewrite/I3/FloodFill-real-dispatch-and-full-pixels-independent-CPU/20261112T032834.886182Z-I3-CPU-reference-f616f52b6d)
- [migration/reports/evidence/rewrite/I3/FloodFill-runtime-CLI-original-validator-mutations/20261112T032836.801106Z-I3-CPU-validator-test-553bdb52e0](../../../reports/evidence/rewrite/I3/FloodFill-runtime-CLI-original-validator-mutations/20261112T032836.801106Z-I3-CPU-validator-test-553bdb52e0)
- [migration/reports/evidence/rewrite/I3/FloodFill-twenty-nine-complete-RGB-inputs/20261111T184712.446213Z-I3-rocm-prototype-ce1da57cfa](../../../reports/evidence/rewrite/I3/FloodFill-twenty-nine-complete-RGB-inputs/20261111T184712.446213Z-I3-rocm-prototype-ce1da57cfa)
- [migration/reports/evidence/rewrite/I3/NPP___floodFill_floodFillVariousRegionTypesNPPPlus.cpp/20261111T181153.969229Z-I3-cuda-original-820d020ffa](../../../reports/evidence/rewrite/I3/NPP___floodFill_floodFillVariousRegionTypesNPPPlus.cpp/20261111T181153.969229Z-I3-cuda-original-820d020ffa)
- [migration/reports/evidence/rewrite/I3/NPP__floodFill__floodFillVariousRegionTypesNPPPlus.cpp/20261111T184727.534283Z-I3-rocm-original-58aa02544e](../../../reports/evidence/rewrite/I3/NPP__floodFill__floodFillVariousRegionTypesNPPPlus.cpp/20261111T184727.534283Z-I3-rocm-original-58aa02544e)
- [migration/reports/evidence/rewrite/I3/NPP__floodFill__floodFillVariousRegionTypesNPPPlus.cpp/20261111T184730.028521Z-I3-rocm-original-38b49ab979](../../../reports/evidence/rewrite/I3/NPP__floodFill__floodFillVariousRegionTypesNPPPlus.cpp/20261111T184730.028521Z-I3-rocm-original-38b49ab979)
- [migration/reports/evidence/rewrite/I3/NPP__floodFill__floodFillVariousRegionTypesNPPPlus.cpp/20261111T184732.267138Z-I3-rocm-original-e043d81120](../../../reports/evidence/rewrite/I3/NPP__floodFill__floodFillVariousRegionTypesNPPPlus.cpp/20261111T184732.267138Z-I3-rocm-original-e043d81120)
- [migration/reports/evidence/rewrite/I3/NPP__floodFill__floodFillVariousRegionTypesNPPPlus.cpp/20261111T184734.468761Z-I3-rocm-original-2be8922773](../../../reports/evidence/rewrite/I3/NPP__floodFill__floodFillVariousRegionTypesNPPPlus.cpp/20261111T184734.468761Z-I3-rocm-original-2be8922773)
- [migration/reports/evidence/rewrite/I3/FloodFill-full-RGB-GPU-backend-build/20261111T181533.727560Z-I3-rocm-build-895672330e](../../../reports/evidence/rewrite/I3/FloodFill-full-RGB-GPU-backend-build/20261111T181533.727560Z-I3-rocm-build-895672330e)
- [migration/reports/evidence/rewrite/I3/FloodFill-legacy-last-row-padding-actual-counterexample/20261111T184511.535189Z-I3-rocm-contract-probe-d3ff42ca14](../../../reports/evidence/rewrite/I3/FloodFill-legacy-last-row-padding-actual-counterexample/20261111T184511.535189Z-I3-rocm-contract-probe-d3ff42ca14)
