# cuSOLVER Library - APIs Examples

## Description

This folder demonstrates cuSOLVER APIs usage.

[cuSOLVER API Documentation](https://docs.nvidia.com/cuda/cusolver/index.html)

## cuSOLVER Samples

##### MutliGPU LU Decomposition example

* [cuSOLVER MgGetrs](MgGetrs/)

    The sample solves linear system by *LU Decomposition*, with partial pivoting (`getrf` and `getrs`). See example for detailed description.

##### MutliGPU Cholesky Decomposition example

* [cuSOLVER MgPotrf](MgPotrf/)

    The sample solves linear system by *Cholesky factorization* (`potrf` and `potrs`). See example for detailed description.

##### MutliGPU Symmetric Eigenvalue solver examples

* [cuSOLVER MgSyevd](MgSyevd/)

    The sample provides three examples to demonstrate *multiGPU standard symmetric eigenvalue* solver. See example for detailed description.

##### 64-bit Singular Value Decomposition example

* [cuSOLVER Xgesvd](Xgesvd/)

    The sample computes *singular value decomposition*, using 64-bit APIs. See example for detailed description.

##### 64-bit Singular Value + Polar Decomposition example

* [cuSOLVER Xgesvdp](Xgesvdp/)

    The sample computes *singular value decomposition*, in combination with polar decomposition, using 64-bit APIs. See example for detailed description.

##### 64-bit Rank-K Singular Value Decomposition example

* [cuSOLVER Xgesvdr](Xgesvdr/)

    The sample computes approximated rank-k *singular value decomposition*, using 64-bit APIs. See example for detailed description.

##### 64-bit LU Decomposition example

* [cuSOLVER Xgetrf](Xgetrf/)

    The sample solves linear system by *LU Decomposition*, with partial pivoting (`getrf` and `getrs`), using 64-bit APIs. See example for detailed description.

##### 64-bit Standard Symmetric Dense Eigenvalue solver example

* [cuSOLVER Xsyevd](Xsyevd/)

    The sample demonstrates *standard symmetric eigenvalue* solver, using 64-bit APIs. See example for detailed description.

##### 64-bit Standard Symmetric Dense Eigenvalue solver example

* [cuSOLVER Xsyevdx](Xsyevdx/)

    The sample demonstrates *standard symmetric eigenvalue* solver, using 64-bit APIs. See example for detailed description.

##### Batched Sparse QR Factorizaion examples

* [cuSOLVER csrqr](csrqr/)

    The sample provides two examples to demonstrate batched *sparse qr factorization*. See example for detailed description.

##### Iterative Refinement solver example

* [cuSOLVER gesv](gesv/)

    The sample demonstrates *iterative refinement solver example* for solving linear systems with multiple right hand sides. See example for detailed description.

##### Singular Value Decomposition example

* [cuSOLVER gesvd](gesvd/)

    The sample computes *singular value decomposition*. See example for detailed description.

##### Singular Value Decomposition example

* [cuSOLVER gesvdaStridedBatched](gesvdaStridedBatched/)

    The sample computes a strided, batched approximate *singular value decomposition*. See example for detailed description.

##### Singular Value Decomposition (via Jacobi method) example

* [cuSOLVER gesvdj](gesvdj/)

    The sample computes *singular value decomposition*, via Jacobi method. See example for detailed description.

##### Batched Singular Value Decomposition (via Jacobi method) example

* [cuSOLVER gesvdjBatched](gesvdjBatched/)

    The sample computes batched *singular value decomposition*, via Jacobi method. See example for detailed description.

##### LU Decomposition example

* [cuSOLVER getrf](getrf/)

    The sample solves linear system by *LU Decomposition*, with partial pivoting (`getrf` and `getrs`). See example for detailed description.

##### Orthgonalization example

* [cuSOLVER orgqr](orgqr/)

    The sample computes complete *orthgonalization* (`geqrf` and `orgqr`). See example for detailed description.

##### QR Factorization example

* [cuSOLVER ormqr](ormqr/)

    The sample computes dense *QR orthgonalization* (`geqrf`, `ormqr`, and `trsm`). See example for detailed description.

##### Batched Cholesky Decomposition example

* [cuSOLVER potrfBatched](potrfBatched/)

    The sample solves linear system by *Cholesky factorization* (`potrfBatched` and `potrsBatched`). See example for detailed description.

##### Standard Symmetric Dense Eigenvalue solver example

* [cuSOLVER syevd](syevd/)

    The sample demonstrates *standard symmetric eigenvalue* solver. See example for detailed description.

##### Standard Symmetric Dense Eigenvalue solver (via Jacobi method) example

* [cuSOLVER syevj](syevj/)

    The sample demonstrates *standard symmetric eigenvalue* solver, via Jacobi method. See example for detailed description.

##### Batched Standard Symmetric Dense Eigenvaluesolver (via Jacobi method)  example

* [cuSOLVER syevjBatched](syevjBatched/)

    The sample demonstrates batched *standard symmetric eigenvalue* solver, via Jacobi method. See example for detailed description.

##### Generalized Symmetric-Definite Dense Eigenvalue solver example

* [cuSOLVER sygvd](sygvd/)

    The sample demonstrates *generalized symmetric-definite dense eigenvalue* solver. See example for detailed description.

##### Generalized Symmetric-Definite Dense Eigenvalue solver (via Jacobi method) example

* [cuSOLVER sygvj](sygvj/)

    The sample demonstrates *generalized symmetric-definite dense eigenvalue* solver, (via Jacobi method). See example for detailed description.

##### Triangular Matrix Inversion Computation example

* [cuSOLVER trtri](trtri/)

    The sample preforms *triangular matrix mnversion*. See example for detailed description.

<!-- ROCM-MIGRATION:START -->
## ROCm 迁移实时状态

39 个独立源入口；PASSED 17，PARTIAL 4，FAILED 18，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：hipSOLVER, rocSOLVER。候选不等于已使用；基础探针成功也不等于整库迁移成功。

基础分解、Xgeqrf/Xpotrf、gesvdjBatched、syevjBatched、syevdx/sygvdx 已验收；后四项检查逐batch重构/配对、meig与选区。Xgeev三例仍需排除CPU兼容路径，gesvdaStridedBatched仍需确认近似算法与残差语义，保留PARTIAL；Mg、IRS等其它入口缺AMD改写或oracle。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [MgGetrf/cusolver_MgGetrf_example.cu](MgGetrf/cusolver_MgGetrf_example.cu) · [详情](../migration/sample-reports/cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu:56:5: error: unknown type name 'cusolverMgHandle_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu:79:5: error: unknown type name 'cudaLibMgMatrixDesc_t' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu) |
| [MgPotrf/cusolver_MgPotrf_example1.cu](MgPotrf/cusolver_MgPotrf_example1.cu) · [详情](../migration/sample-reports/cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu:67:5: error: unknown type name 'cusolverMgHandle_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu:92:5: error: unknown type name 'cudaLibMgMatrixDesc_t' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu) |
| [MgPotrf/cusolver_MgPotrf_example2.cu](MgPotrf/cusolver_MgPotrf_example2.cu) · [详情](../migration/sample-reports/cuSOLVER/MgPotrf/cusolver_MgPotrf_example2.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgPotrf/cusolver_MgPotrf_example2.cu:97:5: error: unknown type name 'cusolverMgHandle_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgPotrf/cusolver_MgPotrf_example2.cu:118:5: error: unknown type name 'cudaLibMgMatrixDesc_t' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example2.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_MgPotrf_cusolver_MgPotrf_example2.cu) |
| [MgSyevd/cusolver_MgSyevd_example1.cu](MgSyevd/cusolver_MgSyevd_example1.cu) · [详情](../migration/sample-reports/cuSOLVER/MgSyevd/cusolver_MgSyevd_example1.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgSyevd/cusolver_MgSyevd_example1.cu:46:5: error: unknown type name 'cusolverMgHandle_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgSyevd/cusolver_MgSyevd_example1.cu:66:5: error: unknown type name 'cudaLibMgMatrixDesc_t' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_MgSyevd_cusolver_MgSyevd_example1.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_MgSyevd_cusolver_MgSyevd_example1.cu) |
| [MgSyevd/cusolver_MgSyevd_example2.cu](MgSyevd/cusolver_MgSyevd_example2.cu) · [详情](../migration/sample-reports/cuSOLVER/MgSyevd/cusolver_MgSyevd_example2.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgSyevd/cusolver_MgSyevd_example2.cu:46:5: error: unknown type name 'cusolverMgHandle_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgSyevd/cusolver_MgSyevd_example2.cu:66:5: error: unknown type name 'cudaLibMgMatrixDesc_t' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_MgSyevd_cusolver_MgSyevd_example2.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_MgSyevd_cusolver_MgSyevd_example2.cu) |
| [MgSyevd/cusolver_MgSyevd_example3.cu](MgSyevd/cusolver_MgSyevd_example3.cu) · [详情](../migration/sample-reports/cuSOLVER/MgSyevd/cusolver_MgSyevd_example3.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgSyevd/cusolver_MgSyevd_example3.cu:56:5: error: unknown type name 'cusolverMgHandle_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgSyevd/cusolver_MgSyevd_example3.cu:76:5: error: unknown type name 'cudaLibMgMatrixDesc_t' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_MgSyevd_cusolver_MgSyevd_example3.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_MgSyevd_cusolver_MgSyevd_example3.cu) |
| [Xgeev/cusolver_Xgeev_example1.cu](Xgeev/cusolver_Xgeev_example1.cu) · [详情](../migration/sample-reports/cuSOLVER/Xgeev/cusolver_Xgeev_example1.cu.md) | hipsolver / rocSOLVER | L3 / PARTIAL | 原始教学输入构建运行通过；独立正确性验证待完成 | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xgeev_cusolver_Xgeev_example1.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xgeev_cusolver_Xgeev_example1.cu) |
| [Xgeev/cusolver_Xgeev_example2.cu](Xgeev/cusolver_Xgeev_example2.cu) · [详情](../migration/sample-reports/cuSOLVER/Xgeev/cusolver_Xgeev_example2.cu.md) | hipsolver / rocSOLVER | L3 / PARTIAL | 原始教学输入构建运行通过；独立正确性验证待完成 | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xgeev_cusolver_Xgeev_example2.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xgeev_cusolver_Xgeev_example2.cu) |
| [Xgeev/cusolver_Xgeev_example3.cu](Xgeev/cusolver_Xgeev_example3.cu) · [详情](../migration/sample-reports/cuSOLVER/Xgeev/cusolver_Xgeev_example3.cu.md) | hipsolver / rocSOLVER | L3 / PARTIAL | 原始教学输入构建运行通过；独立正确性验证待完成 | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xgeev_cusolver_Xgeev_example3.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xgeev_cusolver_Xgeev_example3.cu) |
| [Xgeev/cusolver_Xgeev_example4.cu](Xgeev/cusolver_Xgeev_example4.cu) · [详情](../migration/sample-reports/cuSOLVER/Xgeev/cusolver_Xgeev_example4.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xgeev/cusolver_Xgeev_example4.cu:82:53: error: use of undeclared identifier 'CUSOLVERDN_GEEV' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xgeev_cusolver_Xgeev_example4.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xgeev_cusolver_Xgeev_example4.cu) |
| [Xgeqrf/cusolver_Xgeqrf_example.cu](Xgeqrf/cusolver_Xgeqrf_example.cu) · [详情](../migration/sample-reports/cuSOLVER/Xgeqrf/cusolver_Xgeqrf_example.cu.md) | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER + hipBLAS / rocSOLVER/rocBLAS 保留原始 profile 与数学 API；1 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T120648.693848Z/batch2-cuda/cuSOLVER_Xgeqrf_cusolver_Xgeqrf_example.cu) |
| [Xgesvd/cusolver_Xgesvd_example.cu](Xgesvd/cusolver_Xgesvd_example.cu) · [详情](../migration/sample-reports/cuSOLVER/Xgesvd/cusolver_Xgesvd_example.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xgesvd/cusolver_Xgesvd_example.cu:100:20: error: use of undeclared identifier 'cusolverDnXgesvd_bufferSize'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xgesvd/cusolver_Xgesvd_example.cu:132:20: error: use of undeclared identifier 'cusolverDnXgesvd' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xgesvd_cusolver_Xgesvd_example.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xgesvd_cusolver_Xgesvd_example.cu) |
| [Xgesvdp/cusolver_Xgesvdp_example.cu](Xgesvdp/cusolver_Xgesvdp_example.cu) · [详情](../migration/sample-reports/cuSOLVER/Xgesvdp/cusolver_Xgesvdp_example.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xgesvdp/cusolver_Xgesvdp_example.cu:104:20: error: use of undeclared identifier 'cusolverDnXgesvdp_bufferSize'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xgesvdp/cusolver_Xgesvdp_example.cu:125:20: error: use of undeclared identifier 'cusolverDnXgesvdp' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu) |
| [Xgesvdr/cusolver_Xgesvdr_example.cu](Xgesvdr/cusolver_Xgesvdr_example.cu) · [详情](../migration/sample-reports/cuSOLVER/Xgesvdr/cusolver_Xgesvdr_example.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xgesvdr/cusolver_Xgesvdr_example.cu:105:20: error: use of undeclared identifier 'cusolverDnXgesvdr_bufferSize'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xgesvdr/cusolver_Xgesvdr_example.cu:121:20: error: use of undeclared identifier 'cusolverDnXgesvdr' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xgesvdr_cusolver_Xgesvdr_example.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xgesvdr_cusolver_Xgesvdr_example.cu) |
| [Xgetrf/cusolver_Xgetrf_example.cu](Xgetrf/cusolver_Xgetrf_example.cu) · [详情](../migration/sample-reports/cuSOLVER/Xgetrf/cusolver_Xgetrf_example.cu.md) | hipsolver / rocSOLVER | L2 / FAILED | run 失败：terminate called after throwing an instance of 'std::runtime_error'   what():  hipsolver error  | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xgetrf_cusolver_Xgetrf_example.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xgetrf_cusolver_Xgetrf_example.cu) |
| [Xpotrf/cusolver_Xpotrf_example.cu](Xpotrf/cusolver_Xpotrf_example.cu) · [详情](../migration/sample-reports/cuSOLVER/Xpotrf/cusolver_Xpotrf_example.cu.md) | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER + hipBLAS / rocSOLVER/rocBLAS 保留原始 profile 与数学 API；1 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T120648.693848Z/batch2-cuda/cuSOLVER_Xpotrf_cusolver_Xpotrf_example.cu) |
| [Xsyevd/cusolver_Xsyevd_example.cu](Xsyevd/cusolver_Xsyevd_example.cu) · [详情](../migration/sample-reports/cuSOLVER/Xsyevd/cusolver_Xsyevd_example.cu.md) | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER/rocSOLVER 与 hipBLAS 保留原始固定教学矩阵；通过独立 NumPy/SciPy 特征值/奇异值、重构/残差和正交性检查，见逐项误差与阈值。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu)；[记录](../migration/reports/additional-comparison.json) |
| [Xsyevdx/cusolver_Xsyevdx_example.cu](Xsyevdx/cusolver_Xsyevdx_example.cu) · [详情](../migration/sample-reports/cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu:87:20: error: use of undeclared identifier 'cusolverDnXsyevdx_bufferSize'; did you mean 'hipsolverDnXgeev_bufferSize'?；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu:88:34: error: cannot initialize a parameter of type 'hipsolverEigMode_t' with an lvalue of type 'hipsolverEigRange_t' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu) |
| [Xtrtri/cusolver_Xtrtri_example.cu](Xtrtri/cusolver_Xtrtri_example.cu) · [详情](../migration/sample-reports/cuSOLVER/Xtrtri/cusolver_Xtrtri_example.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xtrtri/cusolver_Xtrtri_example.cu:38:24: error: use of undeclared identifier 'cusolverDnXtrtri_bufferSize'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xtrtri/cusolver_Xtrtri_example.cu:55:24: error: use of undeclared identifier 'cusolverDnXtrtri' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xtrtri_cusolver_Xtrtri_example.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xtrtri_cusolver_Xtrtri_example.cu) |
| [csrqr/cusolver_csrqr_example1.cu](csrqr/cusolver_csrqr_example1.cu) · [详情](../migration/sample-reports/cuSOLVER/csrqr/cusolver_csrqr_example1.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/csrqr/cusolver_csrqr_example1.cu:32:5: error: unknown type name 'csrqrInfo_t' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_csrqr_cusolver_csrqr_example1.cu) |
| [csrqr/cusolver_csrqr_example2.cu](csrqr/cusolver_csrqr_example2.cu) · [详情](../migration/sample-reports/cuSOLVER/csrqr/cusolver_csrqr_example2.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/csrqr/cusolver_csrqr_example2.cu:32:5: error: unknown type name 'csrqrInfo_t' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example2.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_csrqr_cusolver_csrqr_example2.cu) |
| [gesv/cusolver_irs_expert_cuda-10.2.cu](gesv/cusolver_irs_expert_cuda-10.2.cu) · [详情](../migration/sample-reports/cuSOLVER/gesv/cusolver_irs_expert_cuda-10.2.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/gesv/cusolver_irs_expert_cuda-10.2.cu:46:11: error: unknown type name 'cusolverIRSRefinement_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/gesv/cusolver_irs_expert_cuda-10.2.cu:46:55: error: use of undeclared identifier 'CUSOLVER_IRS_REFINE_GMRES' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_gesv_cusolver_irs_expert_cuda-10.2.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_gesv_cusolver_irs_expert_cuda-10.2.cu) |
| [gesv/cusolver_irs_expert_cuda-11.cu](gesv/cusolver_irs_expert_cuda-11.cu) · [详情](../migration/sample-reports/cuSOLVER/gesv/cusolver_irs_expert_cuda-11.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/gesv/cusolver_irs_expert_cuda-11.cu:40:11: error: unknown type name 'cusolverPrecType_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/gesv/cusolver_irs_expert_cuda-11.cu:40:49: error: use of undeclared identifier 'CUSOLVER_R_64F' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_gesv_cusolver_irs_expert_cuda-11.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_gesv_cusolver_irs_expert_cuda-11.cu) |
| [gesv/cusolver_irs_lapack.cu](gesv/cusolver_irs_lapack.cu) · [详情](../migration/sample-reports/cuSOLVER/gesv/cusolver_irs_lapack.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/gesv/cusolver_irs_lapack.cu:41:37: error: use of undeclared identifier 'cusolverDnDHgesv_bufferSize'; did you mean 'hipsolverDnDDgesv_bufferSize'?；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/gesv/cusolver_irs_lapack.cu:42:26: error: use of undeclared identifier 'cusolverDnDHgesv' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_gesv_cusolver_irs_lapack.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_gesv_cusolver_irs_lapack.cu) |
| [gesvd/cusolver_gesvd_example.cu](gesvd/cusolver_gesvd_example.cu) · [详情](../migration/sample-reports/cuSOLVER/gesvd/cusolver_gesvd_example.cu.md) | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER/rocSOLVER 与 hipBLAS 保留原始固定教学矩阵；通过独立 NumPy/SciPy 特征值/奇异值、重构/残差和正交性检查，见逐项误差与阈值。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_gesvd_cusolver_gesvd_example.cu)；[记录](../migration/reports/additional-comparison.json) |
| [gesvdaStridedBatched/cusolver_gesvdaStridedBatched_example.cu](gesvdaStridedBatched/cusolver_gesvdaStridedBatched_example.cu) · [详情](../migration/sample-reports/cuSOLVER/gesvdaStridedBatched/cusolver_gesvdaStridedBatched_example.cu.md) | hipsolver / rocSOLVER | L3 / PARTIAL | 原始教学输入构建运行通过；独立正确性验证待完成 | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu) |
| [gesvdj/cusolver_gesvdj_example.cu](gesvdj/cusolver_gesvdj_example.cu) · [详情](../migration/sample-reports/cuSOLVER/gesvdj/cusolver_gesvdj_example.cu.md) | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER/rocSOLVER 与 hipBLAS 保留原始固定教学矩阵；通过独立 NumPy/SciPy 特征值/奇异值、重构/残差和正交性检查，见逐项误差与阈值。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu)；[记录](../migration/reports/additional-comparison.json) |
| [gesvdjBatched/cusolver_gesvdjBatched_example.cu](gesvdjBatched/cusolver_gesvdjBatched_example.cu) · [详情](../migration/sample-reports/cuSOLVER/gesvdjBatched/cusolver_gesvdjBatched_example.cu.md) | hipSOLVER / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER / rocSOLVER/rocBLAS 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch3-validation.json)；[记录](../migration/reports/evidence/20261109T135901.256203Z/batch3-cuda/cuSOLVER_gesvdjBatched_cusolver_gesvdjBatched_example.cu) |
| [getrf/cusolver_getrf_example.cu](getrf/cusolver_getrf_example.cu) · [详情](../migration/sample-reports/cuSOLVER/getrf/cusolver_getrf_example.cu.md) | hipSOLVER / rocSOLVER | L4 / PASSED | 使用 hipSOLVER（rocSOLVER）成功实现原始 profile 和 6 个数值用例，并通过 CUDA 对照 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_getrf_cusolver_getrf_example.cu) |
| [orgqr/cusolver_orgqr_example.cu](orgqr/cusolver_orgqr_example.cu) · [详情](../migration/sample-reports/cuSOLVER/orgqr/cusolver_orgqr_example.cu.md) | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER/rocSOLVER 与 hipBLAS 保留原始固定教学矩阵；通过独立 NumPy/SciPy 特征值/奇异值、重构/残差和正交性检查，见逐项误差与阈值。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_orgqr_cusolver_orgqr_example.cu)；[记录](../migration/reports/additional-comparison.json) |
| [ormqr/cusolver_ormqr_example.cu](ormqr/cusolver_ormqr_example.cu) · [详情](../migration/sample-reports/cuSOLVER/ormqr/cusolver_ormqr_example.cu.md) | hipSOLVER / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER / rocSOLVER/rocBLAS 保留原始 profile 与数学 API；4 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batches4_8-validation.json)；[记录](../migration/reports/evidence/20261110T023758.405542Z/batches4_8-cuda/cuSOLVER_ormqr_cusolver_ormqr_example.cu) |
| [potrfBatched/cusolver_potrfBatched_example.cu](potrfBatched/cusolver_potrfBatched_example.cu) · [详情](../migration/sample-reports/cuSOLVER/potrfBatched/cusolver_potrfBatched_example.cu.md) | hipSOLVER / rocSOLVER | L4 / PASSED | 使用 hipSOLVER（rocSOLVER）成功实现原始 profile 和 7 个数值用例，并通过 CUDA 对照 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_potrfBatched_cusolver_potrfBatched_example.cu)；[记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_potrfBatched_cusolver_potrfBatched_example.cu) |
| [syevd/cusolver_syevd_example.cu](syevd/cusolver_syevd_example.cu) · [详情](../migration/sample-reports/cuSOLVER/syevd/cusolver_syevd_example.cu.md) | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER/rocSOLVER 与 hipBLAS 保留原始固定教学矩阵；通过独立 NumPy/SciPy 特征值/奇异值、重构/残差和正交性检查，见逐项误差与阈值。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_syevd_cusolver_syevd_example.cu)；[记录](../migration/reports/additional-comparison.json) |
| [syevdx/cusolver_syevdx_example.cu](syevdx/cusolver_syevdx_example.cu) · [详情](../migration/sample-reports/cuSOLVER/syevdx/cusolver_syevdx_example.cu.md) | hipSOLVER / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER / rocSOLVER/rocBLAS 保留原始 profile 与数学 API；4 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch3-validation.json)；[记录](../migration/reports/evidence/20261109T135901.256203Z/batch3-cuda/cuSOLVER_syevdx_cusolver_syevdx_example.cu) |
| [syevj/cusolver_syevj_example.cu](syevj/cusolver_syevj_example.cu) · [详情](../migration/sample-reports/cuSOLVER/syevj/cusolver_syevj_example.cu.md) | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER/rocSOLVER 与 hipBLAS 保留原始固定教学矩阵；通过独立 NumPy/SciPy 特征值/奇异值、重构/残差和正交性检查，见逐项误差与阈值。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_syevj_cusolver_syevj_example.cu)；[记录](../migration/reports/additional-comparison.json) |
| [syevjBatched/cusolver_syevjBatched_example.cu](syevjBatched/cusolver_syevjBatched_example.cu) · [详情](../migration/sample-reports/cuSOLVER/syevjBatched/cusolver_syevjBatched_example.cu.md) | hipSOLVER / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER / rocSOLVER/rocBLAS 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch3-validation.json)；[记录](../migration/reports/evidence/20261109T135901.256203Z/batch3-cuda/cuSOLVER_syevjBatched_cusolver_syevjBatched_example.cu) |
| [sygvd/cusolver_sygvd_example.cu](sygvd/cusolver_sygvd_example.cu) · [详情](../migration/sample-reports/cuSOLVER/sygvd/cusolver_sygvd_example.cu.md) | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER/rocSOLVER 与 hipBLAS 保留原始固定教学矩阵；通过独立 NumPy/SciPy 特征值/奇异值、重构/残差和正交性检查，见逐项误差与阈值。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_sygvd_cusolver_sygvd_example.cu)；[记录](../migration/reports/additional-comparison.json) |
| [sygvdx/cusolver_sygvdx_example.cu](sygvdx/cusolver_sygvdx_example.cu) · [详情](../migration/sample-reports/cuSOLVER/sygvdx/cusolver_sygvdx_example.cu.md) | hipSOLVER / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER / rocSOLVER/rocBLAS 保留原始 profile 与数学 API；4 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch3-validation.json)；[记录](../migration/reports/evidence/20261109T135901.256203Z/batch3-cuda/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu) |
| [sygvj/cusolver_sygvj_example.cu](sygvj/cusolver_sygvj_example.cu) · [详情](../migration/sample-reports/cuSOLVER/sygvj/cusolver_sygvj_example.cu.md) | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS | L4 / PASSED | 使用 hipSOLVER/rocSOLVER 与 hipBLAS 保留原始固定教学矩阵；通过独立 NumPy/SciPy 特征值/奇异值、重构/残差和正交性检查，见逐项误差与阈值。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_sygvj_cusolver_sygvj_example.cu)；[记录](../migration/reports/additional-comparison.json) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
