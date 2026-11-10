# cuSPARSE Library - Generic APIs Examples

## Description

This folder demonstrates cuSPARSE Generic APIs usage.

[cuSPARSE Generic APIs Documentation](https://docs.nvidia.com/cuda/cusparse/index.html#cusparse-generic-api-reference)

## cuSPARSE Samples

- [Vector - Vector Operations](#vector-vector-operations)
- [Matrix - Vector Operations](#matrix-vector-operations)
- [Matrix - Matrix Operations](#matrix-matrix-operations)
- [Conversion](#conversion)
- [Legacy APIs](#legacy-apis)
- [Optimizations](#optimizations)
- [Sparse Iterative Methods](#sparse-iterative-methods)

---

#### Vector - Vector Operations

* [cusparseAxpby](axpby/)

    The sample demonstrates *Sparse Vector - Dense Vector scaling and sum*

* [cusparseGather](gather/)

    The sample demonstrates *Dense Vector to Sparse Vector element gathering*

* [cusparseRot](rot/)

    The sample demonstrates *Sparse Vector - Dense Vector Givens rotation*

* [cusparseScatter](scatter/)

    The sample demonstrates *Sparse Vector to Dense Vector element scattering*

* [cusparseSpVV](spvv/)

    The sample demonstrates *Sparse Vector - Dense Vector dot product*

#### Matrix - Vector Operations

* [cusparseSpMV CSR](spmv_csr/)

    The sample demonstrates *Sparse Matrix - Dense Vector multiplication*, where the sparse matrix is represented in CSR (Compressed Sparse Row) storage format

* [cusparseSpMV COO](spmv_coo/)

    The sample demonstrates *Sparse Matrix - Dense Vector multiplication*, where the sparse matrix is represented in COO (Coordinate) storage format

* [cusparseSpSV CSR](spsv_csr/)

    The sample demonstrates *Sparse triangular solver with single right-hand side*, where the sparse matrix is represented in CSR (Compressed Sparse Row) storage format

* [cusparseSpSV COO](spsv_coo/)

    The sample demonstrates *Sparse triangular solver with single right-hand side*, where the sparse matrix is represented in COO (Coordinate) storage format

#### Matrix - Matrix Operations

* [cusparseSpMM CSR](spmm_csr/)

    The sample demonstrates *Sparse Matrix - Dense Matrix multiplication = Dense Matrix*, where the sparse matrix is represented in CSR (Compressed Sparse Row) storage format

* [cusparseSpMM CSR - Batched](spmm_csr_batched/)

    The sample demonstrates *Batched Sparse Matrix - Dense Matrix multiplication = Dense Matrix* , where the sparse matrix is represented in CSR (Compressed Sparse Row) storage format

* [cusparseSpMMOp CSR](spmm_csr_op/)

    The sample demonstrates *Sparse Matrix - Dense Matrix multiplication = Dense Matrix* *with Custom Operators*, where the sparse matrix is represented in CSR (Compressed Sparse Row) storage format

* [cusparseSpMM COO](spmm_coo/)

    The sample demonstrates *Sparse Matrix - Dense Matrix multiplication = Dense Matrix*, where the sparse matrix is represented in COO (Coordinate) storage format

* [cusparseSpMM COO - Batched](spmm_coo_batched/)

    The sample demonstrates *Batched Sparse Matrix - Dense Matrix multiplication = Dense Matrix*, where the sparse matrix is represented in COO (Coordinate) storage format

* [cusparseSpMM SDDMM](sddmm_csr/)

    The sample demonstrates *Dense Matrix - Dense Matrix multiplication = Sparse Matrix*, where the sparse matrix is represented in CSR (Compressed Sparse Row) storage format

* [cusparseSpMM Blocked-ELL](spmm_blockedell/)

    The sample demonstrates *Sparse Matrix - Dense Matrix multiplication = Dense Matrix*, where the sparse matrix is represented in Blocked-ELL storage format

* [cusparseSpMM SDDMM - Batched](sddmm_csr_batched/)
    The sample demonstrates *Batched Dense matrix - Dense matrix multiplication = Sparse matrix*, where the sparse matrix is represented in CSR (Compressed Sparse Row) storage format

* [cusparseSpGEMM](spgemm/)

    The sample demonstrates *Sparse Matrix - Sparse Matrix multiplication = Sparse Matrix*, where all operands are sparse matrices represented in CSR (Compressed Sparse Row) storage format

* [cusparseSpGEMM - Memory Optmization](spgemm_mem/)

    The sample demonstrates *Sparse Matrix - Sparse Matrix multiplication = Sparse Matrix*, where all operands are sparse matrices represented in CSR (Compressed Sparse Row) storage format and the memory usage is optimzed

* [cusparseSpGEMM_reuse](spgemm_reuse/)

    The sample demonstrates *Sparse Matrix - Sparse Matrix multiplication = Sparse Matrix*, where all operands are sparse matrices represented in CSR (Compressed Sparse Row) storage format and the structure of the output matrix can be reused multiple times

* [cusparseSpSM CSR](spsm_csr/)

    The sample demonstrates *Sparse triangular solver with multiple right-hand sides*, where the sparse matrix is represented in CSR (Compressed Sparse Row) storage format

* [cusparseSpSM COO](spsm_coo/)

    The sample demonstrates *Sparse triangular solver with multiple right-hand sides*, where the sparse matrix is represented in COO (Coordinate) storage format

#### Conversion

* [cusparseSparseToDense](sparse2dense_csr/)

    The sample demonstrates *Sparse Matrix to Dense Matrix conversion*, where the sparse matrix is represented in CSR (Compressed Sparse Row) storage format

* [cusparseDenseToSparse](dense2sparse_csr/)

    The sample demonstrates *Dense Matrix to Sparse Matrix conversion*, where the sparse matrix is represented in CSR (Compressed Sparse Row) storage format

* [cusparseDenseToSparse (Blocked-ELL)](dense2sparse_blockedell/)

    The sample demonstrates *Dense Matrix to Sparse Matrix conversion*, where the sparse matrix is represented in Blocked-Ellpack storage format

#### Legacy APIs

* [cusparseXcoosortByRow](coosort/)

    The sample demonstrates how to sort a COO format matrix

* [cusparseSgpsvInterleavedBatch](gpsvInterleavedBatch/)

    The sample demonstrates how to solves two penta-diagonal systems with NOT interleaved format

#### Optimizations

* [CUDA Graph Capture](graph_capture/)

    The sample demonstrates how to optimize *Sparse vector - Dense vector dot product* (`cusparseSpVV`) by exploiting *CUDA Graph Capture functionality*

* [Hardware Memory Compression](compression/)

    The sample demonstrates how to optimize *Sparse vector - Dense vector scaling and sum* (`cusparseAxpby`) by exploiting NVIDIA Ampere architecture *Hardware Memory Compression*

#### Sparse Iterative Methods

* [Preconditioned CG](cg/)

    The sample describes how to use the cuSPARSE and cuBLAS libraries to implement the Incomplete-Cholesky preconditioned iterative *Conjugate Gradient (CG)*

* [Preconditioned BiCGStab](bicgstab/)

    The sample describes how to use the cuSPARSE and cuBLAS libraries to implement the Incomplete-LU preconditioned iterative *Biconjugate Gradient Stabilized Method (BiCGStab)*

<!-- ROCM-MIGRATION:START -->
## ROCm 迁移实时状态

37 个独立源入口；PASSED 31，PARTIAL 0，FAILED 6，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：hipSPARSE, rocSPARSE。候选不等于已使用；基础探针成功也不等于整库迁移成功。

CSR/COO/blocked ELL、SpVV/SpGEMM/reuse、CG/BiCGSTAB、gpsvInterleavedBatch 与真实 SpVV Graph Capture/Replay 已通过独立 CPU 和 CUDA 验收。BSR SDDMM、部分新转换/custom operator 与其它原始入口仍失败，不能推及整个库。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [axpby/axpby_example.c](axpby/axpby_example.c) · [详情](../migration/sample-reports/cuSPARSE/axpby/axpby_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_axpby_axpby_example.c) |
| [bicgstab/bicgstab_example.c](bicgstab/bicgstab_example.c) · [详情](../migration/sample-reports/cuSPARSE/bicgstab/bicgstab_example.c.md) | hipSPARSE + hipBLAS / rocSPARSE/rocBLAS | L4 / PASSED | 使用 hipSPARSE + hipBLAS / rocSPARSE/rocBLAS 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T140002.910290Z/batch3-rocm/cuSPARSE_bicgstab_bicgstab_example.c)；[记录](../migration/reports/evidence/20261109T135811.364204Z/batch3-cuda/cuSPARSE_bicgstab_bicgstab_example.c) |
| [cg/cg_example.c](cg/cg_example.c) · [详情](../migration/sample-reports/cuSPARSE/cg/cg_example.c.md) | hipSPARSE + hipBLAS / rocSPARSE/rocBLAS | L4 / PASSED | 使用 hipSPARSE + hipBLAS / rocSPARSE/rocBLAS 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261109T140002.910290Z/batch3-rocm/cuSPARSE_cg_cg_example.c)；[记录](../migration/reports/evidence/20261109T135811.364204Z/batch3-cuda/cuSPARSE_cg_cg_example.c) |
| [compression/compression_example.cpp](compression/compression_example.cpp) · [详情](../migration/sample-reports/cuSPARSE/compression/compression_example.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/compression/compression_example.cpp:73:43: error: use of undeclared identifier 'CU_MEM_ALLOCATION_COMP_GENERIC'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/compression/compression_example.cpp:214:21: error: use of undeclared identifier 'CU_DEVICE_ATTRIBUTE_GENERIC_COMPRESSION_SUPPORTED' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_compression_compression_example.cpp)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_compression_compression_example.cpp) |
| [coosort/coosort_example.c](coosort/coosort_example.c) · [详情](../migration/sample-reports/cuSPARSE/coosort/coosort_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_coosort_coosort_example.c) |
| [dense2sparse_blockedell/dense2sparse_blockedell_example.c](dense2sparse_blockedell/dense2sparse_blockedell_example.c) · [详情](../migration/sample-reports/cuSPARSE/dense2sparse_blockedell/dense2sparse_blockedell_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_dense2sparse_blockedell_dense2sparse_blockedell_example.c) |
| [dense2sparse_csr/dense2sparse_csr_example.c](dense2sparse_csr/dense2sparse_csr_example.c) · [详情](../migration/sample-reports/cuSPARSE/dense2sparse_csr/dense2sparse_csr_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_dense2sparse_csr_dense2sparse_csr_example.c) |
| [gather/gather_example.c](gather/gather_example.c) · [详情](../migration/sample-reports/cuSPARSE/gather/gather_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_gather_gather_example.c) |
| [gpsvInterleavedBatch/gpsvInterleavedBatch_example.c](gpsvInterleavedBatch/gpsvInterleavedBatch_example.c) · [详情](../migration/sample-reports/cuSPARSE/gpsvInterleavedBatch/gpsvInterleavedBatch_example.c.md) | hipSPARSE + hipBLAS / rocSPARSE/rocBLAS | L4 / PASSED | 使用 hipSPARSE + hipBLAS / rocSPARSE/rocBLAS 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch3-validation.json)；[记录](../migration/reports/evidence/20261109T135443.759704Z/batch3-cuda/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c) |
| [graph_capture/graph_capture_example.c](graph_capture/graph_capture_example.c) · [详情](../migration/sample-reports/cuSPARSE/graph_capture/graph_capture_example.c.md) | hipSPARSE + HIP Graph / rocSPARSE + HIP runtime | L4 / PASSED | 使用 hipSPARSE + HIP Graph / rocSPARSE + HIP runtime 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。初始化确定性输入并改用device pointer mode；实际GPU图节点及三次输入变化replay均已检查。 | PASSED / PASSED | [记录](../migration/reports/batch3-validation.json)；[记录](../migration/reports/evidence/20261109T140047.312334Z/batch3-cuda/cuSPARSE_graph_capture_graph_capture_example.c) |
| [rot/rot_example.c](rot/rot_example.c) · [详情](../migration/sample-reports/cuSPARSE/rot/rot_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T094106.862809Z/original-rocm/cuSPARSE_rot_rot_example.c)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_rot_rot_example.c) |
| [scatter/scatter_example.c](scatter/scatter_example.c) · [详情](../migration/sample-reports/cuSPARSE/scatter/scatter_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_scatter_scatter_example.c) |
| [sddmm_bsr/sddmm_bsr_example.c](sddmm_bsr/sddmm_bsr_example.c) · [详情](../migration/sample-reports/cuSPARSE/sddmm_bsr/sddmm_bsr_example.c.md) | hipSPARSE + HIP format adapter / rocSPARSE + HIP runtime | L4 / PASSED | 使用 hipSPARSE + HIP format adapter / rocSPARSE + HIP runtime 保留原始dtype/布局与数学运算；4 个预登记输入case通过独立CPU与同输入CUDA，GPU适配和数值路径均已检查。 | PASSED / PASSED | [记录](../migration/reports/batches4_8-validation.json)；[记录](../migration/reports/evidence/20261110T023758.405542Z/batches4_8-cuda/cuSPARSE_sddmm_bsr_sddmm_bsr_example.c) |
| [sddmm_csr/sddmm_csr_example.c](sddmm_csr/sddmm_csr_example.c) · [详情](../migration/sample-reports/cuSPARSE/sddmm_csr/sddmm_csr_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_sddmm_csr_sddmm_csr_example.c) |
| [sddmm_csr_batched/sddmm_csr_batched_example.c](sddmm_csr_batched/sddmm_csr_batched_example.c) · [详情](../migration/sample-reports/cuSPARSE/sddmm_csr_batched/sddmm_csr_batched_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_sddmm_csr_batched_sddmm_csr_batched_example.c) |
| [sparse2dense_csr/sparse2dense_csr_example.c](sparse2dense_csr/sparse2dense_csr_example.c) · [详情](../migration/sample-reports/cuSPARSE/sparse2dense_csr/sparse2dense_csr_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_sparse2dense_csr_sparse2dense_csr_example.c) |
| [spgemm/spgemm_example.c](spgemm/spgemm_example.c) · [详情](../migration/sample-reports/cuSPARSE/spgemm/spgemm_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE / rocSPARSE 保留原始 profile 与数学 API；2 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T115141.126114Z/batch2-cuda/cuSPARSE_spgemm_spgemm_example.c) |
| [spgemm_mem/spgemm_mem_example.c](spgemm_mem/spgemm_mem_example.c) · [详情](../migration/sample-reports/cuSPARSE/spgemm_mem/spgemm_mem_example.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spgemm_mem/spgemm_mem_example.c:151:20: error: use of undeclared identifier 'cusparseSpGEMM_getNumProducts'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spgemm_mem/spgemm_mem_example.c:155:9: error: use of undeclared identifier 'cusparseSpGEMM_estimateMemory' | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spgemm_mem_spgemm_mem_example.c)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spgemm_mem_spgemm_mem_example.c) |
| [spgemm_reuse/spgemm_reuse_example.c](spgemm_reuse/spgemm_reuse_example.c) · [详情](../migration/sample-reports/cuSPARSE/spgemm_reuse/spgemm_reuse_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE / rocSPARSE 保留原始 profile 与数学 API；2 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T115141.126114Z/batch2-cuda/cuSPARSE_spgemm_reuse_spgemm_reuse_example.c) |
| [spmat_convert/spmat_convert_example.c](spmat_convert/spmat_convert_example.c) · [详情](../migration/sample-reports/cuSPARSE/spmat_convert/spmat_convert_example.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spmat_convert/spmat_convert_example.c:90:5: error: unknown type name 'cusparseSpMatConvertDescr_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spmat_convert/spmat_convert_example.c:95:5: error: unknown type name 'cusparseSpMatConvertAlg_t' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spmat_convert_spmat_convert_example.c)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmat_convert_spmat_convert_example.c) |
| [spmm_blockedell/spmm_blockedell_example.cpp](spmm_blockedell/spmm_blockedell_example.cpp) · [详情](../migration/sample-reports/cuSPARSE/spmm_blockedell/spmm_blockedell_example.cpp.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmm_blockedell_spmm_blockedell_example.cpp) |
| [spmm_coo/spmm_coo_example.c](spmm_coo/spmm_coo_example.c) · [详情](../migration/sample-reports/cuSPARSE/spmm_coo/spmm_coo_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmm_coo_spmm_coo_example.c) |
| [spmm_coo_batched/spmm_coo_batched_example.c](spmm_coo_batched/spmm_coo_batched_example.c) · [详情](../migration/sample-reports/cuSPARSE/spmm_coo_batched/spmm_coo_batched_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmm_coo_batched_spmm_coo_batched_example.c) |
| [spmm_csr/spmm_csr_example.c](spmm_csr/spmm_csr_example.c) · [详情](../migration/sample-reports/cuSPARSE/spmm_csr/spmm_csr_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE（rocSPARSE）成功实现原始 profile 和 9 个数值用例，并通过 CUDA 对照 | PASSED / PASSED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmm_csr_spmm_csr_example.c) |
| [spmm_csr_batched/spmm_csr_batched_example.c](spmm_csr_batched/spmm_csr_batched_example.c) · [详情](../migration/sample-reports/cuSPARSE/spmm_csr_batched/spmm_csr_batched_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmm_csr_batched_spmm_csr_batched_example.c) |
| [spmm_csr_op/spmm_csr_op_example.c](spmm_csr_op/spmm_csr_op_example.c) · [详情](../migration/sample-reports/cuSPARSE/spmm_csr_op/spmm_csr_op_example.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spmm_csr_op/spmm_csr_op_example.c:101:18: error: use of undeclared identifier 'nvrtcGetLTOIRSize'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spmm_csr_op/spmm_csr_op_example.c:103:18: error: use of undeclared identifier 'nvrtcGetLTOIR' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spmm_csr_op_spmm_csr_op_example.c)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmm_csr_op_spmm_csr_op_example.c) |
| [spmv_coo/spmv_coo_example.c](spmv_coo/spmv_coo_example.c) · [详情](../migration/sample-reports/cuSPARSE/spmv_coo/spmv_coo_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmv_coo_spmv_coo_example.c) |
| [spmv_csr/spmv_csr_example.c](spmv_csr/spmv_csr_example.c) · [详情](../migration/sample-reports/cuSPARSE/spmv_csr/spmv_csr_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE（rocSPARSE）成功实现原始 profile 和 9 个数值用例，并通过 CUDA 对照 | PASSED / PASSED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmv_csr_spmv_csr_example.c) |
| [spmv_sell/spmv_sell_example.c](spmv_sell/spmv_sell_example.c) · [详情](../migration/sample-reports/cuSPARSE/spmv_sell/spmv_sell_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmv_sell_spmv_sell_example.c) |
| [spmv_symmetric_csr/spmv_symmetric_example.c](spmv_symmetric_csr/spmv_symmetric_example.c) · [详情](../migration/sample-reports/cuSPARSE/spmv_symmetric_csr/spmv_symmetric_example.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spmv_symmetric_csr/spmv_symmetric_example.c:103:5: error: unknown type name 'cusparseSpMVDescr_t'; did you mean 'hipsparseSpSVDescr_t'?；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spmv_symmetric_csr/spmv_symmetric_example.c:112:5: error: unknown type name 'cusparseSymmetryType_t' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spmv_symmetric_csr_spmv_symmetric_example.c)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmv_symmetric_csr_spmv_symmetric_example.c) |
| [spmvop_csr/spmv_csr_op_example.c](spmvop_csr/spmv_csr_op_example.c) · [详情](../migration/sample-reports/cuSPARSE/spmvop_csr/spmv_csr_op_example.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spmvop_csr/spmv_csr_op_example.c:105:17: error: use of undeclared identifier 'nvrtcGetLTOIRSize'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spmvop_csr/spmv_csr_op_example.c:107:17: error: use of undeclared identifier 'nvrtcGetLTOIR' | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spmvop_csr_spmv_csr_op_example.c)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmvop_csr_spmv_csr_op_example.c) |
| [spsm_coo/spsm_coo_example.c](spsm_coo/spsm_coo_example.c) · [详情](../migration/sample-reports/cuSPARSE/spsm_coo/spsm_coo_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spsm_coo_spsm_coo_example.c) |
| [spsm_csr/spsm_csr_example.c](spsm_csr/spsm_csr_example.c) · [详情](../migration/sample-reports/cuSPARSE/spsm_csr/spsm_csr_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spsm_csr_spsm_csr_example.c) |
| [spsv_coo/spsv_coo_example.c](spsv_coo/spsv_coo_example.c) · [详情](../migration/sample-reports/cuSPARSE/spsv_coo/spsv_coo_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。 | PASSED / BLOCKED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spsv_coo_spsv_coo_example.c) |
| [spsv_csr/spsv_csr_example.c](spsv_csr/spsv_csr_example.c) · [详情](../migration/sample-reports/cuSPARSE/spsv_csr/spsv_csr_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE（rocSPARSE）成功实现原始 profile 和 3 个数值用例，并通过 CUDA 对照 | PASSED / PASSED | [记录](../migration/reports/sparse-original-validation.json)；[记录](../migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spsv_csr_spsv_csr_example.c) |
| [spsv_sell/spsv_sell_example.c](spsv_sell/spsv_sell_example.c) · [详情](../migration/sample-reports/cuSPARSE/spsv_sell/spsv_sell_example.c.md) | hipSPARSE + HIP format adapter / rocSPARSE + HIP runtime | L4 / PASSED | 使用 hipSPARSE + HIP format adapter / rocSPARSE + HIP runtime 保留原始dtype/布局与数学运算；4 个预登记输入case通过独立CPU与同输入CUDA，GPU适配和数值路径均已检查。 | PASSED / PASSED | [记录](../migration/reports/batches4_8-validation.json)；[记录](../migration/reports/evidence/20261110T023758.405542Z/batches4_8-cuda/cuSPARSE_spsv_sell_spsv_sell_example.c) |
| [spvv/spvv_example.c](spvv/spvv_example.c) · [详情](../migration/sample-reports/cuSPARSE/spvv/spvv_example.c.md) | hipSPARSE / rocSPARSE | L4 / PASSED | 使用 hipSPARSE / rocSPARSE 保留原始 profile 与数学 API；2 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T115141.126114Z/batch2-cuda/cuSPARSE_spvv_spvv_example.c) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
