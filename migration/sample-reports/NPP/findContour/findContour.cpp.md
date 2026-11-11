# NPP/findContour::findContour.cpp

**PASSED / L4**

两个完整C++入口；22组全像素/逐edge闭环顺序/bbox/count/范围重建，15个实际流程/55RAW/逐点诊断，32CLI、61参数、26畸形设备数据、11状态/stream、58验收器反例及trace/冷检出/三复审通过。保持原例输出与范围/bypass行为；使用公开项目有向单元边表示，非NPP packed ABI。原生错误分区和早期ABI1缺边失败保留单列。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP/findContour/findContour.cpp](../../../../NPP/findContour/findContour.cpp) |
| 实际库 / 后端 | Project HIP equal-value 8-connected CCL + directed cell-edge loops + GPU ordering and geometry rasterization / project HIP contour geometry |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP/findContour/findContour.cpp](../../../../rocm/ported/NPP/findContour/findContour.cpp) |
| required cases | 31/31 |
| CUDA baseline / comparison | PASSED / OBSERVED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `2c8e6ed514f58258b3482cf58adf91a48cbccd17fbebc7680f0e90ba286d1680` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`image-contour/npp-original-CircuitBoard`, `image-contour/plus-original-CircuitBoard`, `image-contour/constant-0`, `image-contour/constant-1`, `image-contour/constant-255`, `image-contour/one-pixel`, `image-contour/single-row`, `image-contour/single-column`, `image-contour/single-island`, `image-contour/ROI-frame`, `image-contour/annulus`, `image-contour/nested-multivalue-holes`, `image-contour/diagonal-touch-two-loops`, `image-contour/clipped-objects`, `image-contour/thin-lines-and-junction`, `image-contour/serpentine`, `image-contour/independent-noise-875231`, `image-contour/independent-noise-821131`, `image-contour/independent-noise-213197`, `image-contour/all-four-neighbor-isolated-eight-connected`, `image-contour/large-single-selected-ID-override`, `image-contour/large-multiple-ID-bypass`, `image-contour/full-original-files-and-ordered-diagnostics`, `image-contour/ranges-bypass-and-single-ID-override`, `image-contour/closed-geometry-and-reconstruction`, `image-contour/actual-runtime-streams-concurrency`, `image-contour/CLI-and-invalid-device-data`, `image-contour/GPU-trace`, `image-contour/validator-mutations`, `image-contour/cold-checkout`, `image-contour/independent-review`。

实现方式：`ALGORITHM_VARIANT_EXACT_PROJECT_GEOMETRY`。

恢复/扩展条件：修改连接、几何、布局、范围、接口或平台须重新固定合同并实测。

CUDA 对照限制：原图正确262分量，NPP273/NPP+266，72002/13246像素分区不同；原生0边界编码与其自身标签对应，HIP按独立CPU正确分区。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/findContour/findContour.cpp:26:10: fatal error: 'npp.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamp

尝试库：—；实现 hash：`3d21eeb31254a57008b13017e56d924e3e098d6bda6ca1b04d8e36bd1edb3e83`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python3 tools/moat/image_contour_contracts.py
python3 tools/moat/image_contour_build.py
python3 tools/moat/image_contour_run.py
python3 tools/moat/image_contour_frontends_build.py
python3 tools/moat/image_contour_originals.py
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/NPP_findContour_findContour.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/NPP_findContour_findContour.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP_findContour_findContour.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/NPP_findContour_findContour.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP_findContour_findContour.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/NPP_findContour_findContour.cpp)
- [migration/reports/image-contour.md](../../../reports/image-contour.md)
- [migration/reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T162136.463283Z-I2-composite-qualification-d3edc4961f](../../../reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T162136.463283Z-I2-composite-qualification-d3edc4961f)
- [migration/reports/evidence/rewrite/I0/I2-contour-native-label-boundary-research/20261111T144347.540300Z-I0-CPU-research-a6d5a9e7f7](../../../reports/evidence/rewrite/I0/I2-contour-native-label-boundary-research/20261111T144347.540300Z-I0-CPU-research-a6d5a9e7f7)
- [migration/reports/evidence/rewrite/I0/NPP__findContour__findContourNPPPlus.cpp/20261111T143925.653981Z-I0-cuda-original-8d2d32ef8b](../../../reports/evidence/rewrite/I0/NPP__findContour__findContourNPPPlus.cpp/20261111T143925.653981Z-I0-cuda-original-8d2d32ef8b)
- [migration/reports/evidence/rewrite/I0/NPP_findContour__findContour.cpp/20261111T143920.643375Z-I0-cuda-original-44dd678001](../../../reports/evidence/rewrite/I0/NPP_findContour__findContour.cpp/20261111T143920.643375Z-I0-cuda-original-44dd678001)
- [migration/reports/evidence/rewrite/I2/Contour-CLI-independent-CPU/20261111T161553.608888Z-I2-CPU-reference-92eb0daa07](../../../reports/evidence/rewrite/I2/Contour-CLI-independent-CPU/20261111T161553.608888Z-I2-CPU-reference-92eb0daa07)
- [migration/reports/evidence/rewrite/I2/Contour-GPU-complete-geometry-all/20261111T151945.469071Z-I2-rocm-prototype-48064e6c01](../../../reports/evidence/rewrite/I2/Contour-GPU-complete-geometry-all/20261111T151945.469071Z-I2-rocm-prototype-48064e6c01)
- [migration/reports/evidence/rewrite/I2/Contour-GPU-geometry-build/20261111T151937.250014Z-I2-rocm-build-af6a53236d](../../../reports/evidence/rewrite/I2/Contour-GPU-geometry-build/20261111T151937.250014Z-I2-rocm-build-af6a53236d)
- [migration/reports/evidence/rewrite/I2/Contour-actual-argument-and-query-errors/20261111T154029.438048Z-I2-rocm-runtime-6f58396312](../../../reports/evidence/rewrite/I2/Contour-actual-argument-and-query-errors/20261111T154029.438048Z-I2-rocm-runtime-6f58396312)
- [migration/reports/evidence/rewrite/I2/Contour-actual-validator-mutations/20261111T160931.855865Z-I2-CPU-validator-test-153f7dcf0d](../../../reports/evidence/rewrite/I2/Contour-actual-validator-mutations/20261111T160931.855865Z-I2-CPU-validator-test-153f7dcf0d)
- [migration/reports/evidence/rewrite/I2/Contour-arguments-fixed-CPU-check/20261111T154035.677724Z-I2-CPU-reference-e8736de99b](../../../reports/evidence/rewrite/I2/Contour-arguments-fixed-CPU-check/20261111T154035.677724Z-I2-CPU-reference-e8736de99b)
- [migration/reports/evidence/rewrite/I2/Contour-clean-checkout/20261111T161048.114670Z-I2-host-cold-replay-85c8a19f8b](../../../reports/evidence/rewrite/I2/Contour-clean-checkout/20261111T161048.114670Z-I2-host-cold-replay-85c8a19f8b)
- [migration/reports/evidence/rewrite/I2/Contour-data-errors-CPU/20261111T152735.418544Z-I2-CPU-reference-9e15cb71e8](../../../reports/evidence/rewrite/I2/Contour-data-errors-CPU/20261111T152735.418544Z-I2-CPU-reference-9e15cb71e8)
- [migration/reports/evidence/rewrite/I2/Contour-frozen-contracts/20261111T151933.274984Z-I2-CPU-contract-7185f7d722](../../../reports/evidence/rewrite/I2/Contour-frozen-contracts/20261111T151933.274984Z-I2-CPU-contract-7185f7d722)
- [migration/reports/evidence/rewrite/I2/Contour-full-geometry-all-CPU/20261111T152246.582939Z-I2-CPU-reference-25eeebf1bd](../../../reports/evidence/rewrite/I2/Contour-full-geometry-all-CPU/20261111T152246.582939Z-I2-CPU-reference-25eeebf1bd)
- [migration/reports/evidence/rewrite/I2/Contour-legacy-ABI1-contract-failure/20261111T152739.949794Z-I2-rocm-data-errors-c5f127f306](../../../reports/evidence/rewrite/I2/Contour-legacy-ABI1-contract-failure/20261111T152739.949794Z-I2-rocm-data-errors-c5f127f306)
- [migration/reports/evidence/rewrite/I2/Contour-legacy-data-error-CPU/20261111T152746.076682Z-I2-CPU-reference-3a5910b967](../../../reports/evidence/rewrite/I2/Contour-legacy-data-error-CPU/20261111T152746.076682Z-I2-CPU-reference-3a5910b967)
- [migration/reports/evidence/rewrite/I2/Contour-malformed-device-geometry-errors/20261111T152729.051437Z-I2-rocm-data-errors-fa120d65b7](../../../reports/evidence/rewrite/I2/Contour-malformed-device-geometry-errors/20261111T152729.051437Z-I2-rocm-data-errors-fa120d65b7)
- [migration/reports/evidence/rewrite/I2/Contour-real-C__-originals-CPU/20261111T160919.174378Z-I2-CPU-reference-633735062b](../../../reports/evidence/rewrite/I2/Contour-real-C__-originals-CPU/20261111T160919.174378Z-I2-CPU-reference-633735062b)
- [migration/reports/evidence/rewrite/I2/Contour-real-loop-and-raster-kernels/20261111T153109.837933Z-I2-rocm-trace-8523ae4d5c](../../../reports/evidence/rewrite/I2/Contour-real-loop-and-raster-kernels/20261111T153109.837933Z-I2-rocm-trace-8523ae4d5c)
- [migration/reports/evidence/rewrite/I2/Contour-real-state-streams-and-concurrent-instances/20261111T154745.577448Z-I2-rocm-runtime-6f8e5d6d3a](../../../reports/evidence/rewrite/I2/Contour-real-state-streams-and-concurrent-instances/20261111T154745.577448Z-I2-rocm-runtime-6f8e5d6d3a)
- [migration/reports/evidence/rewrite/I2/Contour-state-streams-independent-CPU/20261111T154754.396969Z-I2-CPU-reference-7bb12136a9](../../../reports/evidence/rewrite/I2/Contour-state-streams-independent-CPU/20261111T154754.396969Z-I2-CPU-reference-7bb12136a9)
- [migration/reports/evidence/rewrite/I2/Contour-trace-full-CPU-and-dispatch-check/20261111T153427.124565Z-I2-CPU-reference-9f6f38542a](../../../reports/evidence/rewrite/I2/Contour-trace-full-CPU-and-dispatch-check/20261111T153427.124565Z-I2-CPU-reference-9f6f38542a)
- [migration/reports/evidence/rewrite/I2/Contour-two-original-C__-build/20261111T151952.557947Z-I2-rocm-build-4f8e18523d](../../../reports/evidence/rewrite/I2/Contour-two-original-C__-build/20261111T151952.557947Z-I2-rocm-build-4f8e18523d)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161459.063968Z-I2-rocm-CLI-b6541fa25e](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161459.063968Z-I2-rocm-CLI-b6541fa25e)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161500.921302Z-I2-rocm-CLI-2af358c5fa](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161500.921302Z-I2-rocm-CLI-2af358c5fa)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161502.745713Z-I2-rocm-CLI-d613bb4978](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161502.745713Z-I2-rocm-CLI-d613bb4978)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161504.591362Z-I2-rocm-CLI-940b85a59b](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161504.591362Z-I2-rocm-CLI-940b85a59b)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161506.443810Z-I2-rocm-CLI-cb9f122cbc](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161506.443810Z-I2-rocm-CLI-cb9f122cbc)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161508.262399Z-I2-rocm-CLI-70280420e1](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161508.262399Z-I2-rocm-CLI-70280420e1)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161510.097276Z-I2-rocm-CLI-c0266f6be0](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161510.097276Z-I2-rocm-CLI-c0266f6be0)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161511.923888Z-I2-rocm-CLI-f63ecb8088](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161511.923888Z-I2-rocm-CLI-f63ecb8088)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161513.750462Z-I2-rocm-CLI-d0b7585d76](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161513.750462Z-I2-rocm-CLI-d0b7585d76)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161515.748288Z-I2-rocm-CLI-0a23b1d30b](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161515.748288Z-I2-rocm-CLI-0a23b1d30b)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161517.718038Z-I2-rocm-CLI-a4ca1e4169](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161517.718038Z-I2-rocm-CLI-a4ca1e4169)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161519.709257Z-I2-rocm-CLI-ebf911ebf3](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161519.709257Z-I2-rocm-CLI-ebf911ebf3)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161521.734784Z-I2-rocm-CLI-483f361e37](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161521.734784Z-I2-rocm-CLI-483f361e37)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161523.778323Z-I2-rocm-CLI-72ab11da5a](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161523.778323Z-I2-rocm-CLI-72ab11da5a)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161525.714792Z-I2-rocm-CLI-f580f92024](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161525.714792Z-I2-rocm-CLI-f580f92024)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161527.602256Z-I2-rocm-CLI-26bd20ba8f](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161527.602256Z-I2-rocm-CLI-26bd20ba8f)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161529.535308Z-I2-rocm-CLI-a2d258ccb1](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161529.535308Z-I2-rocm-CLI-a2d258ccb1)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161531.602817Z-I2-rocm-CLI-7164dac7f1](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161531.602817Z-I2-rocm-CLI-7164dac7f1)
- [migration/reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161533.497791Z-I2-rocm-CLI-bde261ccb8](../../../reports/evidence/rewrite/I2/NPP__findContour-CLI/20261111T161533.497791Z-I2-rocm-CLI-bde261ccb8)
- [migration/reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152010.275997Z-I2-rocm-original-cbbafc26f4](../../../reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152010.275997Z-I2-rocm-original-cbbafc26f4)
- [migration/reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152012.435467Z-I2-rocm-original-a675ea6179](../../../reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152012.435467Z-I2-rocm-original-a675ea6179)
- [migration/reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152014.439595Z-I2-rocm-original-b5e8295a91](../../../reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152014.439595Z-I2-rocm-original-b5e8295a91)
- [migration/reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152016.457793Z-I2-rocm-original-3a6893d4d5](../../../reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152016.457793Z-I2-rocm-original-3a6893d4d5)
- [migration/reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152018.477177Z-I2-rocm-original-4914f25782](../../../reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152018.477177Z-I2-rocm-original-4914f25782)
- [migration/reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152020.506900Z-I2-rocm-original-d892592a70](../../../reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152020.506900Z-I2-rocm-original-d892592a70)
- [migration/reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152023.117762Z-I2-rocm-original-0ba7ca8a52](../../../reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152023.117762Z-I2-rocm-original-0ba7ca8a52)
- [migration/reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152025.260117Z-I2-rocm-original-e94ec8d66e](../../../reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152025.260117Z-I2-rocm-original-e94ec8d66e)
- [migration/reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152027.804123Z-I2-rocm-original-eb466eeb60](../../../reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152027.804123Z-I2-rocm-original-eb466eeb60)
- [migration/reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152029.818672Z-I2-rocm-original-dabce831d4](../../../reports/evidence/rewrite/I2/NPP__findContour__findContourNPPPlus.cpp/20261111T152029.818672Z-I2-rocm-original-dabce831d4)
- [migration/reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161433.999819Z-I2-rocm-CLI-d348b2b4d4](../../../reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161433.999819Z-I2-rocm-CLI-d348b2b4d4)
- [migration/reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161436.023368Z-I2-rocm-CLI-3d2e870b70](../../../reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161436.023368Z-I2-rocm-CLI-3d2e870b70)
- [migration/reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161437.887799Z-I2-rocm-CLI-208c636e43](../../../reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161437.887799Z-I2-rocm-CLI-208c636e43)
- [migration/reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161439.702039Z-I2-rocm-CLI-7f16886603](../../../reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161439.702039Z-I2-rocm-CLI-7f16886603)
- [migration/reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161441.547737Z-I2-rocm-CLI-c1e095501c](../../../reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161441.547737Z-I2-rocm-CLI-c1e095501c)
- [migration/reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161443.417321Z-I2-rocm-CLI-c838eaf7d2](../../../reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161443.417321Z-I2-rocm-CLI-c838eaf7d2)
- [migration/reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161445.267166Z-I2-rocm-CLI-9ce833e9bf](../../../reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161445.267166Z-I2-rocm-CLI-9ce833e9bf)
- [migration/reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161447.115572Z-I2-rocm-CLI-1e5ffd05f7](../../../reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161447.115572Z-I2-rocm-CLI-1e5ffd05f7)
- [migration/reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161448.957011Z-I2-rocm-CLI-538000700c](../../../reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161448.957011Z-I2-rocm-CLI-538000700c)
- [migration/reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161450.926794Z-I2-rocm-CLI-b4b2e96e37](../../../reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161450.926794Z-I2-rocm-CLI-b4b2e96e37)
- [migration/reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161452.892931Z-I2-rocm-CLI-f499535149](../../../reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161452.892931Z-I2-rocm-CLI-f499535149)
- [migration/reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161454.849088Z-I2-rocm-CLI-02ef4f4387](../../../reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161454.849088Z-I2-rocm-CLI-02ef4f4387)
- [migration/reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161457.073899Z-I2-rocm-CLI-a44c436492](../../../reports/evidence/rewrite/I2/NPP_findContour-CLI/20261111T161457.073899Z-I2-rocm-CLI-a44c436492)
- [migration/reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T151959.744967Z-I2-rocm-original-d9f6638d9b](../../../reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T151959.744967Z-I2-rocm-original-d9f6638d9b)
- [migration/reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T152002.213747Z-I2-rocm-original-aa8756c99a](../../../reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T152002.213747Z-I2-rocm-original-aa8756c99a)
- [migration/reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T152004.255838Z-I2-rocm-original-5f560f842d](../../../reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T152004.255838Z-I2-rocm-original-5f560f842d)
- [migration/reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T152006.301472Z-I2-rocm-original-ff7bc31597](../../../reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T152006.301472Z-I2-rocm-original-ff7bc31597)
- [migration/reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T152008.273045Z-I2-rocm-original-6fc17f2e31](../../../reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T152008.273045Z-I2-rocm-original-6fc17f2e31)
