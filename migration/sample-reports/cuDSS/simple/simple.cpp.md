# cuDSS/simple::simple.cpp

**PASSED / L4**

使用 CPU 稀疏图消去构造符号 L pattern，rocSOLVER CSRRF 在 GPU 上完成稀疏 Cholesky 数值分解和求解；保留原始 FP64 upper-CSR 5×5 SPD 与 RHS，解/残差及缩放矩阵检查通过。未转 dense；高级 cuDSS 接口未覆盖。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/simple/simple.cpp](../../../../cuDSS/simple/simple.cpp) |
| 实际库 / 后端 | rocSOLVER CSRRF + rocBLAS / GPU sparse Cholesky; CPU sparse symbolic analysis |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/cuDSS/simple/sample.cpp](../../../../rocm/cuDSS/simple/sample.cpp) |
| required cases | 3/3 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `f8cdb725eca4b9e19a4b59bc216dab522ac53261227c959d7e712016a881c587` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-upper-csr-solution`, `original-upper-csr-residual`, `scaled-matrix-solution-residual`。

实现方式：`LIBRARY_REWRITE`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuDSS/simple/simple.cpp:25:10: fatal error: 'cudss.h' file not found

尝试库：—；实现 hash：`7ed4010591378f6037ebcc267cab838a62ee9a88ede273ac1e57160fe8b6d515`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python tools/migration/probes.py rocsolver_sparse_chol
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuDSS_simple_simple.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/cuDSS_simple_simple.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuDSS_simple_simple.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/cuDSS_simple_simple.cpp)
- [migration/reports/evidence/20261109T095702.306683Z/native-probes/rocsolver_sparse_chol](../../../reports/evidence/20261109T095702.306683Z/native-probes/rocsolver_sparse_chol)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuDSS_simple_simple.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/cuDSS_simple_simple.cpp)
