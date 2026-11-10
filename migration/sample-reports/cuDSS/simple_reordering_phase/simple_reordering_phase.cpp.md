# cuDSS/simple_reordering_phase::simple_reordering_phase.cpp

**PARTIAL / L4**

历史analysis-only漏项已修正为完整CPU重排→HIP CSR分解/求解；原始解精度、阶段顺序及排列双射实测通过。项目最小度排列[3,0,1,2,4]与原例严格要求的METIS[4,3,1,0,2]不同，原C++检查仍返回1；因此保持PARTIAL，不改期望向量刷通过。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/simple_reordering_phase/simple_reordering_phase.cpp](../../../../cuDSS/simple_reordering_phase/simple_reordering_phase.cpp) |
| 实际库 / 后端 | CPU symbolic min-degree + project HIP CSR pivot LU/solve via shared C ABI / CPU analysis + HIP preparation |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/simple_reordering_phase/simple_reordering_phase.cpp](../../../../rocm/ported/cuDSS/simple_reordering_phase/simple_reordering_phase.cpp) |
| required cases | 1/2 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `a108c459ce8211ef19b5694abe442c8d008b321e114fa8f89e1e29539eb9b7e5` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite/full-factor-solve-after-isolated-reordering`, `rewrite/exact-vendor-permutation`。

实现方式：`HYBRID_HIP`。

恢复/扩展条件：扩展其它精度/规模/参数需要新增预登记case并重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuDSS/simple_reordering_phase/simple_reordering_phase.cpp:25:10: fatal error: 'cudss.h' file not found

尝试库：—；实现 hash：`de578c9208c50834f3035b817f84d96e44c613a09208ccdda547adb9898c8461`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches9_11_run.py b11
OPENBLAS_NUM_THREADS=1 python3 tools/migration/batches9_11_validate.py b11 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuDSS_simple_reordering_phase_simple_reordering_phase.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/cuDSS_simple_reordering_phase_simple_reordering_phase.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuDSS_simple_reordering_phase_simple_reordering_phase.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/cuDSS_simple_reordering_phase_simple_reordering_phase.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuDSS_simple_reordering_phase_simple_reordering_phase.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/cuDSS_simple_reordering_phase_simple_reordering_phase.cpp)
- [migration/reports/evidence/20261110T043650.167709Z/batches9_11-rocm/cuDSS_simple_reordering_phase_simple_reordering_phase.cpp](../../../reports/evidence/20261110T043650.167709Z/batches9_11-rocm/cuDSS_simple_reordering_phase_simple_reordering_phase.cpp)
- [migration/reports/batches9_11-validation.json](../../../reports/batches9_11-validation.json)
- [migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/cuDSS_simple_reordering_phase_simple_reordering_phase.cpp](../../../reports/evidence/20261110T043816.470698Z/batches9_11-cuda/cuDSS_simple_reordering_phase_simple_reordering_phase.cpp)
- [migration/reports/evidence/rewrite/R5/cuDSS_simple_reordering_phase__simple_reordering_phase.cpp/20261110T094452.257460Z-R5-host-contract-review-54565fa16d](../../../reports/evidence/rewrite/R5/cuDSS_simple_reordering_phase__simple_reordering_phase.cpp/20261110T094452.257460Z-R5-host-contract-review-54565fa16d)
- [migration/reports/evidence/rewrite/R5/cuDSS_simple_reordering_phase__simple_reordering_phase.cpp/20261110T101950.027352Z-R5-rocm-contract-repair-17f17216e0](../../../reports/evidence/rewrite/R5/cuDSS_simple_reordering_phase__simple_reordering_phase.cpp/20261110T101950.027352Z-R5-rocm-contract-repair-17f17216e0)
- [migration/reports/rewrite-reordering-cpp-repair.json](../../../reports/rewrite-reordering-cpp-repair.json)
- [migration/reports/evidence/rewrite/R5/cuDSS_simple_reordering_phase__simple_reordering_phase.cpp/20261110T103529.275718Z-R5-rocm-contract-repair-85587ef969](../../../reports/evidence/rewrite/R5/cuDSS_simple_reordering_phase__simple_reordering_phase.cpp/20261110T103529.275718Z-R5-rocm-contract-repair-85587ef969)
