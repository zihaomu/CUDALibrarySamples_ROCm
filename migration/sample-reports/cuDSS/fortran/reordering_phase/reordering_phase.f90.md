# cuDSS/fortran/reordering_phase::reordering_phase.f90

**PARTIAL / L3**

真实标准Fortran入口7场景通过独立FP64 CPU检查；包含原始数组/leading-dimension、GPU分解求解与排列使用、padding和奇异info。native对照、负向、轨迹及独立复核仍待收口；不声称NVIDIA编译器或vendor内部排列完全相同。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/fortran/reordering_phase/reordering_phase.f90](../../../../../cuDSS/fortran/reordering_phase/reordering_phase.f90) |
| 实际库 / 后端 | standard Fortran ISO_C_BINDING + project HIP CSR pivot LU/solve; CPU symbolic min-degree only / — |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/fortran/reordering_phase/reordering_phase.f90](../../../../../rocm/ported/cuDSS/fortran/reordering_phase/reordering_phase.f90) |
| required cases | 0/2 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `7ab5256c56bab8f2879ec0c6edceb393cd0033c7e599afed08b959a2d399e009` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`UNIMPLEMENTED_BINDING`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T084354.110802Z/languages/cuDSS_fortran_reordering_phase_reordering_phase.f90](../../../../reports/evidence/20261109T084354.110802Z/languages/cuDSS_fortran_reordering_phase_reordering_phase.f90)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_fortran_reordering_phase_reordering_phase.f90](../../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_fortran_reordering_phase_reordering_phase.f90)
- [migration/reports/evidence/rewrite/R5/cuDSS_fortran_reordering_phase__reordering_phase.f90/20261110T101053.439324Z-R5-rocm-fortran-cfd97f7c35](../../../../reports/evidence/rewrite/R5/cuDSS_fortran_reordering_phase__reordering_phase.f90/20261110T101053.439324Z-R5-rocm-fortran-cfd97f7c35)
