# cuBLAS Library - APIs Examples

## Description

This folder demonstrates cuBLAS APIs usage.

[cuBLAS API Documentation](https://docs.nvidia.com/cuda/cublas/index.html)

## cuBLAS Samples

##### cuBLAS Level 1

* [cuBLAS amax](Level-1/amax/)

    The sample finds the (smallest) index of the element of the maximum magnitude.

* [cuBLAS amin](Level-1/amin/)

    The sample finds the (smallest) index of the element of the minimum magnitude.

* [cuBLAS asum](Level-1/asum/)

    The sample computes the sum of the absolute values of the elements of vector _x_.

* [cuBLAS axpy](Level-1/axpy/)

    The sample computes a vector-scalar product and adds the result to a vector.

* [cuBLAS copy](Level-1/copy/)

    The sample copies the vector _x_ into the vector _y_.

* [cuBLAS dot](Level-1/dot/)

    The sample applies the dot product to vector _x_ and _y_.

* [cuBLAS nrm2](Level-1/nrm2/)

    The sample computes the Euclidean norm of a vector.

* [cuBLAS rot](Level-1/rot/)

    The sample applies the Givens rotation matrix to vector _x_ and _y_.

* [cuBLAS rotg](Level-1/rotg/)

    The sample applies the Givens rotation matrix to vector _x_ and _y_.

* [cuBLAS rotm](Level-1/rotm/)

    The sample applies the modified Givens rotation matrix to vector _x_ and _y_.

* [cuBLAS rotmg](Level-1/rotmg/)

    The sample applies the modified Givens rotation matrix to vector _x_ and _y_.

* [cuBLAS scal](Level-1/scal/)

    The sample computes the product of a vector by a scalar.

* [cuBLAS swap](Level-1/swap/)

    The sample interchanges the elements of vector _x_ and _y_.

##### cuBLAS Level 2

* [cuBLAS gbmv](Level-2/gbmv/)

    The sample performs a banded matrix-vector multiplication.

* [cuBLAS gemv](Level-2/gemv/)

    The sample performs a matrix-vector multiplication.

* [cuBLAS ger](Level-2/ger/)

    The sample performs a rank-1 update .

* [cuBLAS sbmv](Level-2/sbmv/)

    The sample performs a symmetric banded matrix-vector multiplication.

* [cuBLAS spmv](Level-2/spmv/)

    The sample performs a performs the symmetric packed matrix-vector multiplication.

* [cuBLAS spr](Level-2/spr/)

    The sample performs a packed symmetric rank-1 update.

* [cuBLAS spr2](Level-2/spr2/)

    The sample performs a packed symmetric rank-2 update.

* [cuBLAS symv](Level-2/symv/)

    The sample performs a symmetric matrix-vector multiplication.

* [cuBLAS syr](Level-2/syr/)

    The sample performs a symmetric rank-1 update.

* [cuBLAS syr2](Level-2/syr2/)

    The sample performs a symmetric rank-2 update.

* [cuBLAS tbmv](Level-2/tbmv/)

    The sample performs a triangular banded matrix-vector multiplication.

* [cuBLAS tbsv](Level-2/tbsv/)

    The sample solves a triangular banded linear system with a single right-hand-side.

* [cuBLAS tpmv](Level-2/tpmv/)

    The sample performs a triangular packed matrix-vector multiplication.

* [cuBLAS tpsv](Level-2/tpsv/)

    The sample solves a packed triangular linear system with a single right-hand-side.

* [cuBLAS trmv](Level-2/trmv/)

    The sample performs a triangular matrix-vector multiplication.

* [cuBLAS trsv](Level-2/trsv/)

    The sample solves a triangular linear system with a single right-hand-side.

* [cuBLAS hemv](Level-2/hemv/)

    The sample performs a Hermitian matrix-vector multiplication.

* [cuBLAS hbmv](Level-2/hbmv/)

    The sample performs a Hermitian banded matrix-vector multiplication.

* [cuBLAS hpmv](Level-2/hpmv/)

    The sample performs a Hermitian packed matrix-vector multiplication.

* [cuBLAS her](Level-2/her/)

    The sample performs a Hermitian rank-1 update.

* [cuBLAS her2](Level-2/her2/)

    The sample performs a Hermitian rank-2 update.

* [cuBLAS hpr](Level-2/hpr/)

    The sample performs a packed Hermitian rank-1 update.

* [cuBLAS hpr2](Level-2/hpr2/)

    The sample performs a packed Hermitian rank-2 update.

##### cuBLAS Level 3

* [cuBLAS gemm](Level-3/gemm/)

    The sample computes a matrix-matrix product with general matrices.

* [cuBLAS gemm3m](Level-3/gemm3m/)

    The sample computes matrix-matrix product with general matrices, using the Gauss complexity reduction algorithm.

* [cuBLAS gemmBatched](Level-3/gemmBatched/)

    The sample computes batches of matrix-matrix product with general matrices.

* [cuBLAS gemmStridedBatched](Level-3/gemmStridedBatched/)

    The sample computes strided batches of matrix-matrix product with general matrices.

* [cuBLAS hemm](Level-3/hemm/)

    The sample computes a Hermitian matrix-matrix product.

* [cuBLAS herk](Level-3/herk/)

    The sample computes a Hermitian rank-k update.

* [cuBLAS her2k](Level-3/her2k/)

    The sample computes a Hermitian rank-2k update.

* [cuBLAS herkx](Level-3/herkx/)

    The sample computes a variation of Hermitian rank-2k update.

* [cuBLAS symm](Level-3/symm/)

    The sample computes a symmetric matrix-matrix product.

* [cuBLAS syrk](Level-3/syrk/)

    The sample computes a symmetric rank-k update.

* [cuBLAS syrk](Level-3/syr2k/)

    The sample computes a symmetric rank-2k update.

* [cuBLAS syrk](Level-3/syrkx/)

    The sample computes a variation of symmetric rank-2k update.

* [cuBLAS trmm](Level-3/trmm/)

    The sample computes a triangular matrix-matrix product.

* [cuBLAS trsm](Level-3/trsm/)

    The sample computes a triangular linear system with multiple right-hand-sides.

* [cuBLAS trsmBatched](Level-3/trsmBatched/)

    The sample computes batched triangular linear systems with multiple right-hand-sides.

##### cuBLAS Extensions

* [cuBLAS geam](Extensions/geam/)

    The sample computes a matrix-matrix addition/transposition.

* [cuBLAS dgmm](Extensions/dgmm/)

    The sample computes a matrix-matrix multiplication.

* [cuBLAS tpttr](Extensions/tpttr/)

    The sample computes a conversion from the triangular packed format to the triangular format.

* [cuBLAS trttp](Extensions/trttp/)

    The sample computes a conversion from the triangular format to the triangular packed format.

* [cuBLAS AxpyEx](Extensions/AxpyEx/)

    The sample computes a vector-scalar product and adds the result to a vector.

* [cuBLAS Cherk3mEx](Extensions/Cherk3mEx/)

    The sample computes a Hermitian rank-k update, using the Gauss complexity reduction algorithm.

* [cuBLAS CherkEx](Extensions/CherkEx/)

    The sample computes a Hermitian rank-k update.

* [cuBLAS Csyrk3mEx](Extensions/Csyrk3mEx/)

    The sample computes a symmetric rank-k update, using the Gauss complexity reduction algorithm.

* [cuBLAS CsyrkEx](Extensions/CsyrkEx/)

    The sample computes a symmetric rank-k update.

* [cuBLAS DotEx](Extensions/DotEx/)

    The sample applies the dot product to vector _x_ and _y_.

* [cuBLAS GemmEx](Extensions/GemmEx/)

    The sample computes a matrix-matrix product with general matrices.

* [cuBLAS GemmBatchedEx](Extensions/GemmBatchedEx/)

    The sample computes batches of matrix-matrix product with general matrices.

* [cuBLAS GemmStridedBatchedEx](Extensions/GemmStridedBatchedEx/)

    The sample computes strided batches of matrix-matrix product with general matrices.

* [cuBLAS Nrm2Ex](Extensions/Nrm2Ex/)

    The sample computes the Euclidean norm of a vector.

* [cuBLAS RotEx](Extensions/RotEx/)

    The sample applies the Givens rotation matrix to vector _x_ and _y_.

* [cuBLAS ScalEx](Extensions/ScalEx/)

    The sample computes the product of a vector by a scalar.

<!-- ROCM-MIGRATION:START -->
## ROCm 支持情况

82 个独立源入口；PASSED 72，PARTIAL 0，FAILED 10，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：hipBLAS, rocBLAS。候选不等于已使用；基础探针成功也不等于整库迁移成功。

常规运算与第二批索引/旋转/batch 已验收；rotmg 原生重复缩放错误由项目 HIP GPU 修正。Emulation、3m、部分 Ex/packed 转换仍有接口/算法改写缺口。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu](Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu:125:45: error: use of undeclared identifier 'CUBLAS_EMULATION_STRATEGY_EAGER'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu:129:45: error: use of undeclared identifier 'CUBLAS_COMPUTE_32F_EMULATED_16BFX9' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Emulation_bf16x9_gemmEx_cublas_GemmEx_example.cu) |
| [Emulation/bf16x9_sgemm/cublas_sgemm_example.cu](Emulation/bf16x9_sgemm/cublas_sgemm_example.cu) · [详情](../migration/sample-reports/cuBLAS/Emulation/bf16x9_sgemm/cublas_sgemm_example.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/bf16x9_sgemm/cublas_sgemm_example.cu:119:37: error: use of undeclared identifier 'HIPBLAS_FP32_EMULATED_BF16X9_MATH'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/bf16x9_sgemm/cublas_sgemm_example.cu:126:45: error: use of undeclared identifier 'CUBLAS_EMULATION_STRATEGY_EAGER' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Emulation_bf16x9_sgemm_cublas_sgemm_example.cu)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Emulation_bf16x9_sgemm_cublas_sgemm_example.cu) |
| [Emulation/dgemm_dynamic/cublas_dgemm_dynamic_example.cu](Emulation/dgemm_dynamic/cublas_dgemm_dynamic_example.cu) · [详情](../migration/sample-reports/cuBLAS/Emulation/dgemm_dynamic/cublas_dgemm_dynamic_example.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/dgemm_dynamic/cublas_dgemm_dynamic_example.cu:55:5: error: unknown type name 'cudaEmulationMantissaControl_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/dgemm_dynamic/cublas_dgemm_dynamic_example.cu:55:47: error: use of undeclared identifier 'CUDA_EMULATION_MANTISSA_CONTROL_DYNAMIC' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Emulation_dgemm_dynamic_cublas_dgemm_dynamic_example.cu)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Emulation_dgemm_dynamic_cublas_dgemm_dynamic_example.cu) |
| [Emulation/dgemm_fixed/cublas_dgemm_fixed_example.cu](Emulation/dgemm_fixed/cublas_dgemm_fixed_example.cu) · [详情](../migration/sample-reports/cuBLAS/Emulation/dgemm_fixed/cublas_dgemm_fixed_example.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/dgemm_fixed/cublas_dgemm_fixed_example.cu:54:5: error: unknown type name 'cudaEmulationMantissaControl_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/dgemm_fixed/cublas_dgemm_fixed_example.cu:54:47: error: use of undeclared identifier 'CUDA_EMULATION_MANTISSA_CONTROL_FIXED' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Emulation_dgemm_fixed_cublas_dgemm_fixed_example.cu)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Emulation_dgemm_fixed_cublas_dgemm_fixed_example.cu) |
| [Emulation/gemmEx_dynamic/cublas_gemmEx_dynamic_example.cu](Emulation/gemmEx_dynamic/cublas_gemmEx_dynamic_example.cu) · [详情](../migration/sample-reports/cuBLAS/Emulation/gemmEx_dynamic/cublas_gemmEx_dynamic_example.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/gemmEx_dynamic/cublas_gemmEx_dynamic_example.cu:55:5: error: unknown type name 'cudaEmulationMantissaControl_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/gemmEx_dynamic/cublas_gemmEx_dynamic_example.cu:55:47: error: use of undeclared identifier 'CUDA_EMULATION_MANTISSA_CONTROL_DYNAMIC' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Emulation_gemmEx_dynamic_cublas_gemmEx_dynamic_example.cu)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Emulation_gemmEx_dynamic_cublas_gemmEx_dynamic_example.cu) |
| [Emulation/gemmEx_fixed/cublas_gemmEx_fixed_example.cu](Emulation/gemmEx_fixed/cublas_gemmEx_fixed_example.cu) · [详情](../migration/sample-reports/cuBLAS/Emulation/gemmEx_fixed/cublas_gemmEx_fixed_example.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/gemmEx_fixed/cublas_gemmEx_fixed_example.cu:54:5: error: unknown type name 'cudaEmulationMantissaControl_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/gemmEx_fixed/cublas_gemmEx_fixed_example.cu:54:47: error: use of undeclared identifier 'CUDA_EMULATION_MANTISSA_CONTROL_FIXED' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Emulation_gemmEx_fixed_cublas_gemmEx_fixed_example.cu)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Emulation_gemmEx_fixed_cublas_gemmEx_fixed_example.cu) |
| [Emulation/gemm_grading/grade_blas3.cpp](Emulation/gemm_grading/grade_blas3.cpp) · [详情](../migration/sample-reports/cuBLAS/Emulation/gemm_grading/grade_blas3.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/gemm_grading/grade_blas3.cpp:29:10: fatal error: 'utils.hxx' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Emulation_gemm_grading_grade_blas3.cpp)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Emulation_gemm_grading_grade_blas3.cpp) |
| [Emulation/gemm_grading/test_blas3.cpp](Emulation/gemm_grading/test_blas3.cpp) · [详情](../migration/sample-reports/cuBLAS/Emulation/gemm_grading/test_blas3.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/gemm_grading/test_blas3.cpp:28:10: fatal error: 'utils.hxx' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Emulation_gemm_grading_test_blas3.cpp)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Emulation_gemm_grading_test_blas3.cpp) |
| [Emulation/zgemm_dynamic/cublas_zgemm_dynamic_example.cu](Emulation/zgemm_dynamic/cublas_zgemm_dynamic_example.cu) · [详情](../migration/sample-reports/cuBLAS/Emulation/zgemm_dynamic/cublas_zgemm_dynamic_example.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/zgemm_dynamic/cublas_zgemm_dynamic_example.cu:55:5: error: unknown type name 'cudaEmulationMantissaControl_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/zgemm_dynamic/cublas_zgemm_dynamic_example.cu:55:47: error: use of undeclared identifier 'CUDA_EMULATION_MANTISSA_CONTROL_DYNAMIC' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Emulation_zgemm_dynamic_cublas_zgemm_dynamic_example.cu)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Emulation_zgemm_dynamic_cublas_zgemm_dynamic_example.cu) |
| [Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu](Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu) · [详情](../migration/sample-reports/cuBLAS/Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu:54:5: error: unknown type name 'cudaEmulationMantissaControl_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu:54:47: error: use of undeclared identifier 'CUDA_EMULATION_MANTISSA_CONTROL_FIXED' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Emulation_zgemm_fixed_cublas_zgemm_fixed_example.cu) |
| [Extensions/AxpyEx/cublas_AxpyEx_example.cu](Extensions/AxpyEx/cublas_AxpyEx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/AxpyEx/cublas_AxpyEx_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Extensions_AxpyEx_cublas_AxpyEx_example.cu) |
| [Extensions/Cherk3mEx/cublas_Cherk3mEx_example.cu](Extensions/Cherk3mEx/cublas_Cherk3mEx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/Cherk3mEx/cublas_Cherk3mEx_example.cu.md) | hipBLAS/rocBLAS three real SGEMMs + HIP Hermitian triangle epilogue / rocBLAS | L4 / PASSED | 原始数据/精度/布局与登记扩展用例通过 AMD、独立 CPU、相同输入 CUDA 验收；真实执行语义、反向检查及独立复审完成。实际路线：hipBLAS/rocBLAS three real SGEMMs + HIP Hermitian triangle epilogue。性能未验收。 | PASSED / PASSED | [记录](../migration/reports/rewrite-first-negative.json)；[记录](../migration/reports/rewrite-evidence-errata.json) |
| [Extensions/CherkEx/cublas_CherkEx_example.cu](Extensions/CherkEx/cublas_CherkEx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/CherkEx/cublas_CherkEx_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS / rocBLAS 保留原始 profile 与数学 API；4 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 原始固定complex32使用类型化hipBLAS Cherk/Csyrk保留dtype和数学方程；原生Ex包装失败另存。 | PASSED / PASSED | [记录](../migration/reports/b4-native-ex-failure.json)；[记录](../migration/reports/evidence/20261110T023758.405542Z/batches4_8-cuda/cuBLAS_Extensions_CherkEx_cublas_CherkEx_example.cu) |
| [Extensions/Csyrk3mEx/cublas_Csyrk3mEx_example.cu](Extensions/Csyrk3mEx/cublas_Csyrk3mEx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/Csyrk3mEx/cublas_Csyrk3mEx_example.cu.md) | hipBLAS/rocBLAS three real SGEMMs + HIP symmetric triangle epilogue / rocBLAS | L4 / PASSED | 原始数据/精度/布局与登记扩展用例通过 AMD、独立 CPU、相同输入 CUDA 验收；真实执行语义、反向检查及独立复审完成。实际路线：hipBLAS/rocBLAS three real SGEMMs + HIP symmetric triangle epilogue。性能未验收。 | PASSED / PASSED | [记录](../migration/reports/rewrite-first-negative.json)；[记录](../migration/reports/rewrite-evidence-errata.json) |
| [Extensions/CsyrkEx/cublas_CsyrkEx_example.cu](Extensions/CsyrkEx/cublas_CsyrkEx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/CsyrkEx/cublas_CsyrkEx_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS / rocBLAS 保留原始 profile 与数学 API；4 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 原始固定complex32使用类型化hipBLAS Cherk/Csyrk保留dtype和数学方程；原生Ex包装失败另存。 | PASSED / PASSED | [记录](../migration/reports/b4-native-ex-failure.json)；[记录](../migration/reports/evidence/20261110T023758.405542Z/batches4_8-cuda/cuBLAS_Extensions_CsyrkEx_cublas_CsyrkEx_example.cu) |
| [Extensions/DotEx/cublas_DotEx_example.cu](Extensions/DotEx/cublas_DotEx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/DotEx/cublas_DotEx_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Extensions_DotEx_cublas_DotEx_example.cu) |
| [Extensions/DotEx/cublas_DotcEx_example.cu](Extensions/DotEx/cublas_DotcEx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/DotEx/cublas_DotcEx_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Extensions_DotEx_cublas_DotcEx_example.cu) |
| [Extensions/GemmBatchedEx/cublas_GemmBatchedEx_example.cu](Extensions/GemmBatchedEx/cublas_GemmBatchedEx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/GemmBatchedEx/cublas_GemmBatchedEx_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS / rocBLAS 保留原始 profile 与数学 API；4 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261110T024002.087060Z/batches4_8-cuda/cuBLAS_Extensions_GemmBatchedEx_cublas_GemmBatchedEx_example.cu)；[记录](../migration/reports/evidence/20261110T024002.087060Z/batches4_8-cuda/cuBLAS_Extensions_GemmBatchedEx_cublas_GemmBatchedEx_example.cu) |
| [Extensions/GemmEx/cublas_GemmEx_example.cu](Extensions/GemmEx/cublas_GemmEx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/GemmEx/cublas_GemmEx_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS（rocBLAS）成功实现原始 profile 和 5 个数值用例，并通过 CUDA 对照 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Extensions_GemmEx_cublas_GemmEx_example.cu) |
| [Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu](Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu.md) | hipBLAS + project search/group dispatch / rocBLAS | L4 / PASSED | 使用 hipBLAS + project search/group dispatch，保持原始dtype/规模，全部候选完整输出、所选方案重放及workspace限制通过CPU/CUDA。分组为项目分发适配；搜索ID仅在对应后端有效，不跨库照搬CUDA算法ID；共享GPU计时不计性能资格。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261110T032310.748567Z/batches4_8-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu)；[记录](../migration/reports/evidence/20261110T032104.369797Z/batches4_8-cuda/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu) |
| [Extensions/GemmGroupedBatchedEx/cublas_GemmGroupedBatchedEx_example.cu](Extensions/GemmGroupedBatchedEx/cublas_GemmGroupedBatchedEx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/GemmGroupedBatchedEx/cublas_GemmGroupedBatchedEx_example.cu.md) | hipBLAS + project search/group dispatch / rocBLAS | L4 / PASSED | 使用 hipBLAS + project search/group dispatch，保持原始dtype/规模，全部候选完整输出、所选方案重放及workspace限制通过CPU/CUDA。分组为项目分发适配；搜索ID仅在对应后端有效，不跨库照搬CUDA算法ID；共享GPU计时不计性能资格。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261110T032310.748567Z/batches4_8-rocm/cuBLAS_Extensions_GemmGroupedBatchedEx_cublas_GemmGroupedBatchedEx_example.cu)；[记录](../migration/reports/evidence/20261110T032104.369797Z/batches4_8-cuda/cuBLAS_Extensions_GemmGroupedBatchedEx_cublas_GemmGroupedBatchedEx_example.cu) |
| [Extensions/GemmStridedBatchedEx/cublas_GemmStridedBatchedEx_example.cu](Extensions/GemmStridedBatchedEx/cublas_GemmStridedBatchedEx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/GemmStridedBatchedEx/cublas_GemmStridedBatchedEx_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Extensions_GemmStridedBatchedEx_cublas_GemmStridedBatchedEx_example.cu) |
| [Extensions/Nrm2Ex/cublas_Nrm2Ex_example.cu](Extensions/Nrm2Ex/cublas_Nrm2Ex_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/Nrm2Ex/cublas_Nrm2Ex_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Extensions_Nrm2Ex_cublas_Nrm2Ex_example.cu) |
| [Extensions/RotEx/cublas_RotEx_example.cu](Extensions/RotEx/cublas_RotEx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/RotEx/cublas_RotEx_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Extensions_RotEx_cublas_RotEx_example.cu) |
| [Extensions/ScalEx/cublas_ScalEx_example.cu](Extensions/ScalEx/cublas_ScalEx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/ScalEx/cublas_ScalEx_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Extensions_ScalEx_cublas_ScalEx_example.cu) |
| [Extensions/dgmm/cublas_dgmm_example.cu](Extensions/dgmm/cublas_dgmm_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/dgmm/cublas_dgmm_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Extensions_dgmm_cublas_dgmm_example.cu) |
| [Extensions/geam/cublas_geam_example.cu](Extensions/geam/cublas_geam_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/geam/cublas_geam_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Extensions_geam_cublas_geam_example.cu) |
| [Extensions/tpttr/cublas_tpttr_example.cu](Extensions/tpttr/cublas_tpttr_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/tpttr/cublas_tpttr_example.cu.md) | HIP GPU packed conversion / HIP runtime | L4 / PASSED | 使用 HIP GPU packed conversion / HIP runtime 保留原始dtype/布局与数学运算；4 个预登记输入case通过独立CPU与同输入CUDA，GPU适配和数值路径均已检查。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261110T023758.405542Z/batches4_8-cuda/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu)；[记录](../migration/reports/evidence/20261110T023758.405542Z/batches4_8-cuda/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu) |
| [Extensions/trttp/cublas_trttp_example.cu](Extensions/trttp/cublas_trttp_example.cu) · [详情](../migration/sample-reports/cuBLAS/Extensions/trttp/cublas_trttp_example.cu.md) | HIP GPU packed conversion / HIP runtime | L4 / PASSED | 使用 HIP GPU packed conversion / HIP runtime 保留原始dtype/布局与数学运算；4 个预登记输入case通过独立CPU与同输入CUDA，GPU适配和数值路径均已检查。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261110T023758.405542Z/batches4_8-cuda/cuBLAS_Extensions_trttp_cublas_trttp_example.cu)；[记录](../migration/reports/evidence/20261110T023758.405542Z/batches4_8-cuda/cuBLAS_Extensions_trttp_cublas_trttp_example.cu) |
| [Level-1/amax/cublas_amax_example.cu](Level-1/amax/cublas_amax_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-1/amax/cublas_amax_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS / rocBLAS 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T115427.847741Z/batch2-cuda/cuBLAS_Level-1_amax_cublas_amax_example.cu) |
| [Level-1/amin/cublas_amin_example.cu](Level-1/amin/cublas_amin_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-1/amin/cublas_amin_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS / rocBLAS 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T115427.847741Z/batch2-cuda/cuBLAS_Level-1_amin_cublas_amin_example.cu) |
| [Level-1/asum/cublas_asum_example.cu](Level-1/asum/cublas_asum_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-1/asum/cublas_asum_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-1_asum_cublas_asum_example.cu) |
| [Level-1/axpy/cublas_axpy_example.cu](Level-1/axpy/cublas_axpy_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-1/axpy/cublas_axpy_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS（rocBLAS）成功实现原始 profile 和 5 个数值用例，并通过 CUDA 对照 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-1_axpy_cublas_axpy_example.cu) |
| [Level-1/copy/cublas_copy_example.cu](Level-1/copy/cublas_copy_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-1/copy/cublas_copy_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-1_copy_cublas_copy_example.cu) |
| [Level-1/dot/cublas_dot_example.cu](Level-1/dot/cublas_dot_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-1/dot/cublas_dot_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS（rocBLAS）成功实现原始 profile 和 9 个数值用例，并通过 CUDA 对照 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-1_dot_cublas_dot_example.cu) |
| [Level-1/dot/cublas_dotc_example.cu](Level-1/dot/cublas_dotc_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-1/dot/cublas_dotc_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-1_dot_cublas_dotc_example.cu) |
| [Level-1/nrm2/cublas_nrm2_example.cu](Level-1/nrm2/cublas_nrm2_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-1/nrm2/cublas_nrm2_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-1_nrm2_cublas_nrm2_example.cu) |
| [Level-1/rot/cublas_rot_example.cu](Level-1/rot/cublas_rot_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-1/rot/cublas_rot_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-1_rot_cublas_rot_example.cu) |
| [Level-1/rotg/cublas_rotg_example.cu](Level-1/rotg/cublas_rotg_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-1/rotg/cublas_rotg_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS / rocBLAS 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T115141.126114Z/batch2-cuda/cuBLAS_Level-1_rotg_cublas_rotg_example.cu) |
| [Level-1/rotm/cublas_rotm_example.cu](Level-1/rotm/cublas_rotm_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-1/rotm/cublas_rotm_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS / rocBLAS 保留原始 profile 与数学 API；4 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T115141.126114Z/batch2-cuda/cuBLAS_Level-1_rotm_cublas_rotm_example.cu) |
| [Level-1/rotmg/cublas_rotmg_example.cu](Level-1/rotmg/cublas_rotmg_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-1/rotmg/cublas_rotmg_example.cu.md) | hipBLAS + HIP scale fix / rocBLAS | L4 / PASSED | 使用 hipBLAS / rocBLAS 保留原始 profile 与数学 API；6 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。原生重复缩放的 H 参数错误由项目 GPU kernel 修正；原生失败证据单独保留。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T120619.802852Z/batch2-rocm/cuBLAS_Level-1_rotmg_cublas_rotmg_example.cu)；[记录](../migration/reports/rotmg-native-rescale-failure.json) |
| [Level-1/scal/cublas_scal_example.cu](Level-1/scal/cublas_scal_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-1/scal/cublas_scal_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-1_scal_cublas_scal_example.cu) |
| [Level-1/swap/cublas_swap_example.cu](Level-1/swap/cublas_swap_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-1/swap/cublas_swap_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-1_swap_cublas_swap_example.cu) |
| [Level-2/gbmv/cublas_gbmv_example.cu](Level-2/gbmv/cublas_gbmv_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/gbmv/cublas_gbmv_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_gbmv_cublas_gbmv_example.cu) |
| [Level-2/gemv/cublas_gemv_example.cu](Level-2/gemv/cublas_gemv_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/gemv/cublas_gemv_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS（rocBLAS）成功实现原始 profile 和 5 个数值用例，并通过 CUDA 对照 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_gemv_cublas_gemv_example.cu) |
| [Level-2/ger/cublas_ger_example.cu](Level-2/ger/cublas_ger_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/ger/cublas_ger_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_ger_cublas_ger_example.cu) |
| [Level-2/hbmv/cublas_hbmv_example.cu](Level-2/hbmv/cublas_hbmv_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/hbmv/cublas_hbmv_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_hbmv_cublas_hbmv_example.cu) |
| [Level-2/hemv/cublas_hemv_example.cu](Level-2/hemv/cublas_hemv_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/hemv/cublas_hemv_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_hemv_cublas_hemv_example.cu) |
| [Level-2/her2/cublas_her2_example.cu](Level-2/her2/cublas_her2_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/her2/cublas_her2_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_her2_cublas_her2_example.cu) |
| [Level-2/her/cublas_her_example.cu](Level-2/her/cublas_her_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/her/cublas_her_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_her_cublas_her_example.cu) |
| [Level-2/hpmv/cublas_hpmv_example.cu](Level-2/hpmv/cublas_hpmv_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/hpmv/cublas_hpmv_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_hpmv_cublas_hpmv_example.cu) |
| [Level-2/hpr2/cublas_hpr2_example.cu](Level-2/hpr2/cublas_hpr2_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/hpr2/cublas_hpr2_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_hpr2_cublas_hpr2_example.cu) |
| [Level-2/hpr/cublas_hpr_example.cu](Level-2/hpr/cublas_hpr_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/hpr/cublas_hpr_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_hpr_cublas_hpr_example.cu) |
| [Level-2/sbmv/cublas_sbmv_example.cu](Level-2/sbmv/cublas_sbmv_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/sbmv/cublas_sbmv_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_sbmv_cublas_sbmv_example.cu) |
| [Level-2/spmv/cublas_spmv_example.cu](Level-2/spmv/cublas_spmv_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/spmv/cublas_spmv_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_spmv_cublas_spmv_example.cu) |
| [Level-2/spr2/cublas_spr2_example.cu](Level-2/spr2/cublas_spr2_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/spr2/cublas_spr2_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_spr2_cublas_spr2_example.cu) |
| [Level-2/spr/cublas_spr_example.cu](Level-2/spr/cublas_spr_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/spr/cublas_spr_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_spr_cublas_spr_example.cu) |
| [Level-2/symv/cublas_symv_example.cu](Level-2/symv/cublas_symv_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/symv/cublas_symv_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_symv_cublas_symv_example.cu) |
| [Level-2/syr2/cublas_syr2_example.cu](Level-2/syr2/cublas_syr2_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/syr2/cublas_syr2_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_syr2_cublas_syr2_example.cu) |
| [Level-2/syr/cublas_syr_example.cu](Level-2/syr/cublas_syr_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/syr/cublas_syr_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_syr_cublas_syr_example.cu) |
| [Level-2/tbmv/cublas_tbmv_example.cu](Level-2/tbmv/cublas_tbmv_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/tbmv/cublas_tbmv_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_tbmv_cublas_tbmv_example.cu) |
| [Level-2/tbsv/cublas_tbsv_example.cu](Level-2/tbsv/cublas_tbsv_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/tbsv/cublas_tbsv_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_tbsv_cublas_tbsv_example.cu) |
| [Level-2/tpmv/cublas_tpmv_example.cu](Level-2/tpmv/cublas_tpmv_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/tpmv/cublas_tpmv_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_tpmv_cublas_tpmv_example.cu) |
| [Level-2/tpsv/cublas_tpsv_example.cu](Level-2/tpsv/cublas_tpsv_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/tpsv/cublas_tpsv_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_tpsv_cublas_tpsv_example.cu) |
| [Level-2/trmv/cublas_trmv_example.cu](Level-2/trmv/cublas_trmv_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/trmv/cublas_trmv_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_trmv_cublas_trmv_example.cu) |
| [Level-2/trsv/cublas_trsv_example.cu](Level-2/trsv/cublas_trsv_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-2/trsv/cublas_trsv_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-2_trsv_cublas_trsv_example.cu) |
| [Level-3/gemm3m/cublas_gemm3m_example.cu](Level-3/gemm3m/cublas_gemm3m_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/gemm3m/cublas_gemm3m_example.cu.md) | hipBLAS/rocBLAS three real SGEMMs + HIP complex split/merge / rocBLAS | L4 / PASSED | 原始数据/精度/布局与登记扩展用例通过 AMD、独立 CPU、相同输入 CUDA 验收；真实执行语义、反向检查及独立复审完成。实际路线：hipBLAS/rocBLAS three real SGEMMs + HIP complex split/merge。性能未验收。 | PASSED / PASSED | [记录](../migration/reports/rewrite-first-negative.json)；[记录](../migration/reports/rewrite-evidence-errata.json) |
| [Level-3/gemm/cublas_gemm_example.cu](Level-3/gemm/cublas_gemm_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/gemm/cublas_gemm_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS（rocBLAS）成功实现原始 profile 和 5 个数值用例，并通过 CUDA 对照 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_gemm_cublas_gemm_example.cu) |
| [Level-3/gemmBatched/cublas_gemmBatched_example.cu](Level-3/gemmBatched/cublas_gemmBatched_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/gemmBatched/cublas_gemmBatched_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS / rocBLAS 保留原始 profile 与数学 API；2 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T115141.126114Z/batch2-cuda/cuBLAS_Level-3_gemmBatched_cublas_gemmBatched_example.cu) |
| [Level-3/gemmGroupedBatched/cublas_gemmGroupedBatched_example.cu](Level-3/gemmGroupedBatched/cublas_gemmGroupedBatched_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/gemmGroupedBatched/cublas_gemmGroupedBatched_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS / rocBLAS 保留原始 profile 与数学 API；2 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T115141.126114Z/batch2-cuda/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu) |
| [Level-3/gemmStridedBatched/cublas_gemmStridedBatched_example.cu](Level-3/gemmStridedBatched/cublas_gemmStridedBatched_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/gemmStridedBatched/cublas_gemmStridedBatched_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS（rocBLAS）成功实现原始 profile 和 5 个数值用例，并通过 CUDA 对照 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_gemmStridedBatched_cublas_gemmStridedBatched_example.cu) |
| [Level-3/hemm/cublas_hemm_example.cu](Level-3/hemm/cublas_hemm_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/hemm/cublas_hemm_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_hemm_cublas_hemm_example.cu) |
| [Level-3/her2k/cublas_her2k_example.cu](Level-3/her2k/cublas_her2k_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/her2k/cublas_her2k_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_her2k_cublas_her2k_example.cu) |
| [Level-3/herk/cublas_herk_example.cu](Level-3/herk/cublas_herk_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/herk/cublas_herk_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_herk_cublas_herk_example.cu) |
| [Level-3/herkx/cublas_herkx_example.cu](Level-3/herkx/cublas_herkx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/herkx/cublas_herkx_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_herkx_cublas_herkx_example.cu) |
| [Level-3/symm/cublas_symm_example.cu](Level-3/symm/cublas_symm_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/symm/cublas_symm_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_symm_cublas_symm_example.cu) |
| [Level-3/syr2k/cublas_syr2k_example.cu](Level-3/syr2k/cublas_syr2k_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/syr2k/cublas_syr2k_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_syr2k_cublas_syr2k_example.cu) |
| [Level-3/syrk/cublas_syrk_example.cu](Level-3/syrk/cublas_syrk_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/syrk/cublas_syrk_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_syrk_cublas_syrk_example.cu) |
| [Level-3/syrkx/cublas_syrkx_example.cu](Level-3/syrkx/cublas_syrkx_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/syrkx/cublas_syrkx_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_syrkx_cublas_syrkx_example.cu) |
| [Level-3/trmm/cublas_trmm_example.cu](Level-3/trmm/cublas_trmm_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/trmm/cublas_trmm_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_trmm_cublas_trmm_example.cu) |
| [Level-3/trsm/cublas_trsm_example.cu](Level-3/trsm/cublas_trsm_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/trsm/cublas_trsm_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。 | PASSED / PASSED | [记录](../migration/reports/blas-three-way.json)；[记录](../migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_trsm_cublas_trsm_example.cu) |
| [Level-3/trsmBatched/cublas_trsmBatched_example.cu](Level-3/trsmBatched/cublas_trsmBatched_example.cu) · [详情](../migration/sample-reports/cuBLAS/Level-3/trsmBatched/cublas_trsmBatched_example.cu.md) | hipBLAS / rocBLAS | L4 / PASSED | 使用 hipBLAS / rocBLAS 保留原始 profile 与数学 API；2 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T115141.126114Z/batch2-cuda/cuBLAS_Level-3_trsmBatched_cublas_trsmBatched_example.cu) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
