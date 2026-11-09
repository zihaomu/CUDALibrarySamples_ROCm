# cuBLAS/Level-3/herkx::cublas_herkx_example.cu

**PASSED / L4**

使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLAS/Level-3/herkx/cublas_herkx_example.cu](../../../../../cuBLAS/Level-3/herkx/cublas_herkx_example.cu) |
| 实际库 / 后端 | hipBLAS / rocBLAS |
| 候选路线 | hipBLAS, rocBLAS |
| 代码 | [rocm/ported/cuBLAS/Level-3/herkx/cublas_herkx_example.cu](../../../../../rocm/ported/cuBLAS/Level-3/herkx/cublas_herkx_example.cu) |
| required cases | 2/2 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `05f1477a731d85aae8c1bd11ae8936a7dc965128d8086c5be21be32ac3e9a9b3` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-fixed-input-cpu`, `original-fixed-input-cuda`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：—；实现 hash：`d75de072814dbbf055ddca46cbbf6f00cb4a595d15da6decb2f9a58ffae2b059`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Level-3_herkx_cublas_herkx_example.cu](../../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Level-3_herkx_cublas_herkx_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Level-3_herkx_cublas_herkx_example.cu](../../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Level-3_herkx_cublas_herkx_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Level-3_herkx_cublas_herkx_example.cu](../../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Level-3_herkx_cublas_herkx_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Level-3_herkx_cublas_herkx_example.cu](../../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Level-3_herkx_cublas_herkx_example.cu)
- [migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Level-3_herkx_cublas_herkx_example.cu](../../../../reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Level-3_herkx_cublas_herkx_example.cu)
- [migration/reports/blas-three-way.json](../../../../reports/blas-three-way.json)
- [migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_herkx_cublas_herkx_example.cu](../../../../reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-3_herkx_cublas_herkx_example.cu)
