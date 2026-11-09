# cuFFT/1d_mgpu_c2c::1d_mgpu_c2c_example.cpp

**PASSED / L4**

hipFFT Xt 不接受该单 batch 1D 配置，改用两卡各做 128 点 hipFFT、RCCL AllGather 和 HIP radix-2 合并；保留原始 n=256、FP32、两卡与全局布局，全部复数输出通过 CPU DFT。原 CUDA 重复 {0,0} 设备配置在对照副本中修正为 {0,1}。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuFFT/1d_mgpu_c2c/1d_mgpu_c2c_example.cpp](../../../../cuFFT/1d_mgpu_c2c/1d_mgpu_c2c_example.cpp) |
| 实际库 / 后端 | hipFFT + RCCL + HIP / Two GPU radix decomposition and GPU merge |
| 候选路线 | hipFFT, rocFFT, RCCL + HIP (distributed alternative) |
| 代码 | [rocm/probes/distributed_fft.hip](../../../../rocm/probes/distributed_fft.hip) |
| required cases | 1/1 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `eecde7c5b00f6e3d30bab97a2c7280d1d0a5c2919114445e8c9241e2fdcf1048` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-n256-seed3-two-gpu-full-cpu-dft`。

实现方式：`HYBRID_HIP`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

run 失败：ERROR: CUFFT call "hipfftMakePlan1d(plan, fft[0], HIPFFT_C2C, batch_size, workspace_sizes)" in line 97 of file /home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuFFT/1d_mgpu_c2c/1d_mgpu_c2c_example.cpp failed with code (14).；ERROR: CUFFT call "hipfftXtMalloc(plan, &indesc, subformat)" in line 102 of file /home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuFFT/1d_mgpu_c2c/1d_mgpu_c2c_example.cpp failed with code (1).

尝试库：hipfft；实现 hash：`c3978ac55803c9b4d78faf78a736b8cbd036c28c8762cd8c586759e3e0485251`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python tools/migration/probes.py distributed_fft
```

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuFFT_1d_mgpu_c2c_1d_mgpu_c2c_example.cpp](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuFFT_1d_mgpu_c2c_1d_mgpu_c2c_example.cpp)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuFFT_1d_mgpu_c2c_1d_mgpu_c2c_example.cpp](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuFFT_1d_mgpu_c2c_1d_mgpu_c2c_example.cpp)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuFFT_1d_mgpu_c2c_1d_mgpu_c2c_example.cpp](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuFFT_1d_mgpu_c2c_1d_mgpu_c2c_example.cpp)
- [migration/reports/evidence/20261109T085509.301265Z/original-rocm/cuFFT_1d_mgpu_c2c_1d_mgpu_c2c_example.cpp](../../../reports/evidence/20261109T085509.301265Z/original-rocm/cuFFT_1d_mgpu_c2c_1d_mgpu_c2c_example.cpp)
- [migration/reports/evidence/20261109T090451.232153Z/original-rocm/cuFFT_1d_mgpu_c2c_1d_mgpu_c2c_example.cpp](../../../reports/evidence/20261109T090451.232153Z/original-rocm/cuFFT_1d_mgpu_c2c_1d_mgpu_c2c_example.cpp)
- [migration/reports/evidence/20261109T100213.582268Z/native-probes/distributed_fft](../../../reports/evidence/20261109T100213.582268Z/native-probes/distributed_fft)
- [migration/reports/evidence/20261109T100520.458756Z/original-cuda/cuFFT_1d_mgpu_c2c_1d_mgpu_c2c_example.cpp](../../../reports/evidence/20261109T100520.458756Z/original-cuda/cuFFT_1d_mgpu_c2c_1d_mgpu_c2c_example.cpp)
- [migration/reports/additional-comparison.json](../../../reports/additional-comparison.json)
