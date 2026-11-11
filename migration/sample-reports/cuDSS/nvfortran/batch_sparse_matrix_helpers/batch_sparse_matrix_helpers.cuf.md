# cuDSS/nvfortran/batch_sparse_matrix_helpers::batch_sparse_matrix_helpers.cuf

**PASSED / L4**

9入口中的一个：真实C++/标准Fortran调用项目描述符C ABI，HIP分配/指针表与完整数据读回；5场景AMD/独立CPU/原生cuDSS API对照、生命周期/别名/故障和独立复审通过。仅描述符管理，不是GPU稀疏求解算法。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/nvfortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.cuf](../../../../../cuDSS/nvfortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.cuf) |
| 实际库 / 后端 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/nvfortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.cuf](../../../../../rocm/ported/cuDSS/nvfortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.cuf) |
| required cases | 8/8 |
| CUDA baseline / comparison | BLOCKED / PASSED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `c9540ea356dde1ad33eaf2d3d250d0054b9083d4178d5d52a861660b8ae06d8e` |

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

- [migration/reports/evidence/20261109T084354.110802Z/languages/cuDSS_nvfortran_batch_sparse_matrix_helpers_batch_sparse_matrix_helpers.cuf](../../../../reports/evidence/20261109T084354.110802Z/languages/cuDSS_nvfortran_batch_sparse_matrix_helpers_batch_sparse_matrix_helpers.cuf)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_nvfortran_batch_sparse_matrix_helpers_batch_sparse_matrix_helpers.cuf](../../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_nvfortran_batch_sparse_matrix_helpers_batch_sparse_matrix_helpers.cuf)
- [migration/reports/rewrite-R9.md](../../../../reports/rewrite-R9.md)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T071912.911566Z-R9-composite-qualification-b00affec61](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T071912.911566Z-R9-composite-qualification-b00affec61)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063817.511271Z-R9-rocm-helper-e552dab5f6](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063817.511271Z-R9-rocm-helper-e552dab5f6)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063818.757044Z-R9-rocm-helper-dc8c2a60e2](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063818.757044Z-R9-rocm-helper-dc8c2a60e2)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063820.006955Z-R9-rocm-helper-2e017bf523](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063820.006955Z-R9-rocm-helper-2e017bf523)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063821.268609Z-R9-rocm-helper-4f242d13d4](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063821.268609Z-R9-rocm-helper-4f242d13d4)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063822.526897Z-R9-rocm-helper-6012bf0d03](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063822.526897Z-R9-rocm-helper-6012bf0d03)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063844.347691Z-R9-CPU-negative-b9f464f10a](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063844.347691Z-R9-CPU-negative-b9f464f10a)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063845.111249Z-R9-CPU-negative-3d2ce866ba](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063845.111249Z-R9-CPU-negative-3d2ce866ba)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063845.884170Z-R9-CPU-negative-3a8bac8afc](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063845.884170Z-R9-CPU-negative-3a8bac8afc)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063846.653318Z-R9-CPU-negative-869433a7f5](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063846.653318Z-R9-CPU-negative-869433a7f5)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063859.132181Z-R9-invalid-entry-ab6f4bb4f2](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063859.132181Z-R9-invalid-entry-ab6f4bb4f2)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063912.823530Z-R9-cuda-helper-3f5b690e5c](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063912.823530Z-R9-cuda-helper-3f5b690e5c)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063915.154675Z-R9-cuda-helper-9470af89fd](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063915.154675Z-R9-cuda-helper-9470af89fd)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063917.493488Z-R9-cuda-helper-279b85605a](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063917.493488Z-R9-cuda-helper-279b85605a)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063919.884091Z-R9-cuda-helper-df74772982](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063919.884091Z-R9-cuda-helper-df74772982)
- [migration/reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063922.228814Z-R9-cuda-helper-b69b5b5166](../../../../reports/evidence/rewrite/R9/cuDSS_nvfortran_batch_sparse_matrix_helpers__batch_sparse_matrix_helpers.cuf/20261111T063922.228814Z-R9-cuda-helper-b69b5b5166)
- [migration/reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597](../../../../reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597)
- [migration/reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735](../../../../reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735)
- [migration/reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d](../../../../reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d)
- [migration/reports/evidence/rewrite/R9/original-Fortran-toolchain-inventory/20261111T062651.488557Z-R9-cuda-host-0746f7e0c1](../../../../reports/evidence/rewrite/R9/original-Fortran-toolchain-inventory/20261111T062651.488557Z-R9-cuda-host-0746f7e0c1)
