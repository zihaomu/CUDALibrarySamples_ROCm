# cuDSS/nvfortran/sparse_matrix_helpers::sparse_matrix_helpers.cuf

**PASSED / L4**

9入口中的一个：真实C++/标准Fortran调用项目描述符C ABI，HIP分配/指针表与完整数据读回；5场景AMD/独立CPU/原生cuDSS API对照、生命周期/别名/故障和独立复审通过。仅描述符管理，不是GPU稀疏求解算法。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/nvfortran/sparse_matrix_helpers/sparse_matrix_helpers.cuf](../../../../../cuDSS/nvfortran/sparse_matrix_helpers/sparse_matrix_helpers.cuf) |
| 实际库 / 后端 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/nvfortran/sparse_matrix_helpers/sparse_matrix_helpers.cuf](../../../../../rocm/ported/cuDSS/nvfortran/sparse_matrix_helpers/sparse_matrix_helpers.cuf) |
| required cases | 8/8 |
| CUDA baseline / comparison | BLOCKED / PASSED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `b43ee60fe823851ca7fe271048ec3ffdc0e57a9bbd564acd02dd349a6c367713` |

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

- [migration/reports/evidence/20261109T084354.110802Z/languages/cuDSS_nvfortran_sparse_matrix_helpers_sparse_matrix_helpers.cuf](../../../../reports/evidence/20261109T084354.110802Z/languages/cuDSS_nvfortran_sparse_matrix_helpers_sparse_matrix_helpers.cuf)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_nvfortran_sparse_matrix_helpers_sparse_matrix_helpers.cuf](../../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_nvfortran_sparse_matrix_helpers_sparse_matrix_helpers.cuf)
- [migration/reports/rewrite-R9.md](../../../../reports/rewrite-R9.md)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T071911.832742Z-R9-composite-qualification-f7e55c5f56](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T071911.832742Z-R9-composite-qualification-f7e55c5f56)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063811.506581Z-R9-rocm-helper-9920b33058](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063811.506581Z-R9-rocm-helper-9920b33058)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063812.736545Z-R9-rocm-helper-dd6f5625d1](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063812.736545Z-R9-rocm-helper-dd6f5625d1)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063813.929668Z-R9-rocm-helper-a652f7fb87](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063813.929668Z-R9-rocm-helper-a652f7fb87)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063815.135705Z-R9-rocm-helper-8b6b635806](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063815.135705Z-R9-rocm-helper-8b6b635806)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063816.335084Z-R9-rocm-helper-e8dccc3f7f](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063816.335084Z-R9-rocm-helper-e8dccc3f7f)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063842.041756Z-R9-CPU-negative-6576f1c996](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063842.041756Z-R9-CPU-negative-6576f1c996)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063842.802735Z-R9-CPU-negative-52b6e8a2ef](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063842.802735Z-R9-CPU-negative-52b6e8a2ef)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063843.568779Z-R9-CPU-negative-026c65a072](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063843.568779Z-R9-CPU-negative-026c65a072)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063858.071233Z-R9-invalid-entry-fe6a5e6eb9](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063858.071233Z-R9-invalid-entry-fe6a5e6eb9)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063901.508056Z-R9-cuda-helper-ac93d01dfc](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063901.508056Z-R9-cuda-helper-ac93d01dfc)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063903.735035Z-R9-cuda-helper-246e5eb590](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063903.735035Z-R9-cuda-helper-246e5eb590)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063905.950732Z-R9-cuda-helper-c06f12e757](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063905.950732Z-R9-cuda-helper-c06f12e757)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063908.179787Z-R9-cuda-helper-267681f80b](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063908.179787Z-R9-cuda-helper-267681f80b)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063910.403210Z-R9-cuda-helper-a29098445f](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_sparse_matrix_helpers__sparse_matrix_helpers.cuf/20261111T063910.403210Z-R9-cuda-helper-a29098445f)
- [migration/reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597](../../../../reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597)
- [migration/reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735](../../../../reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735)
- [migration/reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d](../../../../reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d)
- [migration/reports/evidence/rewrite/R9/original-Fortran-toolchain-inventory/20261111T062651.488557Z-R9-cuda-host-0746f7e0c1](../../../../reports/evidence/rewrite/R9/original-Fortran-toolchain-inventory/20261111T062651.488557Z-R9-cuda-host-0746f7e0c1)
