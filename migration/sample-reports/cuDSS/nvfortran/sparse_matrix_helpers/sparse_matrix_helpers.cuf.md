# cuDSS/nvfortran/sparse_matrix_helpers::sparse_matrix_helpers.cuf

**FAILED / L0**

Fortran 原始入口使用 iso_fortran_env, iso_c_binding, cudafor, cudss；当前 flang 编译失败，CUDA/cuDSS/cuFFT/NVFortran module 和 device 语法需用经验证的 ISO_C_BINDING 与 AMD API 重写。C ABI 探针另记，不代表该例已实现。 日志：helpers.cuf:109:8: error: No explicit type declared for 'cudssmatrixdestroy'     st = cudssMatrixDestroy(A); st = cudssDestroy(handle)          ^^^^^^^^^^^^^^^^^^ /home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuDSS/nvfortran/sparse_matrix_helpers/sparse_matrix_helpers.cuf:109:36: error: No explicit type declared for 'cudssdestroy'     st = cudssMatrixDestroy(A); st = cudssDestroy(handle)                                      ^^^^^^^^^^^^

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/nvfortran/sparse_matrix_helpers/sparse_matrix_helpers.cuf](../../../../../cuDSS/nvfortran/sparse_matrix_helpers/sparse_matrix_helpers.cuf) |
| 实际库 / 后端 | — / — |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | 无实现 |
| required cases | 0/2 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `b43ee60fe823851ca7fe271048ec3ffdc0e57a9bbd564acd02dd349a6c367713` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`UNIMPLEMENTED_BINDING`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T084354.110802Z/languages/cuDSS_nvfortran_sparse_matrix_helpers_sparse_matrix_helpers.cuf](../../../../reports/evidence/20261109T084354.110802Z/languages/cuDSS_nvfortran_sparse_matrix_helpers_sparse_matrix_helpers.cuf)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_nvfortran_sparse_matrix_helpers_sparse_matrix_helpers.cuf](../../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_nvfortran_sparse_matrix_helpers_sparse_matrix_helpers.cuf)
