# cuDSS/fortran/batch_sparse_matrix_helpers::batch_sparse_matrix_helpers.f90

**PASSED / L4**

9入口中的一个：真实C++/标准Fortran调用项目描述符C ABI，HIP分配/指针表与完整数据读回；5场景AMD/独立CPU/原生cuDSS API对照、生命周期/别名/故障和独立复审通过。仅描述符管理，不是GPU稀疏求解算法。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/fortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.f90](../../../../../cuDSS/fortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.f90) |
| 实际库 / 后端 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/fortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.f90](../../../../../rocm/ported/cuDSS/fortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.f90) |
| required cases | 8/8 |
| CUDA baseline / comparison | BLOCKED / PASSED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `30ef22aac987bbb0048be4e390fba2f9a8fea4032d2d1854febaea08940dd870` |

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

- [migration/reports/evidence/20261109T084354.110802Z/languages/cuDSS_fortran_batch_sparse_matrix_helpers_batch_sparse_matrix_helpers.f90](../../../../reports/evidence/20261109T084354.110802Z/languages/cuDSS_fortran_batch_sparse_matrix_helpers_batch_sparse_matrix_helpers.f90)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_fortran_batch_sparse_matrix_helpers_batch_sparse_matrix_helpers.f90](../../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_fortran_batch_sparse_matrix_helpers_batch_sparse_matrix_helpers.f90)
- [migration/reports/rewrite-R9.md](../../../../reports/rewrite-R9.md)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T071909.897967Z-R9-composite-qualification-83e60f7722](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T071909.897967Z-R9-composite-qualification-83e60f7722)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063758.830657Z-R9-rocm-helper-f5be3459bf](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063758.830657Z-R9-rocm-helper-f5be3459bf)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063800.089745Z-R9-rocm-helper-d6eda05e09](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063800.089745Z-R9-rocm-helper-d6eda05e09)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063801.391615Z-R9-rocm-helper-58027f915f](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063801.391615Z-R9-rocm-helper-58027f915f)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063802.680299Z-R9-rocm-helper-c256ea2319](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063802.680299Z-R9-rocm-helper-c256ea2319)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063803.935741Z-R9-rocm-helper-a44ce73026](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063803.935741Z-R9-rocm-helper-a44ce73026)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063836.584413Z-R9-CPU-negative-c644c38b0f](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063836.584413Z-R9-CPU-negative-c644c38b0f)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063837.390324Z-R9-CPU-negative-a6583326dc](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063837.390324Z-R9-CPU-negative-a6583326dc)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063838.181553Z-R9-CPU-negative-bbc55e0982](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063838.181553Z-R9-CPU-negative-bbc55e0982)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063838.400254Z-R9-cuda-helper-166004765c](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063838.400254Z-R9-cuda-helper-166004765c)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063839.009399Z-R9-CPU-negative-5424635b96](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063839.009399Z-R9-CPU-negative-5424635b96)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063840.739214Z-R9-cuda-helper-a2794c7f02](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063840.739214Z-R9-cuda-helper-a2794c7f02)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063843.113321Z-R9-cuda-helper-e7f27d9cb4](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063843.113321Z-R9-cuda-helper-e7f27d9cb4)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063845.393597Z-R9-cuda-helper-5265db8eed](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063845.393597Z-R9-cuda-helper-5265db8eed)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063847.667773Z-R9-cuda-helper-8996e04851](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063847.667773Z-R9-cuda-helper-8996e04851)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063855.933942Z-R9-invalid-entry-8c7f3c0ef6](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.f90/20261111T063855.933942Z-R9-invalid-entry-8c7f3c0ef6)
- [migration/reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597](../../../../reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597)
- [migration/reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735](../../../../reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735)
- [migration/reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d](../../../../reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d)
- [migration/reports/evidence/rewrite/R9/original-Fortran-toolchain-inventory/20261111T062651.488557Z-R9-cuda-host-0746f7e0c1](../../../../reports/evidence/rewrite/R9/original-Fortran-toolchain-inventory/20261111T062651.488557Z-R9-cuda-host-0746f7e0c1)
