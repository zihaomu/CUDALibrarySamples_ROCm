# cuDSS/nvfortran/dense_matrix_helpers::dense_matrix_helpers.cuf

**PASSED / L4**

9入口中的一个：真实C++/标准Fortran调用项目描述符C ABI，HIP分配/指针表与完整数据读回；5场景AMD/独立CPU/原生cuDSS API对照、生命周期/别名/故障和独立复审通过。仅描述符管理，不是GPU稀疏求解算法。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/nvfortran/dense_matrix_helpers/dense_matrix_helpers.cuf](../../../../../cuDSS/nvfortran/dense_matrix_helpers/dense_matrix_helpers.cuf) |
| 实际库 / 后端 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/nvfortran/dense_matrix_helpers/dense_matrix_helpers.cuf](../../../../../rocm/ported/cuDSS/nvfortran/dense_matrix_helpers/dense_matrix_helpers.cuf) |
| required cases | 8/8 |
| CUDA baseline / comparison | BLOCKED / PASSED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `0ad5c2bca1694aa127d1c26465bdd73030cab151ccf0e3d5c67cb825e267d0d3` |

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

- [migration/reports/evidence/20261109T084354.110802Z/languages/cuDSS_nvfortran_dense_matrix_helpers_dense_matrix_helpers.cuf](../../../../reports/evidence/20261109T084354.110802Z/languages/cuDSS_nvfortran_dense_matrix_helpers_dense_matrix_helpers.cuf)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_nvfortran_dense_matrix_helpers_dense_matrix_helpers.cuf](../../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_nvfortran_dense_matrix_helpers_dense_matrix_helpers.cuf)
- [migration/reports/rewrite-R9.md](../../../../reports/rewrite-R9.md)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T071910.865580Z-R9-composite-qualification-b677449ca7](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T071910.865580Z-R9-composite-qualification-b677449ca7)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063805.344962Z-R9-rocm-helper-4ec7818252](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063805.344962Z-R9-rocm-helper-4ec7818252)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063806.601430Z-R9-rocm-helper-b3d4ae26d2](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063806.601430Z-R9-rocm-helper-b3d4ae26d2)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063807.789312Z-R9-rocm-helper-7d83c3bc52](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063807.789312Z-R9-rocm-helper-7d83c3bc52)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063809.032540Z-R9-rocm-helper-5dc072fcf4](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063809.032540Z-R9-rocm-helper-5dc072fcf4)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063810.240196Z-R9-rocm-helper-cb98e03352](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063810.240196Z-R9-rocm-helper-cb98e03352)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063839.774959Z-R9-CPU-negative-a0e4a66b67](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063839.774959Z-R9-CPU-negative-a0e4a66b67)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063840.541992Z-R9-CPU-negative-7b9a7ceff5](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063840.541992Z-R9-CPU-negative-7b9a7ceff5)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063841.295639Z-R9-CPU-negative-c6c1198488](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063841.295639Z-R9-CPU-negative-c6c1198488)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063850.416060Z-R9-cuda-helper-b885d8ea41](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063850.416060Z-R9-cuda-helper-b885d8ea41)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063852.637198Z-R9-cuda-helper-37083bc7f8](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063852.637198Z-R9-cuda-helper-37083bc7f8)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063854.798896Z-R9-cuda-helper-8e27feef80](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063854.798896Z-R9-cuda-helper-8e27feef80)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063857.011935Z-R9-invalid-entry-bc3e236016](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063857.011935Z-R9-invalid-entry-bc3e236016)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063857.028552Z-R9-cuda-helper-f5ab957447](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063857.028552Z-R9-cuda-helper-f5ab957447)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063859.248122Z-R9-cuda-helper-0f0dea6b0d](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_dense_matrix_helpers__dense_matrix_helpers.cuf/20261111T063859.248122Z-R9-cuda-helper-0f0dea6b0d)
- [migration/reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597](../../../../reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597)
- [migration/reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735](../../../../reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735)
- [migration/reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d](../../../../reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d)
- [migration/reports/evidence/rewrite/R9/original-Fortran-toolchain-inventory/20261111T062651.488557Z-R9-cuda-host-0746f7e0c1](../../../../reports/evidence/rewrite/R9/original-Fortran-toolchain-inventory/20261111T062651.488557Z-R9-cuda-host-0746f7e0c1)
