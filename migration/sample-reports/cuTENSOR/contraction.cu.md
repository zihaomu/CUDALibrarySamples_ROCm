# cuTENSOR::contraction.cu

**PASSED / L4**

hipTensor 在 gfx1201 拒绝 FP32 contraction，FP16 compute 探针亦有数值失败；选用 rocBLAS SGEMM + HIP 排列，保留原始 modes/extents、FP32、alpha=1.1/beta=0。小尺寸全量 CPU（beta=0.5）及原始规模全量有限值/32 个双精度 CPU 抽样点通过。未声称原始随机输入逐值等同或 JIT/cache 已实现。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuTENSOR/contraction.cu](../../../cuTENSOR/contraction.cu) |
| 实际库 / 后端 | rocBLAS + HIP / FP32 GEMM and GPU tensor permutations |
| 候选路线 | hipTensor, rocBLAS + HIP permutations |
| 代码 | [rocm/probes/tensor_rocblas.hip](../../../rocm/probes/tensor_rocblas.hip) |
| required cases | 3/3 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `9e1ee206bf277ea59d8907106e2ad47dd2dc3a68aba83cf7314a0e197e8b43a4` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`small-four-dimensional-full-cpu-beta`, `original-extents-fp32-all-finite`, `original-extents-32-cpu-dot-products`。

实现方式：`HYBRID_HIP`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

run 失败：Total memory: 0.45 GiB Exception caught! Exiting. HIPTENSOR_STATUS_ARCH_MISMATCH

尝试库：hiptensor；实现 hash：`0df80670531b302a7cd477131d8acdb99367d976461f206c57a6183c3a9c69ea`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python tools/migration/probes.py tensor_rocblas
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuTENSOR_contraction.cu](../../reports/evidence/20261109T083217.050455Z/original-rocm/cuTENSOR_contraction.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSOR_contraction.cu](../../reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSOR_contraction.cu)
- [migration/reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_contraction.cu](../../reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_contraction.cu)
- [migration/reports/evidence/20261109T091046.204877Z/native-probes/tensor_rocblas](../../reports/evidence/20261109T091046.204877Z/native-probes/tensor_rocblas)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_contraction.cu](../../reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_contraction.cu)
