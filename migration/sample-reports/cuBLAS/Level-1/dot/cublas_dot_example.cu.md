# cuBLAS/Level-1/dot::cublas_dot_example.cu

**PASSED / L4**

使用 hipBLAS（rocBLAS）成功实现原始 profile 和 9 个数值用例，并通过 CUDA 对照

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLAS/Level-1/dot/cublas_dot_example.cu](../../../../../cuBLAS/Level-1/dot/cublas_dot_example.cu) |
| 实际库 / 后端 | hipBLAS / rocBLAS |
| 候选路线 | hipBLAS, rocBLAS |
| 代码 | [rocm/cuBLAS/Level-1/dot/sample.cpp](../../../../../rocm/cuBLAS/Level-1/dot/sample.cpp) |
| required cases | 9/9 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `e58ba14a2e18567af6e00dd5743b34de384da8a2cd24823a267013ff415ad7b7` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`n4_stride1_mode0`, `n4_stride1_mode1`, `n4_stride2_mode0`, `n4_stride2_mode1`, `n17_stride1_mode0`, `n17_stride1_mode1`, `n17_stride2_mode0`, `n17_stride2_mode1`, `original_profile`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：—；实现 hash：`a87bc34c26c684946a07b09a6f40e51bb6ce9eac9203215e62badc9fd8d1c80c`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

```bash
HIP_VISIBLE_DEVICES=2 tools/migration/run_rocm.sh --filter cuBLAS/Level-1/dot
```

- [migration/reports/evidence/20261109T074106.668062Z/rocm/cuBLAS_Level-1_dot](../../../../reports/evidence/20261109T074106.668062Z/rocm/cuBLAS_Level-1_dot)
- [migration/reports/evidence/20261109T074136.696317Z/rocm/cuBLAS_Level-1_dot](../../../../reports/evidence/20261109T074136.696317Z/rocm/cuBLAS_Level-1_dot)
- [migration/reports/evidence/20261109T074302.621128Z/rocm/cuBLAS_Level-1_dot](../../../../reports/evidence/20261109T074302.621128Z/rocm/cuBLAS_Level-1_dot)
- [migration/reports/evidence/20261109T074409.357725Z/rocm/cuBLAS_Level-1_dot](../../../../reports/evidence/20261109T074409.357725Z/rocm/cuBLAS_Level-1_dot)
- [migration/reports/evidence/20261109T075141.556119Z/rocm/cuBLAS_Level-1_dot](../../../../reports/evidence/20261109T075141.556119Z/rocm/cuBLAS_Level-1_dot)
- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Level-1_dot_cublas_dot_example.cu](../../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Level-1_dot_cublas_dot_example.cu)
- [migration/reports/evidence/20261109T081304.129128Z/rocm/cuBLAS_Level-1_dot](../../../../reports/evidence/20261109T081304.129128Z/rocm/cuBLAS_Level-1_dot)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Level-1_dot_cublas_dot_example.cu](../../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Level-1_dot_cublas_dot_example.cu)
- [migration/reports/evidence/20261109T081401.539900Z/rocm/cuBLAS_Level-1_dot](../../../../reports/evidence/20261109T081401.539900Z/rocm/cuBLAS_Level-1_dot)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Level-1_dot_cublas_dot_example.cu](../../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Level-1_dot_cublas_dot_example.cu)
- [migration/reports/evidence/20261109T081927.659318Z/rocm/cuBLAS_Level-1_dot](../../../../reports/evidence/20261109T081927.659318Z/rocm/cuBLAS_Level-1_dot)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Level-1_dot_cublas_dot_example.cu](../../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Level-1_dot_cublas_dot_example.cu)
- [migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Level-1_dot_cublas_dot_example.cu](../../../../reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Level-1_dot_cublas_dot_example.cu)
- [migration/reports/blas-three-way.json](../../../../reports/blas-three-way.json)
- [migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-1_dot_cublas_dot_example.cu](../../../../reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-1_dot_cublas_dot_example.cu)
