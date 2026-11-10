# B4–B8 实时实施与验收

更新时间：2026-11-10T02:45:56.598325+00:00。26 个目标；当前全项目 174 PASSED，6 PARTIAL，456 FAILED。每项只有预登记全部 case 的 AMD/CPU/CUDA 数值与语义检查通过后才提升。

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
| B5 | [cuTENSOR/elementwise_permute_padding.cu](../sample-reports/cuTENSOR/elementwise_permute_padding.cu.md) | hiptensor | 待实施；保留既有 FAILED | 未验收 |
| B5 | [cuTENSOR/einsum.cu](../sample-reports/cuTENSOR/einsum.cu.md) | hiptensor | 待实施；保留既有 FAILED | 未验收 |
| B5 | [cuTENSOR/contraction_trinary.cu](../sample-reports/cuTENSOR/contraction_trinary.cu.md) | hiptensor | 待实施；保留既有 FAILED | 未验收 |
| B5 | [cuTENSOR/contraction_plan_cache.cu](../sample-reports/cuTENSOR/contraction_plan_cache.cu.md) | hiptensor | 待实施；保留既有 FAILED | 未验收 |
| B6 | [cuSOLVER/Xgetrf/cusolver_Xgetrf_example.cu](../sample-reports/cuSOLVER/Xgetrf/cusolver_Xgetrf_example.cu.md) | hipsolver | 待实施；保留既有 FAILED | 未验收 |
| B6 | [cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu](../sample-reports/cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu.md) | 待验证 | 待实施；保留既有 FAILED | 未验收 |
| B6 | [cuSOLVER/Xtrtri/cusolver_Xtrtri_example.cu](../sample-reports/cuSOLVER/Xtrtri/cusolver_Xtrtri_example.cu.md) | 待验证 | 待实施；保留既有 FAILED | 未验收 |
| B6 | [cuSOLVER/Xgesvd/cusolver_Xgesvd_example.cu](../sample-reports/cuSOLVER/Xgesvd/cusolver_Xgesvd_example.cu.md) | 待验证 | 待实施；保留既有 FAILED | 未验收 |
| B7 | [cuBLAS/Extensions/GemmGroupedBatchedEx/cublas_GemmGroupedBatchedEx_example.cu](../sample-reports/cuBLAS/Extensions/GemmGroupedBatchedEx/cublas_GemmGroupedBatchedEx_example.cu.md) | 待验证 | 待实施；保留既有 FAILED | 未验收 |
| B7 | [cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu](../sample-reports/cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu.md) | 待验证 | 待实施；保留既有 FAILED | 未验收 |
| B7 | [cuBLASLt/LtHSHgemmGroupedSimple/main.cpp](../sample-reports/cuBLASLt/LtHSHgemmGroupedSimple/main.cpp.md) | 待验证 | 待实施；保留既有 FAILED | 未验收 |
| B7 | [cuBLASLt/LtSgemmCustomFind/main.cu](../sample-reports/cuBLASLt/LtSgemmCustomFind/main.cu.md) | 待验证 | 待实施；保留既有 FAILED | 未验收 |
| B7 | [cuBLASLt/LtSgemmSimpleAutoTuning/main.cpp](../sample-reports/cuBLASLt/LtSgemmSimpleAutoTuning/main.cpp.md) | 待验证 | 待实施；保留既有 FAILED | 未验收 |
| B8 | [cuSPARSE/spmat_convert/spmat_convert_example.c](../sample-reports/cuSPARSE/spmat_convert/spmat_convert_example.c.md) | 待验证 | 待实施；保留既有 FAILED | 未验收 |
| B8 | [cuSPARSE/spgemm_mem/spgemm_mem_example.c](../sample-reports/cuSPARSE/spgemm_mem/spgemm_mem_example.c.md) | 待验证 | 待实施；保留既有 FAILED | 未验收 |
| B8 | [cuSPARSE/spmv_symmetric_csr/spmv_symmetric_example.c](../sample-reports/cuSPARSE/spmv_symmetric_csr/spmv_symmetric_example.c.md) | 待验证 | 待实施；保留既有 FAILED | 未验收 |
| B8 | [cuSPARSE/spmvop_csr/spmv_csr_op_example.c](../sample-reports/cuSPARSE/spmvop_csr/spmv_csr_op_example.c.md) | 待验证 | 待实施；保留既有 FAILED | 未验收 |
| B8 | [cuSPARSE/spmm_csr_op/spmm_csr_op_example.c](../sample-reports/cuSPARSE/spmm_csr_op/spmm_csr_op_example.c.md) | 待验证 | 待实施；保留既有 FAILED | 未验收 |

原生 Ex 包装的运行失败和精确失败源码另存 [b4-native-ex-failure.json](b4-native-ex-failure.json)。固定 complex32 的 HERK/SYRK 使用类型化 hipBLAS；packed 使用项目 HIP GPU kernel；SELL/BSR 在 GPU 上转换后调用 hipSPARSE，再恢复原始存储格式。

本批源码与输入草案见 `tools/migration/batches4_8_spec.py`；数值证据见 [validation](batches4_8-validation.json)、[AMD](batches4_8-rocm.json)、[CUDA](batches4_8-cuda.json)。大二进制输出留本地、记录 SHA256/生成方式。性能资格单列，不将正确性运行的计时宣称为合格加速。
