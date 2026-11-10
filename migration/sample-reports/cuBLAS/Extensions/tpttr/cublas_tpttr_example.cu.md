# cuBLAS/Extensions/tpttr::cublas_tpttr_example.cu

**PASSED / L4**

使用 HIP GPU packed conversion / HIP runtime 保留原始dtype/布局与数学运算；4 个预登记输入case通过独立CPU与同输入CUDA，GPU适配和数值路径均已检查。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLAS/Extensions/tpttr/cublas_tpttr_example.cu](../../../../../cuBLAS/Extensions/tpttr/cublas_tpttr_example.cu) |
| 实际库 / 后端 | HIP GPU packed conversion / HIP runtime |
| 候选路线 | hipBLAS, rocBLAS |
| 代码 | [rocm/ported/cuBLAS/Extensions/tpttr/cublas_tpttr_example.cu](../../../../../rocm/ported/cuBLAS/Extensions/tpttr/cublas_tpttr_example.cu) |
| required cases | 4/4 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `8591d285de518575f346fd987d3d9c97f7fad6e029922b5af167505fc04afc2d` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches4_8/original`, `batches4_8/lower`, `batches4_8/padded-lda`, `batches4_8/odd-size`。

实现方式：`HYBRID_HIP`。

恢复/扩展条件：已登记profile通过；扩展其它精度/规模/矩阵性质或API配置时，新增预登记输入并重新做CPU/CUDA及运行语义验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLAS/Extensions/tpttr/cublas_tpttr_example.cu:71:18: error: use of undeclared identifier 'cublasDtpttr'

尝试库：—；实现 hash：`c1cdae06f144d2e50c34cf4a3cb38770b84b3f70661adb3ef1f71013af7f91dc`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches4_8_run.py b4
python3 tools/migration/batches4_8_validate.py b4 --qualify
```

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu](../../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu](../../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu](../../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu](../../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu](../../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu)
- [migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu](../../../../reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu)
- [migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu](../../../../reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu)
- [migration/reports/evidence/20261110T024004.667635Z/batches4_8-rocm/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu](../../../../reports/evidence/20261110T024004.667635Z/batches4_8-rocm/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu)
- [migration/reports/batches4_8-validation.json](../../../../reports/batches4_8-validation.json)
- [migration/reports/evidence/20261110T023758.405542Z/batches4_8-cuda/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu](../../../../reports/evidence/20261110T023758.405542Z/batches4_8-cuda/cuBLAS_Extensions_tpttr_cublas_tpttr_example.cu)
