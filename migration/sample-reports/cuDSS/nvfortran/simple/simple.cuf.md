# cuDSS/nvfortran/simple::simple.cuf

**PASSED / L4**

原始 one-based 5×5 SPD 输入与 RHS 以标准 Fortran/ISO_C_BINDING 改写；CPU 稀疏符号分析、rocSOLVER CSRRF GPU 数值分解与求解，解及 CSR 残差通过。CUDA Fortran vendor module/device 语法由 C ABI 取代，未降低精度。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/nvfortran/simple/simple.cuf](../../../../../cuDSS/nvfortran/simple/simple.cuf) |
| 实际库 / 后端 | rocSOLVER + rocBLAS via ISO_C_BINDING/C ABI / GPU CSRRF sparse Cholesky; CPU sparse symbolic graph |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/cuDSS/fortran/simple/sample.f90](../../../../../rocm/cuDSS/fortran/simple/sample.f90) |
| required cases | 2/2 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `af28192c44ad478b296188f1e0e6299b612960597405327d4405a45a0a41b121` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-one-based-spd-fortran-solution`, `original-one-based-spd-fortran-residual`。

实现方式：`LIBRARY_REWRITE`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T084354.110802Z/languages/cuDSS_nvfortran_simple_simple.cuf](../../../../reports/evidence/20261109T084354.110802Z/languages/cuDSS_nvfortran_simple_simple.cuf)
- [migration/reports/evidence/20261109T091750.718197Z/fortran-sparse](../../../../reports/evidence/20261109T091750.718197Z/fortran-sparse)
- [migration/reports/evidence/20261109T095656.683154Z/fortran-sparse](../../../../reports/evidence/20261109T095656.683154Z/fortran-sparse)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_nvfortran_simple_simple.cuf](../../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_nvfortran_simple_simple.cuf)
