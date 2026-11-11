# NPP+/distanceTransform::unsignedAndSignedDistanceTransformNPPPlus.cpp

**PASSED / L4**

完整五图/12RAW C++入口，30全量输入，4流程48RAW，69参数、27状态/极值、19CLI、100CPU模型、57验收器检查及trace/12子记录冷检出/三复审通过。Signed使用预固定的线性阈值交点site距离与独立CPU定义；和NPP+闭源算法/锚点规则的差异完整单列，不承诺逐位vendor一致。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP+/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp](../../../../NPP+/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp) |
| 实际库 / 后端 | Project HIP exact unsigned EDT + compact threshold-crossing signed site set + GPU FP64 search, deterministic Voronoi and visualization / project HIP distance transform |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP+/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp](../../../../rocm/ported/NPP+/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp) |
| required cases | 40/40 |
| CUDA baseline / comparison | PASSED / OBSERVED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `637c42cdf9426fa8c3967d738e011c1b7689e9fecc87e9b327c5643bcc1ac7e8` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`image-distance/unsigned-original`, `image-distance/unsigned-original-inverted`, `image-distance/signed-circle-original`, `image-distance/signed-circle-original-inverted`, `image-distance/signed-lith-original`, `image-distance/unsigned-one-site`, `image-distance/unsigned-symmetric-ties`, `image-distance/unsigned-all-zero`, `image-distance/unsigned-no-site`, `image-distance/unsigned-single-row`, `image-distance/unsigned-single-column`, `image-distance/unsigned-independent-noise-773711`, `image-distance/signed-constant-negative`, `image-distance/signed-one-pixel-negative`, `image-distance/signed-constant-positive`, `image-distance/signed-one-pixel-positive`, `image-distance/signed-constant-zero`, `image-distance/signed-one-pixel-zero`, `image-distance/signed-horizontal-fractional`, `image-distance/signed-vertical-float32`, `image-distance/signed-diagonal-float64`, `image-distance/signed-step-subpixel`, `image-distance/signed-fractional-ring`, `image-distance/signed-fractional-ring-inverted`, `image-distance/signed-independent-noise-773971`, `image-distance/signed-independent-noise-999783`, `image-distance/signed-small-magnitude-gradient`, `image-distance/signed-saddle`, `image-distance/signed-single-row`, `image-distance/signed-single-column`, `image-distance/full-five-input-twelve-file-originals`, `image-distance/typed-sites-Voronoi-visualization-padding`, `image-distance/arguments-streams-concurrency-extremes`, `image-distance/CLI-errors`, `image-distance/GPU-trace`, `image-distance/independent-CPU-and-native-comparison`, `image-distance/model-and-validator-checks`, `image-distance/legacy-EDT-NCC-regressions`, `image-distance/cold-checkout`, `image-distance/independent-review`。

实现方式：`ALGORITHM_VARIANT_EXACT_PROJECT_TYPED_SDF`。

恢复/扩展条件：修改数值定义、tie/site规则、布局、接口或平台必须重新固定合同并实测。

CUDA 对照限制：原始unsigned距离一致；signed-circle最大差29.944444444444457、Lith最大差0.8653281413382601及Voronoi规则差异单列。项目HIP对独立CPU全部30输入maxAbs=0，预固定预算atol2e-11/rtol1e-12，非按vendor拟合。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP+/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp:42:10: fatal error: 'nppPlus/nppPlus.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cud

尝试库：—；实现 hash：`98fb10144e9c17ec96fd296b1244514e405ea00a9ac35daed6ca2c6919da288e`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python3 tools/moat/image_distance_contracts.py
python3 tools/moat/image_distance_build.py
python3 tools/moat/image_distance_run.py
python3 tools/moat/image_distance_frontend_build.py
python3 tools/moat/image_distance_originals.py
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/NPP+_distanceTransform_unsignedAndSignedDistanceTransformNPPPlus.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/NPP+_distanceTransform_unsignedAndSignedDistanceTransformNPPPlus.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP+_distanceTransform_unsignedAndSignedDistanceTransformNPPPlus.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/NPP+_distanceTransform_unsignedAndSignedDistanceTransformNPPPlus.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP+_distanceTransform_unsignedAndSignedDistanceTransformNPPPlus.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/NPP+_distanceTransform_unsignedAndSignedDistanceTransformNPPPlus.cpp)
- [migration/reports/image-distance.md](../../../reports/image-distance.md)
- [migration/reports/evidence/rewrite/I2/NPP__distanceTransform__unsignedAndSignedDistanceTransformNPPPlus.cpp/20261111T180633.757355Z-I2-composite-qualification-cbcae7bb6d](../../../reports/evidence/rewrite/I2/NPP__distanceTransform__unsignedAndSignedDistanceTransformNPPPlus.cpp/20261111T180633.757355Z-I2-composite-qualification-cbcae7bb6d)
- [migration/reports/evidence/rewrite/I2/Distance-GPU-shared-backend-build/20261111T164229.865099Z-I2-rocm-build-a221deef64](../../../reports/evidence/rewrite/I2/Distance-GPU-shared-backend-build/20261111T164229.865099Z-I2-rocm-build-a221deef64)
- [migration/reports/evidence/rewrite/I2/Distance-actual-argument-query-and-physical-range-contracts/20261111T170234.984220Z-I2-rocm-runtime-8c0ce146f6](../../../reports/evidence/rewrite/I2/Distance-actual-argument-query-and-physical-range-contracts/20261111T170234.984220Z-I2-rocm-runtime-8c0ce146f6)
- [migration/reports/evidence/rewrite/I2/Distance-actual-states-streams-overlap-and-extremes/20261111T171124.613936Z-I2-rocm-runtime-a5f6b39145](../../../reports/evidence/rewrite/I2/Distance-actual-states-streams-overlap-and-extremes/20261111T171124.613936Z-I2-rocm-runtime-a5f6b39145)
- [migration/reports/evidence/rewrite/I2/Distance-clean-checkout-complete-original-and-runtime/20261111T174754.875439Z-I2-host-cold-replay-ce0109eb53](../../../reports/evidence/rewrite/I2/Distance-clean-checkout-complete-original-and-runtime/20261111T174754.875439Z-I2-host-cold-replay-ce0109eb53)
- [migration/reports/evidence/rewrite/I2/Distance-complete-CLI-independent-CPU/20261111T165350.673907Z-I2-CPU-reference-cd28ba0553](../../../reports/evidence/rewrite/I2/Distance-complete-CLI-independent-CPU/20261111T165350.673907Z-I2-CPU-reference-cd28ba0553)
- [migration/reports/evidence/rewrite/I2/Distance-complete-native-CPU-HIP-comparison/20261111T172404.395541Z-I2-CPU-reference-05af27a230](../../../reports/evidence/rewrite/I2/Distance-complete-native-CPU-HIP-comparison/20261111T172404.395541Z-I2-CPU-reference-05af27a230)
- [migration/reports/evidence/rewrite/I2/Distance-five-image-original-workflow-contracts/20261111T163848.440971Z-I2-CPU-contract-0f67f53e4d](../../../reports/evidence/rewrite/I2/Distance-five-image-original-workflow-contracts/20261111T163848.440971Z-I2-CPU-contract-0f67f53e4d)
- [migration/reports/evidence/rewrite/I2/Distance-fixed-argument-independent-CPU/20261111T170345.214757Z-I2-CPU-reference-efa47e55a4](../../../reports/evidence/rewrite/I2/Distance-fixed-argument-independent-CPU/20261111T170345.214757Z-I2-CPU-reference-efa47e55a4)
- [migration/reports/evidence/rewrite/I2/Distance-frozen-complete-contracts/20261111T163447.419142Z-I2-CPU-contract-8b0d4e0a1b](../../../reports/evidence/rewrite/I2/Distance-frozen-complete-contracts/20261111T163447.419142Z-I2-CPU-contract-8b0d4e0a1b)
- [migration/reports/evidence/rewrite/I2/Distance-full-independent-spatial-CPU/20261111T170234.096014Z-I2-CPU-reference-d3c47f16ca](../../../reports/evidence/rewrite/I2/Distance-full-independent-spatial-CPU/20261111T170234.096014Z-I2-CPU-reference-d3c47f16ca)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165159.731418Z-I2-rocm-CLI-ebe5aaf973](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165159.731418Z-I2-rocm-CLI-ebe5aaf973)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165201.738146Z-I2-rocm-CLI-8a2f4d99dc](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165201.738146Z-I2-rocm-CLI-8a2f4d99dc)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165203.688355Z-I2-rocm-CLI-699a351099](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165203.688355Z-I2-rocm-CLI-699a351099)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165205.587204Z-I2-rocm-CLI-e7e34c1198](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165205.587204Z-I2-rocm-CLI-e7e34c1198)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165207.489969Z-I2-rocm-CLI-2f23b60faf](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165207.489969Z-I2-rocm-CLI-2f23b60faf)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165209.369337Z-I2-rocm-CLI-8eac3dc5f0](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165209.369337Z-I2-rocm-CLI-8eac3dc5f0)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165211.237579Z-I2-rocm-CLI-0c8670c6b3](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165211.237579Z-I2-rocm-CLI-0c8670c6b3)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165213.112547Z-I2-rocm-CLI-0ffbaf13dd](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165213.112547Z-I2-rocm-CLI-0ffbaf13dd)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165214.982077Z-I2-rocm-CLI-f734cc55f1](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165214.982077Z-I2-rocm-CLI-f734cc55f1)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165216.900411Z-I2-rocm-CLI-5014ccbde0](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165216.900411Z-I2-rocm-CLI-5014ccbde0)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165218.771775Z-I2-rocm-CLI-3dc0fb4f9c](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165218.771775Z-I2-rocm-CLI-3dc0fb4f9c)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165220.679118Z-I2-rocm-CLI-5e0654b940](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165220.679118Z-I2-rocm-CLI-5e0654b940)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165222.556892Z-I2-rocm-CLI-95264028ab](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165222.556892Z-I2-rocm-CLI-95264028ab)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165224.407920Z-I2-rocm-CLI-9d7dd720fc](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165224.407920Z-I2-rocm-CLI-9d7dd720fc)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165226.305069Z-I2-rocm-CLI-f158a900e5](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165226.305069Z-I2-rocm-CLI-f158a900e5)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165228.571686Z-I2-rocm-CLI-0a8481fd1c](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165228.571686Z-I2-rocm-CLI-0a8481fd1c)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165230.698133Z-I2-rocm-CLI-0bed2f099d](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165230.698133Z-I2-rocm-CLI-0bed2f099d)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165232.559519Z-I2-rocm-CLI-4d1375af10](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165232.559519Z-I2-rocm-CLI-4d1375af10)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165234.679200Z-I2-rocm-CLI-507734c9ed](../../../reports/evidence/rewrite/I2/Distance-full-original-CLI/20261111T165234.679200Z-I2-rocm-CLI-507734c9ed)
- [migration/reports/evidence/rewrite/I2/Distance-full-original-C__-build/20261111T164256.114831Z-I2-rocm-build-690d648ef0](../../../reports/evidence/rewrite/I2/Distance-full-original-C__-build/20261111T164256.114831Z-I2-rocm-build-690d648ef0)
- [migration/reports/evidence/rewrite/I2/Distance-full-state-streams-extremes-independent-CPU/20261111T171325.286073Z-I2-CPU-reference-c461885447](../../../reports/evidence/rewrite/I2/Distance-full-state-streams-extremes-independent-CPU/20261111T171325.286073Z-I2-CPU-reference-c461885447)
- [migration/reports/evidence/rewrite/I2/Distance-full-thirty-real-device-kernels/20261111T170348.521941Z-I2-rocm-trace-03d674a99e](../../../reports/evidence/rewrite/I2/Distance-full-thirty-real-device-kernels/20261111T170348.521941Z-I2-rocm-trace-03d674a99e)
- [migration/reports/evidence/rewrite/I2/Distance-full-trace-independent-CPU/20261111T170746.184136Z-I2-CPU-reference-d33f51f1e8](../../../reports/evidence/rewrite/I2/Distance-full-trace-independent-CPU/20261111T170746.184136Z-I2-CPU-reference-d33f51f1e8)
- [migration/reports/evidence/rewrite/I2/Distance-independent-CPU-analytic-checks/20261111T171446.787732Z-I2-CPU-model-ac501b07b6](../../../reports/evidence/rewrite/I2/Distance-independent-CPU-analytic-checks/20261111T171446.787732Z-I2-CPU-model-ac501b07b6)
- [migration/reports/evidence/rewrite/I2/Distance-legacy-EDT-and-full-NCC-fresh-build/20261111T173250.484874Z-I2-rocm-build-8fbeeb0035](../../../reports/evidence/rewrite/I2/Distance-legacy-EDT-and-full-NCC-fresh-build/20261111T173250.484874Z-I2-rocm-build-8fbeeb0035)
- [migration/reports/evidence/rewrite/I2/Distance-legacy-six-EDT-eight-NCC-independent-CPU/20261111T173554.321556Z-I2-CPU-reference-47ccad9ccd](../../../reports/evidence/rewrite/I2/Distance-legacy-six-EDT-eight-NCC-independent-CPU/20261111T173554.321556Z-I2-CPU-reference-47ccad9ccd)
- [migration/reports/evidence/rewrite/I2/Distance-original-four-workflows-independent-CPU/20261111T170237.660963Z-I2-CPU-reference-f11372d558](../../../reports/evidence/rewrite/I2/Distance-original-four-workflows-independent-CPU/20261111T170237.660963Z-I2-CPU-reference-f11372d558)
- [migration/reports/evidence/rewrite/I2/Distance-real-validator-mutations/20261111T165819.470914Z-I2-CPU-validator-test-6821de3933](../../../reports/evidence/rewrite/I2/Distance-real-validator-mutations/20261111T165819.470914Z-I2-CPU-validator-test-6821de3933)
- [migration/reports/evidence/rewrite/I2/Distance-regression-distance/20261111T173255.865085Z-I2-rocm-regression-06fb911ef2](../../../reports/evidence/rewrite/I2/Distance-regression-distance/20261111T173255.865085Z-I2-rocm-regression-06fb911ef2)
- [migration/reports/evidence/rewrite/I2/Distance-regression-distance/20261111T173258.370202Z-I2-rocm-regression-dd4842b215](../../../reports/evidence/rewrite/I2/Distance-regression-distance/20261111T173258.370202Z-I2-rocm-regression-dd4842b215)
- [migration/reports/evidence/rewrite/I2/Distance-regression-distance/20261111T173300.580515Z-I2-rocm-regression-8932963660](../../../reports/evidence/rewrite/I2/Distance-regression-distance/20261111T173300.580515Z-I2-rocm-regression-8932963660)
- [migration/reports/evidence/rewrite/I2/Distance-regression-distance/20261111T173302.771572Z-I2-rocm-regression-086c4377b2](../../../reports/evidence/rewrite/I2/Distance-regression-distance/20261111T173302.771572Z-I2-rocm-regression-086c4377b2)
- [migration/reports/evidence/rewrite/I2/Distance-regression-distance/20261111T173304.926773Z-I2-rocm-regression-66ab93d1e4](../../../reports/evidence/rewrite/I2/Distance-regression-distance/20261111T173304.926773Z-I2-rocm-regression-66ab93d1e4)
- [migration/reports/evidence/rewrite/I2/Distance-regression-distance/20261111T173307.128916Z-I2-rocm-regression-e97e070d2a](../../../reports/evidence/rewrite/I2/Distance-regression-distance/20261111T173307.128916Z-I2-rocm-regression-e97e070d2a)
- [migration/reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173309.330965Z-I2-rocm-regression-f28a1054a0](../../../reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173309.330965Z-I2-rocm-regression-f28a1054a0)
- [migration/reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173316.193776Z-I2-rocm-regression-edb628653b](../../../reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173316.193776Z-I2-rocm-regression-edb628653b)
- [migration/reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173318.764694Z-I2-rocm-regression-13124714d2](../../../reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173318.764694Z-I2-rocm-regression-13124714d2)
- [migration/reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173321.212151Z-I2-rocm-regression-79c9418e47](../../../reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173321.212151Z-I2-rocm-regression-79c9418e47)
- [migration/reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173323.536116Z-I2-rocm-regression-f2d4a23753](../../../reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173323.536116Z-I2-rocm-regression-f2d4a23753)
- [migration/reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173326.110493Z-I2-rocm-regression-731d2e5ecd](../../../reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173326.110493Z-I2-rocm-regression-731d2e5ecd)
- [migration/reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173328.436434Z-I2-rocm-regression-67ebd9219c](../../../reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173328.436434Z-I2-rocm-regression-67ebd9219c)
- [migration/reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173330.727427Z-I2-rocm-regression-db289577c0](../../../reports/evidence/rewrite/I2/Distance-regression-ncc/20261111T173330.727427Z-I2-rocm-regression-db289577c0)
- [migration/reports/evidence/rewrite/I2/Distance-runtime-CLI-original-validator-mutations/20261111T174128.275008Z-I2-CPU-validator-test-7454731bb4](../../../reports/evidence/rewrite/I2/Distance-runtime-CLI-original-validator-mutations/20261111T174128.275008Z-I2-CPU-validator-test-7454731bb4)
- [migration/reports/evidence/rewrite/I2/Distance-state-and-extreme-numeric-contracts/20261111T171445.472195Z-I2-CPU-contract-7d26af65d4](../../../reports/evidence/rewrite/I2/Distance-state-and-extreme-numeric-contracts/20261111T171445.472195Z-I2-CPU-contract-7d26af65d4)
- [migration/reports/evidence/rewrite/I2/Distance-thirty-complete-inputs/20261111T165351.843649Z-I2-rocm-prototype-bdf4077298](../../../reports/evidence/rewrite/I2/Distance-thirty-complete-inputs/20261111T165351.843649Z-I2-rocm-prototype-bdf4077298)
- [migration/reports/evidence/rewrite/I2/Distance-unchanged-CUDA-original-with-full-receipts/20261111T171925.812763Z-I2-cuda-original-855e0c016a](../../../reports/evidence/rewrite/I2/Distance-unchanged-CUDA-original-with-full-receipts/20261111T171925.812763Z-I2-cuda-original-855e0c016a)
- [migration/reports/evidence/rewrite/I2/NPP__distanceTransform__unsignedAndSignedDistanceTransformNPPPlus.cpp/20261111T164302.341701Z-I2-rocm-original-a08b2823d1](../../../reports/evidence/rewrite/I2/NPP__distanceTransform__unsignedAndSignedDistanceTransformNPPPlus.cpp/20261111T164302.341701Z-I2-rocm-original-a08b2823d1)
- [migration/reports/evidence/rewrite/I2/NPP__distanceTransform__unsignedAndSignedDistanceTransformNPPPlus.cpp/20261111T164304.930332Z-I2-rocm-original-e848e14aa3](../../../reports/evidence/rewrite/I2/NPP__distanceTransform__unsignedAndSignedDistanceTransformNPPPlus.cpp/20261111T164304.930332Z-I2-rocm-original-e848e14aa3)
- [migration/reports/evidence/rewrite/I2/NPP__distanceTransform__unsignedAndSignedDistanceTransformNPPPlus.cpp/20261111T164307.057198Z-I2-rocm-original-8dfed26bf6](../../../reports/evidence/rewrite/I2/NPP__distanceTransform__unsignedAndSignedDistanceTransformNPPPlus.cpp/20261111T164307.057198Z-I2-rocm-original-8dfed26bf6)
- [migration/reports/evidence/rewrite/I2/NPP__distanceTransform__unsignedAndSignedDistanceTransformNPPPlus.cpp/20261111T164309.204860Z-I2-rocm-original-4df824750e](../../../reports/evidence/rewrite/I2/NPP__distanceTransform__unsignedAndSignedDistanceTransformNPPPlus.cpp/20261111T164309.204860Z-I2-rocm-original-4df824750e)
