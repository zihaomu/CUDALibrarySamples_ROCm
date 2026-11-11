# cuDSS/simple_batch_sparse_matrix_helpers::simple_batch_sparse_matrix_helpers.cpp

**PASSED / L4**

9入口中的一个：真实C++/标准Fortran调用项目描述符C ABI，HIP分配/指针表与完整数据读回；5场景AMD/独立CPU/原生cuDSS API对照、生命周期/别名/故障和独立复审通过。仅描述符管理，不是GPU稀疏求解算法。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/simple_batch_sparse_matrix_helpers/simple_batch_sparse_matrix_helpers.cpp](../../../../cuDSS/simple_batch_sparse_matrix_helpers/simple_batch_sparse_matrix_helpers.cpp) |
| 实际库 / 后端 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/simple_batch_sparse_matrix_helpers/simple_batch_sparse_matrix_helpers.cpp](../../../../rocm/ported/cuDSS/simple_batch_sparse_matrix_helpers/simple_batch_sparse_matrix_helpers.cpp) |
| required cases | 8/8 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `6dbf150c67e3faa31e178f18a45dc87a8b443dc59c546db3153967837bf39428` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite/original`, `rewrite/changed-values`, `rewrite/irregular`, `rewrite/alternate-base`, `rewrite/repeat`, `rewrite/negative-and-runtime`, `rewrite/sealed-build-and-native-identities`, `rewrite/independent-source-review`。

实现方式：`PROJECT_DESCRIPTOR_ABI_WITH_HIP_STORAGE`。

恢复/扩展条件：扩展API/精度/布局/设备或性能声明时重新冻结合同并完成实际GPU与独立参考验收。

CUDA 对照限制：原始CUDA C++程序及同输入native cuDSS API对照通过。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuDSS/simple_batch_sparse_matrix_helpers/simple_batch_sparse_matrix_helpers.cpp:25:10: fatal error: 'cudss.h' file not found

尝试库：—；实现 hash：`706bb5a48a1b1970cba0b6e42700b89aeff2a67d6e7725ac2e6f77e2be4d01a8`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python3 tools/moat/build_helpers.py
python3 tools/moat/run_helpers.py
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuDSS_simple_batch_sparse_matrix_helpers_simple_batch_sparse_matrix_helpers.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/cuDSS_simple_batch_sparse_matrix_helpers_simple_batch_sparse_matrix_helpers.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuDSS_simple_batch_sparse_matrix_helpers_simple_batch_sparse_matrix_helpers.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/cuDSS_simple_batch_sparse_matrix_helpers_simple_batch_sparse_matrix_helpers.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuDSS_simple_batch_sparse_matrix_helpers_simple_batch_sparse_matrix_helpers.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/cuDSS_simple_batch_sparse_matrix_helpers_simple_batch_sparse_matrix_helpers.cpp)
- [migration/reports/rewrite-R9.md](../../../reports/rewrite-R9.md)
- [migration/reports/rewrite-R9-helper-originals.json](../../../reports/rewrite-R9-helper-originals.json)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T062648.012712Z-R9-cuda-original-8d2709f6b8](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T062648.012712Z-R9-cuda-original-8d2709f6b8)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T071906.890915Z-R9-composite-qualification-25b7806c68](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T071906.890915Z-R9-composite-qualification-25b7806c68)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063739.756050Z-R9-rocm-helper-780d060d31](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063739.756050Z-R9-rocm-helper-780d060d31)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063741.022541Z-R9-rocm-helper-a62923560e](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063741.022541Z-R9-rocm-helper-a62923560e)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063742.301276Z-R9-rocm-helper-bb020ababf](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063742.301276Z-R9-rocm-helper-bb020ababf)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063743.587059Z-R9-rocm-helper-6e1f8d9dd1](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063743.587059Z-R9-rocm-helper-6e1f8d9dd1)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063744.882449Z-R9-rocm-helper-79702e6b3c](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063744.882449Z-R9-rocm-helper-79702e6b3c)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063803.838456Z-R9-cuda-helper-452da10a52](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063803.838456Z-R9-cuda-helper-452da10a52)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063806.153763Z-R9-cuda-helper-3ba8f47bdc](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063806.153763Z-R9-cuda-helper-3ba8f47bdc)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063808.476992Z-R9-cuda-helper-bcb019592d](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063808.476992Z-R9-cuda-helper-bcb019592d)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063810.817600Z-R9-cuda-helper-77368b9689](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063810.817600Z-R9-cuda-helper-77368b9689)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063813.149159Z-R9-cuda-helper-62eaaf7f1b](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063813.149159Z-R9-cuda-helper-62eaaf7f1b)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063828.812860Z-R9-CPU-negative-ac880de1f5](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063828.812860Z-R9-CPU-negative-ac880de1f5)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063829.609161Z-R9-CPU-negative-3b361c8590](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063829.609161Z-R9-CPU-negative-3b361c8590)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063830.395461Z-R9-CPU-negative-0f07a2ea2e](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063830.395461Z-R9-CPU-negative-0f07a2ea2e)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063831.177296Z-R9-CPU-negative-74917446df](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063831.177296Z-R9-CPU-negative-74917446df)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063852.742012Z-R9-invalid-entry-6423f1aa66](../../../reports/evidence/rewrite/R9/cuDSS_simple_batch_sparse_matrix_helpers__simple_batch_sparse_matrix_helpers.cpp/20261111T063852.742012Z-R9-invalid-entry-6423f1aa66)
- [migration/reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597](../../../reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597)
- [migration/reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735](../../../reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735)
- [migration/reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d](../../../reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d)
