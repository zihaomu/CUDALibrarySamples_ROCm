# cuBLAS/Level-3/gemmGroupedBatched::cublas_gemmGroupedBatched_example.cu

**PASSED / L4**

使用 hipBLAS / rocBLAS 保留原始 profile 与数学 API；2 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLAS/Level-3/gemmGroupedBatched/cublas_gemmGroupedBatched_example.cu](../../../../../cuBLAS/Level-3/gemmGroupedBatched/cublas_gemmGroupedBatched_example.cu) |
| 实际库 / 后端 | hipBLAS / rocBLAS |
| 候选路线 | hipBLAS, rocBLAS |
| 代码 | [rocm/ported/cuBLAS/Level-3/gemmGroupedBatched/cublas_gemmGroupedBatched_example.cu](../../../../../rocm/ported/cuBLAS/Level-3/gemmGroupedBatched/cublas_gemmGroupedBatched_example.cu) |
| required cases | 2/2 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `24b86be7c4c222cddd8d04c0542c9b582aac0cc76176baba7ef10bae33e59dda` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batch2/original`, `batch2/negative-alpha`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：—；实现 hash：`16f76e81c49e03596089a6b56b6172c15d3761d06c91439707bc37c72f5aca90`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按第二批报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batch2_run.py blas
python3 tools/migration/batch2_validate.py blas --qualify
```

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu](../../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu](../../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu](../../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu](../../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu](../../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu)
- [migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu](../../../../reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu)
- [migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu](../../../../reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu)
- [migration/reports/evidence/20261109T115319.593333Z/batch2-rocm/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu](../../../../reports/evidence/20261109T115319.593333Z/batch2-rocm/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu)
- [migration/reports/batch2-validation.json](../../../../reports/batch2-validation.json)
- [migration/reports/evidence/20261109T115141.126114Z/batch2-cuda/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu](../../../../reports/evidence/20261109T115141.126114Z/batch2-cuda/cuBLAS_Level-3_gemmGroupedBatched_cublas_gemmGroupedBatched_example.cu)
