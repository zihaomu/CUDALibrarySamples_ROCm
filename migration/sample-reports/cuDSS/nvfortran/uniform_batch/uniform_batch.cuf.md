# cuDSS/nvfortran/uniform_batch::uniform_batch.cuf

**PASSED / L4**

标准Fortran ISO_C_BINDING真实入口；CPU符号分析+HIP CSR pivot LU/solve，6数值场景通过独立FP64与同输入native cuDSS；奇异info单列（GENERAL native经同步仍info0/NaN，是原生数值失败，非通过基线）。排列实际用于factor/solve、leading dimensions/padding、17注入/8运行边界、C ABI生命周期及GPU轨迹与独立复核通过。nvfortran来源改写为标准Fortran，不声称NVIDIA编译器或内部排列等价。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/nvfortran/uniform_batch/uniform_batch.cuf](../../../../../cuDSS/nvfortran/uniform_batch/uniform_batch.cuf) |
| 实际库 / 后端 | standard Fortran ISO_C_BINDING + project HIP CSR pivot LU/solve; CPU symbolic min-degree only / — |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/nvfortran/uniform_batch/uniform_batch.f90](../../../../../rocm/ported/cuDSS/nvfortran/uniform_batch/uniform_batch.f90) |
| required cases | 12/12 |
| CUDA baseline / comparison | BLOCKED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `d25219b88b37642e35676b6e18b269393a4eb949e487ddea62b814260be9018e` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite/R5/original`, `rewrite/R5/changed-values`, `rewrite/R5/layout`, `rewrite/R5/base0`, `rewrite/R5/repeat`, `rewrite/R5/irregular`, `rewrite/R5/singular-info`, `rewrite/R5/negative`, `rewrite/R5/runtime`, `rewrite/R5/C-ABI`, `rewrite/R5/GPU-trace`, `rewrite/R5/review`。

实现方式：`ALGORITHM_REWRITE_WITH_STANDARD_FORTRAN_C_ABI`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：真实CUDA C++ cuDSS核心使用相同冻结Fortran数组；CUDA主机缺少Fortran编译器及vendor module，原语言原生基线仍BLOCKED。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T084354.110802Z/languages/cuDSS_nvfortran_uniform_batch_uniform_batch.cuf](../../../../reports/evidence/20261109T084354.110802Z/languages/cuDSS_nvfortran_uniform_batch_uniform_batch.cuf)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_nvfortran_uniform_batch_uniform_batch.cuf](../../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_nvfortran_uniform_batch_uniform_batch.cuf)
- [migration/reports/evidence/rewrite/R5/cuDSS_nvfortran_uniform_batch__uniform_batch.cuf/20261110T101120.786409Z-R5-rocm-fortran-a20e4918ca](../../../../reports/evidence/rewrite/R5/cuDSS_nvfortran_uniform_batch__uniform_batch.cuf/20261110T101120.786409Z-R5-rocm-fortran-a20e4918ca)
- [migration/reports/evidence/rewrite/R5/cuDSS_nvfortran_uniform_batch__uniform_batch.cuf/20261110T104823.399436Z-R5-composite-qualification-64c98b8470](../../../../reports/evidence/rewrite/R5/cuDSS_nvfortran_uniform_batch__uniform_batch.cuf/20261110T104823.399436Z-R5-composite-qualification-64c98b8470)
- [migration/reports/rewrite-R5-qualification.json](../../../../reports/rewrite-R5-qualification.json)
