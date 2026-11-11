# cuDSS/simple_sparse_matrix_helpers::simple_sparse_matrix_helpers.cpp

**PASSED / L4**

9入口中的一个：真实C++/标准Fortran调用项目描述符C ABI，HIP分配/指针表与完整数据读回；5场景AMD/独立CPU/原生cuDSS API对照、生命周期/别名/故障和独立复审通过。仅描述符管理，不是GPU稀疏求解算法。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/simple_sparse_matrix_helpers/simple_sparse_matrix_helpers.cpp](../../../../cuDSS/simple_sparse_matrix_helpers/simple_sparse_matrix_helpers.cpp) |
| 实际库 / 后端 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/simple_sparse_matrix_helpers/simple_sparse_matrix_helpers.cpp](../../../../rocm/ported/cuDSS/simple_sparse_matrix_helpers/simple_sparse_matrix_helpers.cpp) |
| required cases | 8/8 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `a14782439936e4e0db1bd1f1877419c4e3d9593bb0d3e43ea4b2a831eb499764` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite/original`, `rewrite/changed-values`, `rewrite/irregular`, `rewrite/alternate-base`, `rewrite/repeat`, `rewrite/negative-and-runtime`, `rewrite/sealed-build-and-native-identities`, `rewrite/independent-source-review`。

实现方式：`PROJECT_DESCRIPTOR_ABI_WITH_HIP_STORAGE`。

恢复/扩展条件：扩展API/精度/布局/设备或性能声明时重新冻结合同并完成实际GPU与独立参考验收。

CUDA 对照限制：原始CUDA C++程序及同输入native cuDSS API对照通过。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuDSS/simple_sparse_matrix_helpers/simple_sparse_matrix_helpers.cpp:24:10: fatal error: 'cudss.h' file not found

尝试库：—；实现 hash：`12c70270c9d51c6b745353dba4ae62a2d3721b6d18e1eda1b2755cce1312b3d7`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python3 tools/moat/build_helpers.py
python3 tools/moat/run_helpers.py
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuDSS_simple_sparse_matrix_helpers_simple_sparse_matrix_helpers.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/cuDSS_simple_sparse_matrix_helpers_simple_sparse_matrix_helpers.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuDSS_simple_sparse_matrix_helpers_simple_sparse_matrix_helpers.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/cuDSS_simple_sparse_matrix_helpers_simple_sparse_matrix_helpers.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuDSS_simple_sparse_matrix_helpers_simple_sparse_matrix_helpers.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/cuDSS_simple_sparse_matrix_helpers_simple_sparse_matrix_helpers.cpp)
- [migration/reports/rewrite-R9.md](../../../reports/rewrite-R9.md)
- [migration/reports/rewrite-R9-helper-originals.json](../../../reports/rewrite-R9-helper-originals.json)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T062644.949086Z-R9-cuda-original-7f2e8b5098](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T062644.949086Z-R9-cuda-original-7f2e8b5098)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T071905.821040Z-R9-composite-qualification-37ab0f258e](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T071905.821040Z-R9-composite-qualification-37ab0f258e)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063733.375072Z-R9-rocm-helper-e8fab86bd6](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063733.375072Z-R9-rocm-helper-e8fab86bd6)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063734.629973Z-R9-rocm-helper-78c2f23638](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063734.629973Z-R9-rocm-helper-78c2f23638)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063735.909656Z-R9-rocm-helper-60558a752a](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063735.909656Z-R9-rocm-helper-60558a752a)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063737.202777Z-R9-rocm-helper-59afb97c06](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063737.202777Z-R9-rocm-helper-59afb97c06)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063738.459977Z-R9-rocm-helper-7fd5d34439](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063738.459977Z-R9-rocm-helper-7fd5d34439)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063752.578769Z-R9-cuda-helper-6ab70e920e](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063752.578769Z-R9-cuda-helper-6ab70e920e)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063754.805746Z-R9-cuda-helper-1383127014](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063754.805746Z-R9-cuda-helper-1383127014)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063757.019969Z-R9-cuda-helper-bf901a8fac](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063757.019969Z-R9-cuda-helper-bf901a8fac)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063759.242747Z-R9-cuda-helper-0aa5ddea7f](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063759.242747Z-R9-cuda-helper-0aa5ddea7f)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063801.465138Z-R9-cuda-helper-fe4c2dcbc7](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063801.465138Z-R9-cuda-helper-fe4c2dcbc7)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063826.477486Z-R9-CPU-negative-73a109f598](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063826.477486Z-R9-CPU-negative-73a109f598)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063827.255053Z-R9-CPU-negative-c8d8de8371](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063827.255053Z-R9-CPU-negative-c8d8de8371)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063828.037960Z-R9-CPU-negative-fae2e8843c](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063828.037960Z-R9-CPU-negative-fae2e8843c)
- [migration/reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063851.638407Z-R9-invalid-entry-4c0650d9b5](../../../reports/evidence/rewrite/R9/cuDSS_simple_sparse_matrix_helpers__simple_sparse_matrix_helpers.cpp/20261111T063851.638407Z-R9-invalid-entry-4c0650d9b5)
- [migration/reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597](../../../reports/evidence/rewrite/R9/matrix-helper-ABI-negative/20261111T063900.215664Z-R9-rocm-ABI-037c056597)
- [migration/reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735](../../../reports/evidence/rewrite/R9/matrix-helper-language-builds/20261111T063716.921772Z-R9-rocm-build-af4c1c9735)
- [migration/reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d](../../../reports/evidence/rewrite/R9/matrix-helpers-native-cuDSS/20261111T063715.699322Z-R9-cuda-build-1ecd936b9d)
