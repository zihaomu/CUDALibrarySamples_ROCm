# cuDSS/fortran/sparse_matrix_helpers::sparse_matrix_helpers.f90

**PASSED / L4**

9入口中的一个：真实C++/标准Fortran调用项目描述符C ABI，HIP分配/指针表与完整数据读回；5场景AMD/独立CPU/原生cuDSS API对照、生命周期/别名/故障和独立复审通过。仅描述符管理，不是GPU稀疏求解算法。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/fortran/sparse_matrix_helpers/sparse_matrix_helpers.f90](../../../../../cuDSS/fortran/sparse_matrix_helpers/sparse_matrix_helpers.f90) |
| 实际库 / 后端 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/fortran/sparse_matrix_helpers/sparse_matrix_helpers.f90](../../../../../rocm/ported/cuDSS/fortran/sparse_matrix_helpers/sparse_matrix_helpers.f90) |
| required cases | 8/8 |
| CUDA baseline / comparison | BLOCKED / PASSED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `e4ccf1af16a190572ca85480b2263d3a6bdfa78d568ace65af09f45a619909a5` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite/original`, `rewrite/changed-values`, `rewrite/irregular`, `rewrite/alternate-base`, `rewrite/repeat`, `rewrite/negative-and-runtime`, `rewrite/sealed-build-and-native-identities`, `rewrite/independent-source-review`。

实现方式：`PROJECT_DESCRIPTOR_ABI_WITH_HIP_STORAGE`。

恢复/扩展条件：扩展API/精度/布局/设备或性能声明时重新冻结合同并完成实际GPU与独立参考验收。

CUDA 对照限制：原始CUDA Fortran工具链仍BLOCKED；同输入native cuDSS C++ API对照通过，AMD侧实际执行标准Fortran。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python3 tools/moat/build_helpers.py
python3 tools/moat/run_helpers.py
```

- [migration/reports/evidence/20261109T084354.110802Z/languages/cuDSS_fortran_sparse_matrix_helpers_sparse_matrix_helpers.f90](../../../../reports/evidence/20261109T084354.110802Z/languages/cuDSS_fortran_sparse_matrix_helpers_sparse_matrix_helpers.f90)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_fortran_sparse_matrix_helpers_sparse_matrix_helpers.f90](../../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_fortran_sparse_matrix_helpers_sparse_matrix_helpers.f90)
- [migration/reports/rewrite-R9.md](../../../../reports/rewrite-R9.md)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T071908.866277Z-R9-composite-qualification-e7b7cdb597](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T071908.866277Z-R9-composite-qualification-e7b7cdb597)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063752.517189Z-R9-rocm-helper-1342ee753a](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063752.517189Z-R9-rocm-helper-1342ee753a)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063753.802253Z-R9-rocm-helper-493aa05c49](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063753.802253Z-R9-rocm-helper-493aa05c49)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063755.052560Z-R9-rocm-helper-df0079cc46](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063755.052560Z-R9-rocm-helper-df0079cc46)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063756.321652Z-R9-rocm-helper-aebdccc0d6](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063756.321652Z-R9-rocm-helper-aebdccc0d6)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063757.576185Z-R9-rocm-helper-c187f98925](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063757.576185Z-R9-rocm-helper-c187f98925)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063827.029666Z-R9-cuda-helper-1f58124f9c](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063827.029666Z-R9-cuda-helper-1f58124f9c)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063829.246768Z-R9-cuda-helper-b9e35709e5](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063829.246768Z-R9-cuda-helper-b9e35709e5)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063831.507233Z-R9-cuda-helper-2df1b3d979](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063831.507233Z-R9-cuda-helper-2df1b3d979)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063833.774451Z-R9-cuda-helper-e8d313a9a1](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063833.774451Z-R9-cuda-helper-e8d313a9a1)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063834.274815Z-R9-CPU-negative-9a2554693b](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063834.274815Z-R9-CPU-negative-9a2554693b)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063835.050184Z-R9-CPU-negative-56fbbb903e](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063835.050184Z-R9-CPU-negative-56fbbb903e)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063835.826232Z-R9-CPU-negative-59bf3d6a0d](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063835.826232Z-R9-CPU-negative-59bf3d6a0d)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063836.011331Z-R9-cuda-helper-0c9d561fba](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063836.011331Z-R9-cuda-helper-0c9d561fba)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063854.844243Z-R9-invalid-entry-61d63c2fda](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_sparse_matrix_helpers__sparse_matrix_helpers.f90/20261111T063854.844243Z-R9-invalid-entry-61d63c2fda)
- [migration/reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597](../../../../reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597)
- [migration/reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735](../../../../reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735)
- [migration/reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d](../../../../reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d)
- [migration/reports/evidence/rewrite/R9/original-Fortran-toolchain-inventory/20261111T062651.488557Z-R9-cuda-host-0746f7e0c1](../../../../reports/evidence/rewrite/R9/original-Fortran-toolchain-inventory/20261111T062651.488557Z-R9-cuda-host-0746f7e0c1)
