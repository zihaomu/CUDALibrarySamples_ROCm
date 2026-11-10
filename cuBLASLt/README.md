# cuBLASLt Library API examples

## Description
This folder demonstrates cuBLASLt library API usage.

## Samples
- [LtDgemmPresetAlgo](LtDgemmPresetAlgo/)
    
    Sample wrapper executing double precision gemm with a predefined algorithm using cublasLtMatmul, nearly a drop-in
    replacement for cublasDgemm, with addition of the workspace to support split-K algorithms.

- [LtHSHgemmStridedBatchSimple](LtHSHgemmStridedBatchSimple/)

    Sample wrapper executing mixed precision gemm with cublasLtMatmul, nearly a drop-in replacement for cublasGemmEx,
    with addition of the workspace to support split-K algorithms.

- [LtIgemmTensor](LtIgemmTensor/)

    Use cublasLtMatmul to perform tensor-op Igemm with memory order transforms on all buffers.

- [LtPlanarComplex](LtPlanarComplex/)

    Use cublasLtMatmul to perform tensor-op Cgemm using planar complex memory layout and half-precision inputs.

- [LtSgemm](LtSgemm/)

    Sample wrapper executing single precision gemm with cublasLtMatmul, nearly a drop-in replacement for cublasSgemm,
    with addition of the workspace to support split-K algorithms.

- [LtSgemmCustomFind](LtSgemmCustomFind/)

    Sample wrapper running through multiple algo and config attributes combination for single precision gemm using cublasLt low-level API.

- [LtSgemmSimpleAutoTuning](LtSgemmSimpleAutoTuning/)

    Sample wrapper executing single precision gemm algorithm auto tuning by querying cublasLt heuristics for best algorithms,
    iterate over the results and pick the algorithm that have the best performance for the given problem.
    
## Supported SM Architectures
[SM 5.0 ](https://developer.nvidia.com/cuda-gpus)  [SM 5.2 ](https://developer.nvidia.com/cuda-gpus)  [SM 5.3 ](https://developer.nvidia.com/cuda-gpus)  [SM 6.0 ](https://developer.nvidia.com/cuda-gpus)  [SM 6.1 ](https://developer.nvidia.com/cuda-gpus)  [SM 6.2 ](https://developer.nvidia.com/cuda-gpus)  [SM 7.0 ](https://developer.nvidia.com/cuda-gpus)  [SM 7.2 ](https://developer.nvidia.com/cuda-gpus)  [SM 7.5 ](https://developer.nvidia.com/cuda-gpus)  [SM 8.0 ](https://developer.nvidia.com/cuda-gpus)  [SM 8.6 ](https://developer.nvidia.com/cuda-gpus)  [SM 8.7 ](https://developer.nvidia.com/cuda-gpus)  [SM 8.9 ](https://developer.nvidia.com/cuda-gpus)  [SM 9.0 ](https://developer.nvidia.com/cuda-gpus)  [SM 10.0 ](https://developer.nvidia.com/cuda-gpus)  [SM 10.3 ](https://developer.nvidia.com/cuda-gpus)  [SM 11.0 ](https://developer.nvidia.com/cuda-gpus)  [SM 12.0 ](https://developer.nvidia.com/cuda-gpus)  [SM 12.1 ](https://developer.nvidia.com/cuda-gpus)

## Supported OSes
Linux & Windows

## Supported CPU Architecture
x86_64

## Tested Platforms:
 - Windows 10
 - Ubuntu 18.04

## cuBLAS Documentation
[cuBLAS](https://docs.nvidia.com/cuda/cublas/index.html)

## Prerequisites
- A Linux/Windows system with NVIDIA driver of version 450.41 and above.
- [CUDA 11.0 toolkit](https://developer.nvidia.com/cuda-downloads).
- CMake 3.10 and above
- Compiler with C++ 11 or above capabilities

## Build Steps
        git clone https://github.com/NVIDIA/CUDALibrarySamples.git
        cd CUDALibrarySamples/cuBLASLt
        mkdir build
        cd build
        cmake .. -DCMAKE_BUILD_TYPE=Release
        make -j

On Windows, instead of running the last build step, open the Visual Studio Solution that was created and build.

<!-- ROCM-MIGRATION:START -->
## ROCm 迁移实时状态

20 个独立源入口；PASSED 6，PARTIAL 0，FAILED 14，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：hipBLASLt。候选不等于已使用；基础探针成功也不等于整库迁移成功。

FP32 与两种 HSH FP16 batch 路径验证通过；高级 scale/quantization、grouped/autotune 接口及 FP8 格式不能按名字强行等同。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [LtBlk128x128Fp8Matmul/main.cpp](LtBlk128x128Fp8Matmul/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtBlk128x128Fp8Matmul/main.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/Common/helpers.h:534:62: error: ambiguous conversion for functional-style cast from 'size_t' (aka 'unsigned long') to '__hip_bfloat16'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/Common/helpers.h:535:68: error: ambiguous conversion for functional-style cast from 'size_t' (aka 'unsigned long') to '__hip_bfloat16' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtBlk128x128Fp8Matmul_main.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtBlk128x128Fp8Matmul_main.cpp) |
| [LtBlk128x128Fp8gemmGroupedSimple/main.cpp](LtBlk128x128Fp8gemmGroupedSimple/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtBlk128x128Fp8gemmGroupedSimple/main.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/Common/helpers.h:534:62: error: ambiguous conversion for functional-style cast from 'size_t' (aka 'unsigned long') to '__hip_bfloat16'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/Common/helpers.h:535:68: error: ambiguous conversion for functional-style cast from 'size_t' (aka 'unsigned long') to '__hip_bfloat16' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtBlk128x128Fp8gemmGroupedSimple_main.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtBlk128x128Fp8gemmGroupedSimple_main.cpp) |
| [LtDgemmEmulated/main.cpp](LtDgemmEmulated/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtDgemmEmulated/main.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtDgemmEmulated/sample_cublasLt_LtDgemmEmulated.h:47:22: error: unknown type name 'hipblasEmulationStrategy_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtDgemmEmulated/sample_cublasLt_LtDgemmEmulated.h:48:22: error: unknown type name 'cudaEmulationSpecialValuesSupport' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtDgemmEmulated_main.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtDgemmEmulated_main.cpp) |
| [LtDgemmPresetAlgo/main.cpp](LtDgemmPresetAlgo/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtDgemmPresetAlgo/main.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtDgemmPresetAlgo/sample_cublasLt_LtDgemmPresetAlgo.cu:54:11: error: unknown type name 'cublasLtMatmulTile_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtDgemmPresetAlgo/sample_cublasLt_LtDgemmPresetAlgo.cu:54:41: error: use of undeclared identifier 'CUBLASLT_MATMUL_TILE_16x16' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtDgemmPresetAlgo_main.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtDgemmPresetAlgo_main.cpp) |
| [LtFp8CustomFind/main.cu](LtFp8CustomFind/main.cu) · [详情](../migration/sample-reports/cuBLASLt/LtFp8CustomFind/main.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/Common/LtMatmulCustomFind.h:34:5: error: unknown type name 'hipblasMath_t'; did you mean 'hipblasStatus_t'?；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/Common/LtMatmulCustomFind.h:35:5: error: unknown type name 'cublasLtReductionScheme_t' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtFp8CustomFind_main.cu)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtFp8CustomFind_main.cu) |
| [LtFp8Matmul/main.cpp](LtFp8Matmul/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtFp8Matmul/main.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtFp8Matmul/main.cpp:26:18: error: no matching function for call to 'hipblasLtGetVersion'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/Common/helpers.h:534:62: error: ambiguous conversion for functional-style cast from 'size_t' (aka 'unsigned long') to '__hip_bfloat16' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtFp8Matmul_main.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtFp8Matmul_main.cpp) |
| [LtFp8gemmGroupedSimple/main.cpp](LtFp8gemmGroupedSimple/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtFp8gemmGroupedSimple/main.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtFp8gemmGroupedSimple/main.cpp:31:9: error: use of undeclared identifier 'CUBLASLT_MATMUL_MATRIX_SCALE_PER_BATCH_SCALAR_32F'; did you mean 'HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F'?；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtFp8gemmGroupedSimple/main.cpp:31:60: error: use of undeclared identifier 'CUBLASLT_MATMUL_MATRIX_SCALE_PER_BATCH_SCALAR_32F'; did you mean 'HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F'? | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtFp8gemmGroupedSimple_main.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtFp8gemmGroupedSimple_main.cpp) |
| [LtHSHgemmGroupedSimple/main.cpp](LtHSHgemmGroupedSimple/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtHSHgemmGroupedSimple/main.cpp.md) | hipBLASLt + project search/group dispatch / hipBLASLt/rocBLAS | L4 / PASSED | 使用 hipBLASLt + project search/group dispatch，保持原始dtype/规模，全部候选完整输出、所选方案重放及workspace限制通过CPU/CUDA。分组为项目分发适配；搜索ID仅在对应后端有效，不跨库照搬CUDA算法ID；共享GPU计时不计性能资格。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261110T032310.748567Z/batches4_8-rocm/cuBLASLt_LtHSHgemmGroupedSimple_main.cpp)；[记录](../migration/reports/evidence/20261110T032104.369797Z/batches4_8-cuda/cuBLASLt_LtHSHgemmGroupedSimple_main.cpp) |
| [LtHSHgemmPointerArrayBatchSimple/main.cpp](LtHSHgemmPointerArrayBatchSimple/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtHSHgemmPointerArrayBatchSimple/main.cpp.md) | hipBLASLt / hipBLASLt | L4 / PASSED | 使用 hipBLASLt 保留原始 4×4 profile、alpha/beta 与 FP16 input/output + FP32 compute（HSH）或 FP32（SGEMM）及 batch 存储方式；完整输出通过独立 NumPy GEMM 与显式 half 舍入检查。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T100601.956702Z/original-cuda/cuBLASLt_LtHSHgemmPointerArrayBatchSimple_main.cpp)；[记录](../migration/reports/additional-comparison.json) |
| [LtHSHgemmStridedBatchSimple/main.cpp](LtHSHgemmStridedBatchSimple/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtHSHgemmStridedBatchSimple/main.cpp.md) | hipBLASLt / hipBLASLt | L4 / PASSED | 使用 hipBLASLt 保留原始 4×4 profile、alpha/beta 与 FP16 input/output + FP32 compute（HSH）或 FP32（SGEMM）及 batch 存储方式；完整输出通过独立 NumPy GEMM 与显式 half 舍入检查。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T100608.316377Z/original-cuda/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp)；[记录](../migration/reports/additional-comparison.json) |
| [LtIgemmTensor/main.cpp](LtIgemmTensor/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtIgemmTensor/main.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtIgemmTensor/sample_cublasLt_LtIgemmTensor.cu:58:36: error: use of undeclared identifier 'CUBLASLT_ORDER_COL32'; did you mean 'HIPBLASLT_ORDER_COL'?；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtIgemmTensor/sample_cublasLt_LtIgemmTensor.cu:59:42: error: use of undeclared identifier 'CUBLASLT_ORDER_COL4_4R2_8C' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtIgemmTensor_main.cpp) |
| [LtMxfp8Matmul/main.cpp](LtMxfp8Matmul/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtMxfp8Matmul/main.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtMxfp8Matmul/sample_cublasLt_LtMxfp8Matmul.h:35:26: error: unknown type name '__nv_fp8_e8m0'; did you mean '__hip_fp8_e8m0'?；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtMxfp8Matmul/sample_cublasLt_LtMxfp8Matmul.h:38:26: error: unknown type name '__nv_fp8_e8m0'; did you mean '__hip_fp8_e8m0'? | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtMxfp8Matmul_main.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtMxfp8Matmul_main.cpp) |
| [LtMxfp8gemmGroupedSimple/main.cpp](LtMxfp8gemmGroupedSimple/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtMxfp8gemmGroupedSimple/main.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtMxfp8gemmGroupedSimple/sample_cublasLt_LtMxfp8gemmGroupedSimple.h:41:37: error: unknown type name '__nv_fp8_e8m0'; did you mean '__hip_fp8_e8m0'?；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtMxfp8gemmGroupedSimple/sample_cublasLt_LtMxfp8gemmGroupedSimple.h:44:37: error: unknown type name '__nv_fp8_e8m0'; did you mean '__hip_fp8_e8m0'? | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtMxfp8gemmGroupedSimple_main.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtMxfp8gemmGroupedSimple_main.cpp) |
| [LtNvfp4Matmul/main.cpp](LtNvfp4Matmul/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtNvfp4Matmul/main.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/common/observe.hpp:14:14: error: no matching conversion for functional-style cast from '__hip_fp4x2_e2m1' to 'float'；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sam | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtNvfp4Matmul_main.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtNvfp4Matmul_main.cpp) |
| [LtNvfp4gemmGroupedSimple/main.cpp](LtNvfp4gemmGroupedSimple/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtNvfp4gemmGroupedSimple/main.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/common/observe.hpp:14:14: error: no matching conversion for functional-style cast from '__hip_fp4x2_e2m1' to 'float'；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sam | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtNvfp4gemmGroupedSimple_main.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtNvfp4gemmGroupedSimple_main.cpp) |
| [LtPlanarComplex/main.cpp](LtPlanarComplex/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtPlanarComplex/main.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtPlanarComplex/sample_cublasLt_LtPlanarComplex.cu:64:64: error: use of undeclared identifier 'CUBLASLT_MATRIX_LAYOUT_PLANE_OFFSET'; did you mean 'HIPBLASLT_MATRIX_LAYOUT_OFFSET'?；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtPlanarComplex/sample_cublasLt_LtPlanarComplex.cu:69:64: error: use of undeclared identifier 'CUBLASLT_MATRIX_LAYOUT_PLANE_OFFSET'; did you mean 'HIPBLASLT_MATRIX_LAYOUT_OFFSET'? | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtPlanarComplex_main.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtPlanarComplex_main.cpp) |
| [LtSgemm/main.cpp](LtSgemm/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtSgemm/main.cpp.md) | hipBLASLt / hipBLASLt native | L4 / PASSED | 使用 hipBLASLt（hipBLASLt native）成功实现原始 profile 和 5 个数值用例，并通过 CUDA 对照 | PASSED / PASSED | [记录](../migration/reports/blaslt-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtSgemm_main.cpp) |
| [LtSgemmCustomFind/main.cu](LtSgemmCustomFind/main.cu) · [详情](../migration/sample-reports/cuBLASLt/LtSgemmCustomFind/main.cu.md) | hipBLASLt + project search/group dispatch / hipBLASLt/rocBLAS | L4 / PASSED | 使用 hipBLASLt + project search/group dispatch，保持原始dtype/规模，全部候选完整输出、所选方案重放及workspace限制通过CPU/CUDA。分组为项目分发适配；搜索ID仅在对应后端有效，不跨库照搬CUDA算法ID；共享GPU计时不计性能资格。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261110T032310.748567Z/batches4_8-rocm/cuBLASLt_LtSgemmCustomFind_main.cu)；[记录](../migration/reports/evidence/20261110T032104.369797Z/batches4_8-cuda/cuBLASLt_LtSgemmCustomFind_main.cu) |
| [LtSgemmGreenContext/main.cpp](LtSgemmGreenContext/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtSgemmGreenContext/main.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtSgemmGreenContext/sample_cublasLt_LtSgemmGreenCtx.cu:43:5: error: unknown type name 'cudaExecutionContext_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtSgemmGreenContext/sample_cublasLt_LtSgemmGreenCtx.cu:47:9: error: unknown type name 'cudaDevResource'; did you mean 'hipDevResource'? | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtSgemmGreenContext_main.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtSgemmGreenContext_main.cpp) |
| [LtSgemmSimpleAutoTuning/main.cpp](LtSgemmSimpleAutoTuning/main.cpp) · [详情](../migration/sample-reports/cuBLASLt/LtSgemmSimpleAutoTuning/main.cpp.md) | hipBLASLt + project search/group dispatch / hipBLASLt/rocBLAS | L4 / PASSED | 使用 hipBLASLt + project search/group dispatch，保持原始dtype/规模，全部候选完整输出、所选方案重放及workspace限制通过CPU/CUDA。分组为项目分发适配；搜索ID仅在对应后端有效，不跨库照搬CUDA算法ID；共享GPU计时不计性能资格。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261110T032310.748567Z/batches4_8-rocm/cuBLASLt_LtSgemmSimpleAutoTuning_main.cpp)；[记录](../migration/reports/evidence/20261110T032104.369797Z/batches4_8-cuda/cuBLASLt_LtSgemmSimpleAutoTuning_main.cpp) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
