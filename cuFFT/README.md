# cuFFT Library - APIs Examples

## Description

This folder demonstrates cuFFT APIs usage.

[cuFFT API Documentation](https://docs.nvidia.com/cuda/cufft/index.html)

## cuFFT Samples

##### 1D FFT R2C example

* [cuFFT 1D R2C:C2R](1d_r2c_c2r/)

    The sample compute 1D FFT using R2C and C2R. See example for detailed description.

##### 1D FFT C2C example

* [cuFFT 1D C2C](1d_c2c/)

    The sample compute 1D FFT using C2C. See example for detailed description.
    
##### 2D FFT C2R example

* [cuFFT 2D C2R:R2C](2d_c2r_r2c/)

    The sample compute 2D FFT using C2R and R2C. See example for detailed description.

##### 3D FFT C2C example

* [cuFFT 3D C2C](3d_c2c/)

    The sample compute 3D FFT using C2C. See example for detailed description.

##### MutliGPU 1D FFT C2C example

* [cuFFT MGPU 1D C2C](1d_mgpu_c2c/)

    The sample compute MultiGPU 1D FFT using C2C. See example for detailed description.

##### MutliGPU 3D FFT C2C example

* [cuFFT MGPU 3D R2C:C2R](3d_mgpu_c2c/)

    The sample compute MultiGPU 3D FFT using C2C. See example for detailed description.

##### MutliGPU 3D FFT R2C:C2R example

* [cuFFT MGPU 3D R2C:C2R](3d_mgpu_r2c_c2r/)

    The sample compute MultiGPU 3D FFT using R2C and C2R. See example for detailed description.

##### cuFFT LTO callback R2C:C2R example

* [cuFFT LTO R2C:C2R](lto_callback_window_1d/)

    The sample computes a low-pass filter using using R2C and C2R with LTO callbacks. See example for detailed description.

<!-- ROCM-MIGRATION:START -->
## ROCm 支持情况

10 个独立源入口；PASSED 10，PARTIAL 0，FAILED 0，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：hipFFT, rocFFT, RCCL + HIP (distributed alternative)。候选不等于已使用；基础探针成功也不等于整库迁移成功。

原始单卡、双卡、legacy/JIT callback 分别实现；1D Xt 不支持的单 batch 路径改用 hipFFT + RCCL + GPU 合并，JIT 使用 SPIR-V。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [1d_c2c/1d_c2c_example.cpp](1d_c2c/1d_c2c_example.cpp) · [详情](../migration/sample-reports/cuFFT/1d_c2c/1d_c2c_example.cpp.md) | hipFFT / rocFFT | L4 / PASSED | 使用 hipFFT（rocFFT）成功实现原始 profile 和 6 个数值用例，并通过 CUDA 对照 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T090451.232153Z/original-rocm/cuFFT_1d_c2c_1d_c2c_example.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_1d_c2c_1d_c2c_example.cpp) |
| [1d_mgpu_c2c/1d_mgpu_c2c_example.cpp](1d_mgpu_c2c/1d_mgpu_c2c_example.cpp) · [详情](../migration/sample-reports/cuFFT/1d_mgpu_c2c/1d_mgpu_c2c_example.cpp.md) | hipFFT + RCCL + HIP / Two GPU radix decomposition and GPU merge | L4 / PASSED | hipFFT Xt 不接受该单 batch 1D 配置，改用两卡各做 128 点 hipFFT、RCCL AllGather 和 HIP radix-2 合并；保留原始 n=256、FP32、两卡与全局布局，全部复数输出通过 CPU DFT。原 CUDA 重复 {0,0} 设备配置在对照副本中修正为 {0,1}。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T100520.458756Z/original-cuda/cuFFT_1d_mgpu_c2c_1d_mgpu_c2c_example.cpp)；[记录](../migration/reports/additional-comparison.json) |
| [1d_r2c_c2r/1d_r2c_c2r_example.cpp](1d_r2c_c2r/1d_r2c_c2r_example.cpp) · [详情](../migration/sample-reports/cuFFT/1d_r2c_c2r/1d_r2c_c2r_example.cpp.md) | hipFFT / rocFFT | L4 / PASSED | 使用 hipFFT（rocFFT）成功实现原始 profile 和 6 个数值用例，并通过 CUDA 对照 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T090451.232153Z/original-rocm/cuFFT_1d_r2c_c2r_1d_r2c_c2r_example.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_1d_r2c_c2r_1d_r2c_c2r_example.cpp) |
| [2d_c2r_r2c/2d_c2r_r2c_example.cpp](2d_c2r_r2c/2d_c2r_r2c_example.cpp) · [详情](../migration/sample-reports/cuFFT/2d_c2r_r2c/2d_c2r_r2c_example.cpp.md) | hipFFT / rocFFT | L4 / PASSED | 使用 hipFFT/rocFFT 保留原始尺寸、batch 和 GPU scaling，全部数值经独立 CPU FFT 检查；2D 实现修复原始 real 输出显示的 padded stride，并显式同步异步回传。 | PASSED / BLOCKED | [记录](../migration/reports/small-fft-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_2d_c2r_r2c_2d_c2r_r2c_example.cpp) |
| [3d_c2c/3d_c2c_example.cpp](3d_c2c/3d_c2c_example.cpp) · [详情](../migration/sample-reports/cuFFT/3d_c2c/3d_c2c_example.cpp.md) | hipFFT / rocFFT | L4 / PASSED | 使用 hipFFT/rocFFT 保留原始尺寸、batch 和 GPU scaling，全部数值经独立 CPU FFT 检查；2D 实现修复原始 real 输出显示的 padded stride，并显式同步异步回传。 | PASSED / BLOCKED | [记录](../migration/reports/small-fft-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_3d_c2c_3d_c2c_example.cpp) |
| [3d_mgpu_c2c/3d_mgpu_c2c_example.cpp](3d_mgpu_c2c/3d_mgpu_c2c_example.cpp) · [详情](../migration/sample-reports/cuFFT/3d_mgpu_c2c/3d_mgpu_c2c_example.cpp.md) | hipFFT / rocFFT | L4 / PASSED | 使用 hipFFT/rocFFT 保留原始 双 GPU descriptor/分布与数据规模；全量输出通过独立 CPU NumPy/pocketfft full 256^3 C2C transform，相对 L2=1.5957800769683672e-07。性能未验收。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T100930.645396Z/original-cuda/cuFFT_3d_mgpu_c2c_3d_mgpu_c2c_example.cpp)；[记录](../migration/reports/additional-comparison.json) |
| [3d_mgpu_r2c_c2r/3d_mgpu_r2c_c2r_example.cpp](3d_mgpu_r2c_c2r/3d_mgpu_r2c_c2r_example.cpp) · [详情](../migration/sample-reports/cuFFT/3d_mgpu_r2c_c2r/3d_mgpu_r2c_c2r_example.cpp.md) | hipFFT / rocFFT | L4 / PASSED | 使用 hipFFT/rocFFT 保留原始 双 GPU descriptor/分布与数据规模；全量输出通过独立 CPU Analytic R2C -> spectrum*2 -> unnormalized C2R = input*2*N, original padded layout; padding is excluded from semantic elements，相对 L2=2.399042588663825e-07。性能未验收。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T100934.320053Z/original-cuda/cuFFT_3d_mgpu_r2c_c2r_3d_mgpu_r2c_c2r_example.cpp)；[记录](../migration/reports/additional-comparison.json) |
| [lto_callback_window_1d/src/r2c_c2r_legacy_callback_example.cu](lto_callback_window_1d/src/r2c_c2r_legacy_callback_example.cu) · [详情](../migration/sample-reports/cuFFT/lto_callback_window_1d/src/r2c_c2r_legacy_callback_example.cu.md) | hipFFT / rocFFT | L4 / PASSED | 使用 hipFFT/rocFFT 保留原始 device load callback 融合与原始 window/batch 配置；全量输出通过独立 CPU Independent CPU rfft, frequency truncation at bin32, irfft*328 on all 830 signals，相对 L2=2.746302811829082e-07。性能未验收。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu)；[记录](../migration/reports/additional-comparison.json) |
| [lto_callback_window_1d/src/r2c_c2r_lto_callback_example.cpp](lto_callback_window_1d/src/r2c_c2r_lto_callback_example.cpp) · [详情](../migration/sample-reports/cuFFT/lto_callback_window_1d/src/r2c_c2r_lto_callback_example.cpp.md) | hipFFT/rocFFT JIT callbacks + HIP compiler SPIR-V / rocFFT SPIR-V JIT integration | L4 / PASSED | HIP 编译器预生成 SPIR-V，经 hipfftXtSetJITCallback 与 FFT 内核 JIT 集成，保留 device callback 融合；原始 830×328、window32 全量输出通过独立 CPU FFT/filter/inverse 检查，L2=2.746302811829082e-07。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_lto_callback_window_1d_src_r2c_c2r_lto_callback_example.cpp)；[记录](../migration/reports/additional-comparison.json) |
| [lto_callback_window_1d/src/r2c_c2r_lto_nvrtc_callback_example.cpp](lto_callback_window_1d/src/r2c_c2r_lto_nvrtc_callback_example.cpp) · [详情](../migration/sample-reports/cuFFT/lto_callback_window_1d/src/r2c_c2r_lto_nvrtc_callback_example.cpp.md) | hipFFT/rocFFT JIT callbacks + HIPRTC / rocFFT SPIR-V JIT integration | L4 / PASSED | HIPRTC 运行时编译 SPIR-V，经 hipfftXtSetJITCallback 与 FFT 内核 JIT 集成，保留 device callback 融合；原始 830×328、window32 全量输出通过独立 CPU FFT/filter/inverse 检查，L2=2.746302811829082e-07。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_lto_callback_window_1d_src_r2c_c2r_lto_nvrtc_callback_example.cpp)；[记录](../migration/reports/additional-comparison.json) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
