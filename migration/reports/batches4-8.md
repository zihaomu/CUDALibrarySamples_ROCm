# B4–B8 实时实施与验收

更新时间：2026-11-10T05:42:35.407283+00:00。26 个目标；当前全项目 211 PASSED，24 PARTIAL，402 FAILED。每项只有预登记全部 case 的 AMD/CPU/CUDA 数值与语义检查通过后才提升。

| 批次 | 样例 / 详细日志 | 实际 AMD 路线 | 本批进度 | CPU / CUDA |
| --- | --- | --- | --- | --- |
| B4 | [cuBLAS/Extensions/GemmBatchedEx/cublas_GemmBatchedEx_example.cu](../sample-reports/cuBLAS/Extensions/GemmBatchedEx/cublas_GemmBatchedEx_example.cu.md) | hipBLAS | 已验收 4/4 cases | PASSED / PASSED |
| B4 | [cuBLAS/Extensions/CherkEx/cublas_CherkEx_example.cu](../sample-reports/cuBLAS/Extensions/CherkEx/cublas_CherkEx_example.cu.md) | hipBLAS | 已验收 4/4 cases | PASSED / PASSED |
| B4 | [cuBLAS/Extensions/CsyrkEx/cublas_CsyrkEx_example.cu](../sample-reports/cuBLAS/Extensions/CsyrkEx/cublas_CsyrkEx_example.cu.md) | hipBLAS | 已验收 4/4 cases | PASSED / PASSED |
| B4 | [cuBLAS/Extensions/trttp/cublas_trttp_example.cu](../sample-reports/cuBLAS/Extensions/trttp/cublas_trttp_example.cu.md) | HIP GPU packed conversion | 已验收 4/4 cases | PASSED / PASSED |
| B4 | [cuBLAS/Extensions/tpttr/cublas_tpttr_example.cu](../sample-reports/cuBLAS/Extensions/tpttr/cublas_tpttr_example.cu.md) | HIP GPU packed conversion | 已验收 4/4 cases | PASSED / PASSED |
| B4 | [cuSOLVER/ormqr/cusolver_ormqr_example.cu](../sample-reports/cuSOLVER/ormqr/cusolver_ormqr_example.cu.md) | hipSOLVER | 已验收 4/4 cases | PASSED / PASSED |
| B4 | [cuSPARSE/spsv_sell/spsv_sell_example.c](../sample-reports/cuSPARSE/spsv_sell/spsv_sell_example.c.md) | hipSPARSE + HIP format adapter | 已验收 4/4 cases | PASSED / PASSED |
| B4 | [cuSPARSE/sddmm_bsr/sddmm_bsr_example.c](../sample-reports/cuSPARSE/sddmm_bsr/sddmm_bsr_example.c.md) | hipSPARSE + HIP format adapter | 已验收 4/4 cases | PASSED / PASSED |
| B5 | [cuTENSOR/elementwise_permute_padding.cu](../sample-reports/cuTENSOR/elementwise_permute_padding.cu.md) | HIP GPU permutation/padding | 已验收 3/3 cases | PASSED / PASSED |
| B5 | [cuTENSOR/einsum.cu](../sample-reports/cuTENSOR/einsum.cu.md) | hipTensor + rocBLAS + HIP | 已验收 3/3 cases | PASSED / PASSED |
| B5 | [cuTENSOR/contraction_trinary.cu](../sample-reports/cuTENSOR/contraction_trinary.cu.md) | rocBLAS + HIP tensor adapter | 已验收 3/3 cases | PASSED / PASSED |
| B5 | [cuTENSOR/contraction_plan_cache.cu](../sample-reports/cuTENSOR/contraction_plan_cache.cu.md) | rocBLAS + HIP tiled-plan/cache adapter | 已验收 3/3 cases | PASSED / PASSED |
| B6 | [cuSOLVER/Xgetrf/cusolver_Xgetrf_example.cu](../sample-reports/cuSOLVER/Xgetrf/cusolver_Xgetrf_example.cu.md) | rocSOLVER ILP64 | 已验收 4/4 cases | PASSED / PASSED |
| B6 | [cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu](../sample-reports/cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu.md) | rocSOLVER dsyevx + checked dimension bridge | 已验收 4/4 cases | PASSED / PASSED |
| B6 | [cuSOLVER/Xtrtri/cusolver_Xtrtri_example.cu](../sample-reports/cuSOLVER/Xtrtri/cusolver_Xtrtri_example.cu.md) | hipBLAS Dtrsm_64 + HIP diagonal/info adapter | 已验收 4/4 cases | PASSED / PASSED |
| B6 | [cuSOLVER/Xgesvd/cusolver_Xgesvd_example.cu](../sample-reports/cuSOLVER/Xgesvd/cusolver_Xgesvd_example.cu.md) | rocSOLVER dgesvd + checked dimension bridge | 已验收 3/3 cases | PASSED / PASSED |
| B7 | [cuBLAS/Extensions/GemmGroupedBatchedEx/cublas_GemmGroupedBatchedEx_example.cu](../sample-reports/cuBLAS/Extensions/GemmGroupedBatchedEx/cublas_GemmGroupedBatchedEx_example.cu.md) | hipBLAS + project search/group dispatch | 已验收 3/3 cases | PASSED / PASSED |
| B7 | [cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu](../sample-reports/cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu.md) | hipBLAS + project search/group dispatch | 已验收 3/3 cases | PASSED / PASSED |
| B7 | [cuBLASLt/LtHSHgemmGroupedSimple/main.cpp](../sample-reports/cuBLASLt/LtHSHgemmGroupedSimple/main.cpp.md) | hipBLASLt + project search/group dispatch | 已验收 3/3 cases | PASSED / PASSED |
| B7 | [cuBLASLt/LtSgemmCustomFind/main.cu](../sample-reports/cuBLASLt/LtSgemmCustomFind/main.cu.md) | hipBLASLt + project search/group dispatch | 已验收 3/3 cases | PASSED / PASSED |
| B7 | [cuBLASLt/LtSgemmSimpleAutoTuning/main.cpp](../sample-reports/cuBLASLt/LtSgemmSimpleAutoTuning/main.cpp.md) | hipBLASLt + project search/group dispatch | 已验收 3/3 cases | PASSED / PASSED |
| B8 | [cuSPARSE/spmat_convert/spmat_convert_example.c](../sample-reports/cuSPARSE/spmat_convert/spmat_convert_example.c.md) | hipSPARSE Csr2cscEx2 | 已验收 4/4 cases | PASSED / PASSED |
| B8 | [cuSPARSE/spgemm_mem/spgemm_mem_example.c](../sample-reports/cuSPARSE/spgemm_mem/spgemm_mem_example.c.md) | HIP GPU budgeted CSR SpGEMM adapter | 已验收 4/4 cases | PASSED / PASSED |
| B8 | [cuSPARSE/spmv_symmetric_csr/spmv_symmetric_example.c](../sample-reports/cuSPARSE/spmv_symmetric_csr/spmv_symmetric_example.c.md) | HIP symmetric expansion + rocSPARSE v2 | 已验收 4/4 cases | PASSED / PASSED |
| B8 | [cuSPARSE/spmvop_csr/spmv_csr_op_example.c](../sample-reports/cuSPARSE/spmvop_csr/spmv_csr_op_example.c.md) | HIP GPU fused custom SpMV epilogue | 已验收 3/3 cases | PASSED / PASSED |
| B8 | [cuSPARSE/spmm_csr_op/spmm_csr_op_example.c](../sample-reports/cuSPARSE/spmm_csr_op/spmm_csr_op_example.c.md) | HIP GPU fused custom SpMM add/mul/epilogue | 已验收 3/3 cases | PASSED / PASSED |

原生 Ex 包装的运行失败和精确失败源码另存 [b4-native-ex-failure.json](b4-native-ex-failure.json)。固定 complex32 的 HERK/SYRK 使用类型化 hipBLAS；packed 使用项目 HIP GPU kernel；SELL/BSR 在 GPU 上转换后调用 hipSPARSE，再恢复原始存储格式。

适配边界：B5 padding 为 HIP GPU 实现，einsum 为 hipTensor/rocBLAS 路由，三输入收缩为 FP32 rocBLAS + GPU 分块排列，缓存为项目真实分块搜索及持久化策略。B6 LU/三角求逆使用64位接口，SVD/eigen typed 接口显式拒绝超过 INT_MAX 的尺寸。B7 FP32 Grouped Ex 使用 hipBLAS batched 按组分发；FP64 autotune 为项目实际 row-dispatch 搜索；Lt 搜索会运行并核对每个候选，HSH保留原例seed42的空group，bias/out-of-place/FP16输出均验收，不声称HIP原生device-grouped描述符等价。

B8 conversion 使用 hipSPARSE Csr2cscEx2；symmetric 在GPU上展开后用rocSPARSE v2；SpGEMM 为项目 HIP CSR kernel，numeric accumulator 按预算分块（不包含调用者输入/最终输出内存）；SpMV/SpMM custom op 保留原例设备函数并在HIP数值路径执行。CUDA 的 convert、新symmetric API、SpMVOp 在已安装SDK中缺失，三者使用**兼容CUDA数学基线**通过对照，原始CUDA API基线仍标FAILED，见 [native API failure](b8-native-cuda-api-failure.json)。SpGEMM ALG3/SpMMOp 则为原生CUDA API。

验证加固：26项各一次有限错误输出与一次NaN，共52次全部拒绝；另8次缓存/search/workspace/chunk/symmetry/custom语义错误全部拒绝；4项真实进程运行边界检查通过；54个B5输入buffer以seed=20261110分块重建并逐文件核对SHA256。详见 [输出故障注入](batches4_8-negative.json)、[语义故障注入](batches4_8-semantic-negative.json)、[运行边界](batches4_8-runtime-checks.json)、[输入重建](batches4_8-input-replay.json)。

本批源码与输入草案见 `tools/migration/batches4_8_spec.py`；数值证据见 [validation](batches4_8-validation.json)、[AMD](batches4_8-rocm.json)、[CUDA](batches4_8-cuda.json)。大二进制输出留本地、记录 SHA256/生成方式。性能资格单列，不将正确性运行的计时宣称为合格加速。
