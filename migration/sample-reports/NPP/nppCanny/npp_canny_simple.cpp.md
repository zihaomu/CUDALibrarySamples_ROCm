# NPP/nppCanny::npp_canny_simple.cpp

**PASSED / L4**

完整C++/Python原例三PNG、1预热/10测量及两类OpenCV比较；22组mask/padding对独立CPU精确，55项运行合同、真实C++ ROI/错误/并发实例、10 CLI/无设备、39正反例、trace、冷检出和三复审通过。采用经典8连接强种子滞后：原图比NPP少4328个弱边缘像素（IoU0.6323），全部强种子保留，实测项目边缘均包含在native边缘中；不宣称NPP mask逐点兼容。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP/nppCanny/npp_canny_simple.cpp](../../../../NPP/nppCanny/npp_canny_simple.cpp) |
| 实际库 / 后端 | HIP C3 Sobel/NMS/GPU union-find hysteresis + OpenCV file IO/CPU comparisons / project HIP classical C3 Canny |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP/nppCanny/npp_canny_simple.cpp](../../../../rocm/ported/NPP/nppCanny/npp_canny_simple.cpp) |
| required cases | 30/30 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `baf56fa10d093239368ac3feb40874b3d76f9a9d97824697ea8851d196a68eb4` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`image-C3/original-teapot`, `image-C3/constant-zero`, `image-C3/constant-gray`, `image-C3/step-channel-0`, `image-C3/step-channel-1`, `image-C3/step-channel-2`, `image-C3/isoluminant-color-step`, `image-C3/isolated-weak-step`, `image-C3/weak-step-with-strong-seed`, `image-C3/strong-cross`, `image-C3/strong-diagonal`, `image-C3/border-frame`, `image-C3/impulse`, `image-C3/independent-noise-128374`, `image-C3/independent-noise-983743`, `image-C3/independent-noise-762321`, `image-C3/one-pixel`, `image-C3/single-row`, `image-C3/single-column`, `image-C3/equal-threshold`, `image-C3/high-threshold`, `image-C3/zero-threshold`, `image-C3/full-original-three-files-and-10-loops`, `image-C3/runtime-and-actual-ABI`, `image-C3/real-C++-class-ROI-errors-and-instances`, `image-C3/default-file-errors-and-no-device`, `image-C3/raw-GPU-trace`, `image-C3/validator-negative`, `image-C3/cold-checkout`, `image-C3/independent-source-review`。

实现方式：`ALGORITHM_VARIANT_C3_CLASSICAL_HYSTERESIS`。

恢复/扩展条件：变更算法/阈值/布局/规模/平台或性能声明需新冻结并完整实测。

CUDA 对照限制：22组真实native NPP成功；18组mask精确，原图、孤立弱边缘、高强阈值、零阈值按已固定的经典8连接变体完整记录差异。原始CUDA C++另实测成功；原Python依赖缺口单列。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/nppCanny/npp_canny_simple.cpp:33:10: fatal error: 'opencv2/opencv.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/

尝试库：—；实现 hash：`7adbac6cac499239424949127761525e82d9128380500cadd717b0283b1b8c50`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python3 tools/moat/canny_color_build.py
python3 tools/moat/canny_color_run.py
python3 tools/moat/canny_color_run.py --originals
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/evidence/20261110T051547.561861Z/batches12_15-rocm/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261110T051547.561861Z/batches12_15-rocm/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/batches12_15-validation.json](../../../reports/batches12_15-validation.json)
- [migration/reports/evidence/20261110T051436.908488Z/batches12_15-cuda/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261110T051436.908488Z/batches12_15-cuda/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/evidence/20261110T053436.400711Z/batches12_15-rocm/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261110T053436.400711Z/batches12_15-rocm/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/evidence/20261110T053230.152526Z/batches12_15-cuda/NPP_nppCanny_npp_canny_simple.cpp](../../../reports/evidence/20261110T053230.152526Z/batches12_15-cuda/NPP_nppCanny_npp_canny_simple.cpp)
- [migration/reports/canny-color.md](../../../reports/canny-color.md)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T134944.382367Z-I1-composite-qualification-de4a35e530](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T134944.382367Z-I1-composite-qualification-de4a35e530)
- [migration/reports/evidence/rewrite/I1/C3-Canny-CLI-independent-check/20261111T133344.842713Z-I1-CPU-reference-437b1ac188](../../../reports/evidence/rewrite/I1/C3-Canny-CLI-independent-check/20261111T133344.842713Z-I1-CPU-reference-437b1ac188)
- [migration/reports/evidence/rewrite/I1/C3-Canny-C__-class-independent-check/20261111T131709.455515Z-I1-CPU-reference-d7ab526084](../../../reports/evidence/rewrite/I1/C3-Canny-C__-class-independent-check/20261111T131709.455515Z-I1-CPU-reference-d7ab526084)
- [migration/reports/evidence/rewrite/I1/C3-Canny-both-public-APIs/20261111T130002.873095Z-I1-rocm-run-facc5cc9e6](../../../reports/evidence/rewrite/I1/C3-Canny-both-public-APIs/20261111T130002.873095Z-I1-rocm-run-facc5cc9e6)
- [migration/reports/evidence/rewrite/I1/C3-Canny-clean-checkout/20261111T133732.314009Z-I1-host-cold-replay-000ee189ff](../../../reports/evidence/rewrite/I1/C3-Canny-clean-checkout/20261111T133732.314009Z-I1-host-cold-replay-000ee189ff)
- [migration/reports/evidence/rewrite/I1/C3-Canny-complete-masks/20261111T130421.254625Z-I1-CPU-reference-5d7d8350e1](../../../reports/evidence/rewrite/I1/C3-Canny-complete-masks/20261111T130421.254625Z-I1-CPU-reference-5d7d8350e1)
- [migration/reports/evidence/rewrite/I1/C3-Canny-contract-and-fixtures/20261111T123551.898143Z-I1-CPU-fixtures-809377af53](../../../reports/evidence/rewrite/I1/C3-Canny-contract-and-fixtures/20261111T123551.898143Z-I1-CPU-fixtures-809377af53)
- [migration/reports/evidence/rewrite/I1/C3-Canny-deterministic-fixtures/20261111T125520.286886Z-I1-CPU-fixtures-1021202580](../../../reports/evidence/rewrite/I1/C3-Canny-deterministic-fixtures/20261111T125520.286886Z-I1-CPU-fixtures-1021202580)
- [migration/reports/evidence/rewrite/I1/C3-Canny-full-build/20261111T125815.409990Z-I1-rocm-build-e4019a75d5](../../../reports/evidence/rewrite/I1/C3-Canny-full-build/20261111T125815.409990Z-I1-rocm-build-e4019a75d5)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-build/20261111T124455.300560Z-I1-cuda-build-23b6396e6b](../../../reports/evidence/rewrite/I1/C3-Canny-native-build/20261111T124455.300560Z-I1-cuda-build-23b6396e6b)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124458.915110Z-I1-cuda-run-d786ac28a9](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124458.915110Z-I1-cuda-run-d786ac28a9)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124501.305069Z-I1-cuda-run-3540868ad4](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124501.305069Z-I1-cuda-run-3540868ad4)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124503.572135Z-I1-cuda-run-acc4b13ed0](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124503.572135Z-I1-cuda-run-acc4b13ed0)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124505.984676Z-I1-cuda-run-fe53add719](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124505.984676Z-I1-cuda-run-fe53add719)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124508.326792Z-I1-cuda-run-32bdaea6c2](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124508.326792Z-I1-cuda-run-32bdaea6c2)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124510.629917Z-I1-cuda-run-b48992e939](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124510.629917Z-I1-cuda-run-b48992e939)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124512.967840Z-I1-cuda-run-34f2277a37](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124512.967840Z-I1-cuda-run-34f2277a37)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124515.345644Z-I1-cuda-run-d4628bf02a](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124515.345644Z-I1-cuda-run-d4628bf02a)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124517.685914Z-I1-cuda-run-878e94328f](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124517.685914Z-I1-cuda-run-878e94328f)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124520.074654Z-I1-cuda-run-bcecd4f45f](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124520.074654Z-I1-cuda-run-bcecd4f45f)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124522.383363Z-I1-cuda-run-74783b3da9](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124522.383363Z-I1-cuda-run-74783b3da9)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124524.706845Z-I1-cuda-run-028f530155](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124524.706845Z-I1-cuda-run-028f530155)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124527.093502Z-I1-cuda-run-f14f4262c9](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124527.093502Z-I1-cuda-run-f14f4262c9)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124529.476202Z-I1-cuda-run-809637dbc3](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124529.476202Z-I1-cuda-run-809637dbc3)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124531.864428Z-I1-cuda-run-aecc4f4dd7](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124531.864428Z-I1-cuda-run-aecc4f4dd7)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124534.238600Z-I1-cuda-run-858fe72026](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124534.238600Z-I1-cuda-run-858fe72026)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124536.632615Z-I1-cuda-run-eab63b208d](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124536.632615Z-I1-cuda-run-eab63b208d)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124539.142390Z-I1-cuda-run-76d83134e5](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124539.142390Z-I1-cuda-run-76d83134e5)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124541.508245Z-I1-cuda-run-a00857c6f1](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124541.508245Z-I1-cuda-run-a00857c6f1)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124543.899840Z-I1-cuda-run-f22fb3b38f](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124543.899840Z-I1-cuda-run-f22fb3b38f)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124546.265667Z-I1-cuda-run-eec5719438](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124546.265667Z-I1-cuda-run-eec5719438)
- [migration/reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124548.630365Z-I1-cuda-run-b3e29b3863](../../../reports/evidence/rewrite/I1/C3-Canny-native-mask/20261111T124548.630365Z-I1-cuda-run-b3e29b3863)
- [migration/reports/evidence/rewrite/I1/C3-Canny-original-CUDA-file-verification/20261111T130036.265905Z-I1-CPU-reference-960e13f829](../../../reports/evidence/rewrite/I1/C3-Canny-original-CUDA-file-verification/20261111T130036.265905Z-I1-CPU-reference-960e13f829)
- [migration/reports/evidence/rewrite/I1/C3-Canny-originals/20261111T130421.264655Z-I1-CPU-reference-b61f8970f8](../../../reports/evidence/rewrite/I1/C3-Canny-originals/20261111T130421.264655Z-I1-CPU-reference-b61f8970f8)
- [migration/reports/evidence/rewrite/I1/C3-Canny-runtime-CPU-check/20261111T130421.327461Z-I1-CPU-reference-ea13fad9aa](../../../reports/evidence/rewrite/I1/C3-Canny-runtime-CPU-check/20261111T130421.327461Z-I1-CPU-reference-ea13fad9aa)
- [migration/reports/evidence/rewrite/I1/C3-Canny-runtime/20261111T130004.170118Z-I1-rocm-runtime-158fb53156](../../../reports/evidence/rewrite/I1/C3-Canny-runtime/20261111T130004.170118Z-I1-rocm-runtime-158fb53156)
- [migration/reports/evidence/rewrite/I1/C3-Canny-runtime/20261111T130005.286455Z-I1-rocm-trace-60344be9aa](../../../reports/evidence/rewrite/I1/C3-Canny-runtime/20261111T130005.286455Z-I1-rocm-trace-60344be9aa)
- [migration/reports/evidence/rewrite/I1/C3-Canny-trace-CPU-check/20261111T130421.304841Z-I1-CPU-reference-c707b1df03](../../../reports/evidence/rewrite/I1/C3-Canny-trace-CPU-check/20261111T130421.304841Z-I1-CPU-reference-c707b1df03)
- [migration/reports/evidence/rewrite/I1/C3-Canny-validator-mutations/20261111T131710.747758Z-I1-CPU-validator-test-aab106c466](../../../reports/evidence/rewrite/I1/C3-Canny-validator-mutations/20261111T131710.747758Z-I1-CPU-validator-test-aab106c466)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T125651.093276Z-I1-cuda-original-0b26d5d685](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T125651.093276Z-I1-cuda-original-0b26d5d685)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T130002.915816Z-I1-rocm-original-899baf79ea](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T130002.915816Z-I1-rocm-original-899baf79ea)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T130005.379157Z-I1-rocm-original-9d5ffdbe04](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T130005.379157Z-I1-rocm-original-9d5ffdbe04)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T130007.597332Z-I1-rocm-original-5f1091bc4b](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T130007.597332Z-I1-rocm-original-5f1091bc4b)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T130009.968776Z-I1-rocm-original-28ac49ffa7](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T130009.968776Z-I1-rocm-original-28ac49ffa7)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T130012.002589Z-I1-rocm-original-6f74d0a195](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T130012.002589Z-I1-rocm-original-6f74d0a195)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T130928.329112Z-I1-rocm-C++-runtime-4f1085fb80](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T130928.329112Z-I1-rocm-C++-runtime-4f1085fb80)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T132657.918211Z-I1-rocm-CLI-ea9d0402a2](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T132657.918211Z-I1-rocm-CLI-ea9d0402a2)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T132700.720011Z-I1-rocm-CLI-0733bc9d2b](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T132700.720011Z-I1-rocm-CLI-0733bc9d2b)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T132702.612676Z-I1-rocm-CLI-0dbbcdea5f](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T132702.612676Z-I1-rocm-CLI-0dbbcdea5f)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T132704.483615Z-I1-rocm-CLI-2441b03dc5](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T132704.483615Z-I1-rocm-CLI-2441b03dc5)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T132706.531897Z-I1-rocm-CLI-1863805b37](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.cpp/20261111T132706.531897Z-I1-rocm-CLI-1863805b37)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T125718.122262Z-I1-cuda-original-edc8139bf1](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T125718.122262Z-I1-cuda-original-edc8139bf1)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T130014.056912Z-I1-rocm-original-956f216a8f](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T130014.056912Z-I1-rocm-original-956f216a8f)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T130017.593126Z-I1-rocm-original-0574e34db0](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T130017.593126Z-I1-rocm-original-0574e34db0)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T130021.096225Z-I1-rocm-original-a3eae9c000](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T130021.096225Z-I1-rocm-original-a3eae9c000)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T130024.714513Z-I1-rocm-original-3d24172d0c](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T130024.714513Z-I1-rocm-original-3d24172d0c)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T130028.799336Z-I1-rocm-original-12efa9b1e7](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T130028.799336Z-I1-rocm-original-12efa9b1e7)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T132708.518364Z-I1-rocm-CLI-7f93c94bee](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T132708.518364Z-I1-rocm-CLI-7f93c94bee)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T132712.220663Z-I1-rocm-CLI-e41d545a69](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T132712.220663Z-I1-rocm-CLI-e41d545a69)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T132715.350017Z-I1-rocm-CLI-42d891a119](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T132715.350017Z-I1-rocm-CLI-42d891a119)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T132718.419319Z-I1-rocm-CLI-9e76d10fa1](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T132718.419319Z-I1-rocm-CLI-9e76d10fa1)
- [migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T132721.980476Z-I1-rocm-CLI-8b9044dd47](../../../reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T132721.980476Z-I1-rocm-CLI-8b9044dd47)
- [migration/reports/evidence/rewrite/I1/image-private-OpenCV-C__/20261111T123829.979807Z-I1-host-setup-196d7f2db2](../../../reports/evidence/rewrite/I1/image-private-OpenCV-C__/20261111T123829.979807Z-I1-host-setup-196d7f2db2)
