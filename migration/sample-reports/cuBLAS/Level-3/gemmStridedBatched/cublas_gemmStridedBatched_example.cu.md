# cuBLAS/Level-3/gemmStridedBatched::cublas_gemmStridedBatched_example.cu

**PASSED / L4**

使用 hipBLAS（rocBLAS）成功实现原始 profile 和 5 个数值用例，并通过 CUDA 对照

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLAS/Level-3/gemmStridedBatched/cublas_gemmStridedBatched_example.cu](../../../../../cuBLAS/Level-3/gemmStridedBatched/cublas_gemmStridedBatched_example.cu) |
| 实际库 / 后端 | hipBLAS / rocBLAS |
| 候选路线 | hipBLAS, rocBLAS |
| 代码 | [rocm/cuBLAS/Level-3/gemmStridedBatched/sample.cpp](../../../../../rocm/cuBLAS/Level-3/gemmStridedBatched/sample.cpp) |
| required cases | 5/5 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `3abd15b8dace24d1d786b21beb28c1e1c68cfeeb29f15d77ff9b7adf9431a77b` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`transpose0_beta0.000000`, `transpose0_beta0.500000`, `transpose1_beta0.000000`, `transpose1_beta0.500000`, `original_profile`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：—；实现 hash：`7dc48065df8e3ab2995c5d3f494f2fee820052c114892dd5ea3ebb7f651d0b26`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

```bash
HIP_VISIBLE_DEVICES=2 tools/migration/run_rocm.sh --filter cuBLAS/Level-3/gemmStridedBatched
```

- [migration/reports/evidence/20261109T074106.668062Z/rocm/cuBLAS_Level-3_gemmStridedBatched](../../../../reports/evidence/20261109T074106.668062Z/rocm/cuBLAS_Level-3_gemmStridedBatched)
- [migration/reports/evidence/20261109T074136.696317Z/rocm/cuBLAS_Level-3_gemmStridedBatched](../../../../reports/evidence/20261109T074136.696317Z/rocm/cuBLAS_Level-3_gemmStridedBatched)
- [migration/reports/evidence/20261109T074302.621128Z/rocm/cuBLAS_Level-3_gemmStridedBatched](../../../../reports/evidence/20261109T074302.621128Z/rocm/cuBLAS_Level-3_gemmStridedBatched)
- [migration/reports/evidence/20261109T074409.357725Z/rocm/cuBLAS_Level-3_gemmStridedBatched](../../../../reports/evidence/20261109T074409.357725Z/rocm/cuBLAS_Level-3_gemmStridedBatched)
- [migration/reports/evidence/20261109T075141.556119Z/rocm/cuBLAS_Level-3_gemmStridedBatched](../../../../reports/evidence/20261109T075141.556119Z/rocm/cuBLAS_Level-3_gemmStridedBatched)
- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Level-3_gemmStridedBatched_cublas_gemmStridedBatched_example.cu](../../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Level-3_gemmStridedBatched_cublas_gemmStridedBatched_example.cu)
- [migration/reports/evidence/20261109T081304.129128Z/rocm/cuBLAS_Level-3_gemmStridedBatched](../../../../reports/evidence/20261109T081304.129128Z/rocm/cuBLAS_Level-3_gemmStridedBatched)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Level-3_gemmStridedBatched_cublas_gemmStridedBatched_example.cu](../../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Level-3_gemmStridedBatched_cublas_gemmStridedBatched_example.cu)
- [migration/reports/evidence/20261109T081401.539900Z/rocm/cuBLAS_Level-3_gemmStridedBatched](../../../../reports/evidence/20261109T081401.539900Z/rocm/cuBLAS_Level-3_gemmStridedBatched)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Level-3_gemmStridedBatched_cublas_gemmStridedBatched_example.cu](../../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Level-3_gemmStridedBatched_cublas_gemmStridedBatched_example.cu)
- [migration/reports/evidence/20261109T081927.659318Z/rocm/cuBLAS_Level-3_gemmStridedBatched](../../../../reports/evidence/20261109T081927.659318Z/rocm/cuBLAS_Level-3_gemmStridedBatched)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Level-3_gemmStridedBatched_cublas_gemmStridedBatched_example.cu](../../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Level-3_gemmStridedBatched_cublas_gemmStridedBatched_example.cu)
- [migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Level-3_gemmStridedBatched_cublas_gemmStridedBatched_example.cu](../../../../reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Level-3_gemmStridedBatched_cublas_gemmStridedBatched_example.cu)
- [migration/reports/blas-three-way.json](../../../../reports/blas-three-way.json)
- [migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_gemmStridedBatched_cublas_gemmStridedBatched_example.cu](../../../../reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_gemmStridedBatched_cublas_gemmStridedBatched_example.cu)
