# cuBLAS/Extensions/GemmExAutoTuning::cublas_GemmExAutoTuning_example.cu

**PASSED / L4**

使用 hipBLAS + project search/group dispatch，保持原始dtype/规模，全部候选完整输出、所选方案重放及workspace限制通过CPU/CUDA。分组为项目分发适配；搜索ID仅在对应后端有效，不跨库照搬CUDA算法ID；共享GPU计时不计性能资格。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu](../../../../../cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu) |
| 实际库 / 后端 | hipBLAS + project search/group dispatch / rocBLAS |
| 候选路线 | hipBLAS, rocBLAS |
| 代码 | [rocm/ported/cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu](../../../../../rocm/ported/cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu) |
| required cases | 3/3 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `63dae037447105c271f59e6303be914fcd36d89aee15b3721adb9195e704973b` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches4_8/original`, `batches4_8/limited-workspace`, `batches4_8/changed-values`。

实现方式：`HYBRID_HIP`。

恢复/扩展条件：已登记profile通过；扩展其它精度/规模/矩阵性质或API配置时，新增预登记输入并重新做CPU/CUDA及运行语义验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu:138:9: error: use of undeclared identifier 'CUBLAS_GEMM_AUTOTUNE'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu:155:9: error: use of undeclared identifier 'CUBLAS_GEMM_AUTOTUNE'

尝试库：—；实现 hash：`90d392558d01732090d92174c0af218f7ec9a297b43d7401033d45cc499db905`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches4_8_run.py b7
python3 tools/migration/batches4_8_validate.py b7 --qualify
```

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu](../../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu](../../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu](../../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu](../../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu](../../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu)
- [migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu](../../../../reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu)
- [migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu](../../../../reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu)
- [migration/reports/evidence/20261110T032042.120705Z/batches4_8-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu](../../../../reports/evidence/20261110T032042.120705Z/batches4_8-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu)
- [migration/reports/batches4_8-validation.json](../../../../reports/batches4_8-validation.json)
- [migration/reports/evidence/20261110T031433.835201Z/batches4_8-cuda/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu](../../../../reports/evidence/20261110T031433.835201Z/batches4_8-cuda/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu)
- [migration/reports/evidence/20261110T031918.495272Z/batches4_8-cuda/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu](../../../../reports/evidence/20261110T031918.495272Z/batches4_8-cuda/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu)
- [migration/reports/evidence/20261110T032310.748567Z/batches4_8-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu](../../../../reports/evidence/20261110T032310.748567Z/batches4_8-rocm/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu)
- [migration/reports/evidence/20261110T032104.369797Z/batches4_8-cuda/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu](../../../../reports/evidence/20261110T032104.369797Z/batches4_8-cuda/cuBLAS_Extensions_GemmExAutoTuning_cublas_GemmExAutoTuning_example.cu)
