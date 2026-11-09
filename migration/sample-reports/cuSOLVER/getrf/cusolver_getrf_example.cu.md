# cuSOLVER/getrf::cusolver_getrf_example.cu

**PASSED / L4**

使用 hipSOLVER（rocSOLVER）成功实现原始 profile 和 6 个数值用例，并通过 CUDA 对照

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSOLVER/getrf/cusolver_getrf_example.cu](../../../../cuSOLVER/getrf/cusolver_getrf_example.cu) |
| 实际库 / 后端 | hipSOLVER / rocSOLVER |
| 候选路线 | hipSOLVER, rocSOLVER |
| 代码 | [rocm/cuSOLVER/getrf/sample.cpp](../../../../rocm/cuSOLVER/getrf/sample.cpp) |
| required cases | 6/6 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `2f172cf9a098404814f57f78f0fddc0f33dfb13e4a24e0d5e0f4e3fec5f22f9b` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`factorization_pivot0`, `pivot0`, `residual_pivot0`, `factorization_pivot1`, `pivot1`, `residual_pivot1`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

run 失败：terminate called after throwing an instance of 'std::runtime_error'   what():  hipsolver error

尝试库：hipsolver；实现 hash：`168d9792bfff9b3fb7b16fc5b464456c847fb12608921b8172ba2a706ac144ea`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

```bash
HIP_VISIBLE_DEVICES=2 tools/migration/run_rocm.sh --filter cuSOLVER/getrf
```

- [migration/reports/evidence/20261109T074106.668062Z/rocm/cuSOLVER_getrf](../../../reports/evidence/20261109T074106.668062Z/rocm/cuSOLVER_getrf)
- [migration/reports/evidence/20261109T074136.696317Z/rocm/cuSOLVER_getrf](../../../reports/evidence/20261109T074136.696317Z/rocm/cuSOLVER_getrf)
- [migration/reports/evidence/20261109T074302.621128Z/rocm/cuSOLVER_getrf](../../../reports/evidence/20261109T074302.621128Z/rocm/cuSOLVER_getrf)
- [migration/reports/evidence/20261109T074409.357725Z/rocm/cuSOLVER_getrf](../../../reports/evidence/20261109T074409.357725Z/rocm/cuSOLVER_getrf)
- [migration/reports/evidence/20261109T074618.724680Z/rocm/cuSOLVER_getrf](../../../reports/evidence/20261109T074618.724680Z/rocm/cuSOLVER_getrf)
- [migration/reports/evidence/20261109T075141.556119Z/rocm/cuSOLVER_getrf](../../../reports/evidence/20261109T075141.556119Z/rocm/cuSOLVER_getrf)
- [migration/reports/evidence/20261109T075300.685270Z/rocm/cuSOLVER_getrf](../../../reports/evidence/20261109T075300.685270Z/rocm/cuSOLVER_getrf)
- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu)
- [migration/reports/evidence/20261109T081304.129128Z/rocm/cuSOLVER_getrf](../../../reports/evidence/20261109T081304.129128Z/rocm/cuSOLVER_getrf)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu](../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu](../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu](../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu)
- [migration/reports/evidence/20261109T081927.659318Z/rocm/cuSOLVER_getrf](../../../reports/evidence/20261109T081927.659318Z/rocm/cuSOLVER_getrf)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu)
- [migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu](../../../reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_getrf_cusolver_getrf_example.cu)
- [migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_getrf_cusolver_getrf_example.cu](../../../reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_getrf_cusolver_getrf_example.cu)
