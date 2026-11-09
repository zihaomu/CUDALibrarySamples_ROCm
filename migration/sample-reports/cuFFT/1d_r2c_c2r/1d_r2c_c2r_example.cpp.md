# cuFFT/1d_r2c_c2r::1d_r2c_c2r_example.cpp

**PASSED / L4**

使用 hipFFT（rocFFT）成功实现原始 profile 和 6 个数值用例，并通过 CUDA 对照

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuFFT/1d_r2c_c2r/1d_r2c_c2r_example.cpp](../../../../cuFFT/1d_r2c_c2r/1d_r2c_c2r_example.cpp) |
| 实际库 / 后端 | hipFFT / rocFFT |
| 候选路线 | hipFFT, rocFFT, RCCL + HIP (distributed alternative) |
| 代码 | [rocm/cuFFT/1d_r2c_c2r/sample.cpp](../../../../rocm/cuFFT/1d_r2c_c2r/sample.cpp) |
| required cases | 6/6 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `9dd0d13edce427c68301393d51f2c40aae82a5b259758337272395d30bcd4718` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`forward_n8`, `roundtrip_n8`, `forward_n15`, `roundtrip_n15`, `original_forward`, `original_profile`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipfft；实现 hash：`461beda6750c34e68ea9dddfba5ab3afd1f1efa761a7953df9d27431e6b5f275`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

```bash
HIP_VISIBLE_DEVICES=2 tools/migration/run_rocm.sh --filter cuFFT/1d_r2c_c2r
```

- [migration/reports/evidence/20261109T074106.668062Z/rocm/cuFFT_1d_r2c_c2r](../../../reports/evidence/20261109T074106.668062Z/rocm/cuFFT_1d_r2c_c2r)
- [migration/reports/evidence/20261109T074136.696317Z/rocm/cuFFT_1d_r2c_c2r](../../../reports/evidence/20261109T074136.696317Z/rocm/cuFFT_1d_r2c_c2r)
- [migration/reports/evidence/20261109T074302.621128Z/rocm/cuFFT_1d_r2c_c2r](../../../reports/evidence/20261109T074302.621128Z/rocm/cuFFT_1d_r2c_c2r)
- [migration/reports/evidence/20261109T074409.357725Z/rocm/cuFFT_1d_r2c_c2r](../../../reports/evidence/20261109T074409.357725Z/rocm/cuFFT_1d_r2c_c2r)
- [migration/reports/evidence/20261109T075141.556119Z/rocm/cuFFT_1d_r2c_c2r](../../../reports/evidence/20261109T075141.556119Z/rocm/cuFFT_1d_r2c_c2r)
- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuFFT_1d_r2c_c2r_1d_r2c_c2r_example.cpp](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuFFT_1d_r2c_c2r_1d_r2c_c2r_example.cpp)
- [migration/reports/evidence/20261109T081304.129128Z/rocm/cuFFT_1d_r2c_c2r](../../../reports/evidence/20261109T081304.129128Z/rocm/cuFFT_1d_r2c_c2r)
- [migration/reports/evidence/20261109T081927.659318Z/rocm/cuFFT_1d_r2c_c2r](../../../reports/evidence/20261109T081927.659318Z/rocm/cuFFT_1d_r2c_c2r)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuFFT_1d_r2c_c2r_1d_r2c_c2r_example.cpp](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuFFT_1d_r2c_c2r_1d_r2c_c2r_example.cpp)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuFFT_1d_r2c_c2r_1d_r2c_c2r_example.cpp](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuFFT_1d_r2c_c2r_1d_r2c_c2r_example.cpp)
- [migration/reports/evidence/20261109T085509.301265Z/original-rocm/cuFFT_1d_r2c_c2r_1d_r2c_c2r_example.cpp](../../../reports/evidence/20261109T085509.301265Z/original-rocm/cuFFT_1d_r2c_c2r_1d_r2c_c2r_example.cpp)
- [migration/reports/evidence/20261109T090451.232153Z/original-rocm/cuFFT_1d_r2c_c2r_1d_r2c_c2r_example.cpp](../../../reports/evidence/20261109T090451.232153Z/original-rocm/cuFFT_1d_r2c_c2r_1d_r2c_c2r_example.cpp)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_1d_r2c_c2r_1d_r2c_c2r_example.cpp](../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_1d_r2c_c2r_1d_r2c_c2r_example.cpp)
