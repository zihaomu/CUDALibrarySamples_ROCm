# cuDSS/fortran/dense_matrix_helpers::dense_matrix_helpers.f90

**PASSED / L4**

9入口中的一个：真实C++/标准Fortran调用项目描述符C ABI，HIP分配/指针表与完整数据读回；5场景AMD/独立CPU/原生cuDSS API对照、生命周期/别名/故障和独立复审通过。仅描述符管理，不是GPU稀疏求解算法。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/fortran/dense_matrix_helpers/dense_matrix_helpers.f90](../../../../../cuDSS/fortran/dense_matrix_helpers/dense_matrix_helpers.f90) |
| 实际库 / 后端 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/fortran/dense_matrix_helpers/dense_matrix_helpers.f90](../../../../../rocm/ported/cuDSS/fortran/dense_matrix_helpers/dense_matrix_helpers.f90) |
| required cases | 8/8 |
| CUDA baseline / comparison | BLOCKED / PASSED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `73ae92f810e32324ee25d6d281b2ee0a0eacf3f67b2177d8240f02ef326a446f` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite/original`, `rewrite/changed-values`, `rewrite/irregular`, `rewrite/padding`, `rewrite/repeat`, `rewrite/negative-and-runtime`, `rewrite/sealed-build-and-native-identities`, `rewrite/independent-source-review`。

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

- [migration/reports/evidence/20261109T084354.110802Z/languages/cuDSS_fortran_dense_matrix_helpers_dense_matrix_helpers.f90](../../../../reports/evidence/20261109T084354.110802Z/languages/cuDSS_fortran_dense_matrix_helpers_dense_matrix_helpers.f90)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_fortran_dense_matrix_helpers_dense_matrix_helpers.f90](../../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_fortran_dense_matrix_helpers_dense_matrix_helpers.f90)
- [migration/reports/rewrite-R9.md](../../../../reports/rewrite-R9.md)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T071907.861255Z-R9-composite-qualification-5da8e53276](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T071907.861255Z-R9-composite-qualification-5da8e53276)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063746.248096Z-R9-rocm-helper-140d983790](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063746.248096Z-R9-rocm-helper-140d983790)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063747.465545Z-R9-rocm-helper-11a81f4e6a](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063747.465545Z-R9-rocm-helper-11a81f4e6a)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063748.736278Z-R9-rocm-helper-4af9b1fa3b](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063748.736278Z-R9-rocm-helper-4af9b1fa3b)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063749.992745Z-R9-rocm-helper-30c4bb1bc3](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063749.992745Z-R9-rocm-helper-30c4bb1bc3)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063751.246448Z-R9-rocm-helper-ea0a6bd4a3](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063751.246448Z-R9-rocm-helper-ea0a6bd4a3)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063815.880096Z-R9-cuda-helper-cc2443218f](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063815.880096Z-R9-cuda-helper-cc2443218f)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063818.075497Z-R9-cuda-helper-3190dd375a](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063818.075497Z-R9-cuda-helper-3190dd375a)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063820.261193Z-R9-cuda-helper-b7b5b941df](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063820.261193Z-R9-cuda-helper-b7b5b941df)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063822.478729Z-R9-cuda-helper-898360920b](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063822.478729Z-R9-cuda-helper-898360920b)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063824.708960Z-R9-cuda-helper-c7d5e1d03d](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063824.708960Z-R9-cuda-helper-c7d5e1d03d)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063831.956771Z-R9-CPU-negative-a739ee496c](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063831.956771Z-R9-CPU-negative-a739ee496c)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063832.750658Z-R9-CPU-negative-9bc86c2985](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063832.750658Z-R9-CPU-negative-9bc86c2985)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063833.521804Z-R9-CPU-negative-5effbe7e97](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063833.521804Z-R9-CPU-negative-5effbe7e97)
- [migration/reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063853.797655Z-R9-invalid-entry-f2e81d0cc7](../../../../reports/evidence/rewrite/R9/cuDSS_fortran_dense_matrix_helpers__dense_matrix_helpers.f90/20261111T063853.797655Z-R9-invalid-entry-f2e81d0cc7)
- [migration/reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597](../../../../reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597)
- [migration/reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735](../../../../reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735)
- [migration/reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d](../../../../reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d)
- [migration/reports/evidence/rewrite/R9/original-Fortran-toolchain-inventory/20261111T062651.488557Z-R9-cuda-host-0746f7e0c1](../../../../reports/evidence/rewrite/R9/original-Fortran-toolchain-inventory/20261111T062651.488557Z-R9-cuda-host-0746f7e0c1)
