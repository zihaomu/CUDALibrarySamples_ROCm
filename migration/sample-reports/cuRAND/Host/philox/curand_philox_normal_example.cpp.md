# cuRAND/Host/philox::curand_philox_normal_example.cpp

**PASSED / L4**

使用 hipRAND（rocRAND）成功实现原始 profile 和 5 个数值用例，并通过 CUDA 对照

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuRAND/Host/philox/curand_philox_normal_example.cpp](../../../../../cuRAND/Host/philox/curand_philox_normal_example.cpp) |
| 实际库 / 后端 | hipRAND / rocRAND |
| 候选路线 | hipRAND, rocRAND |
| 代码 | [rocm/cuRAND/Host/philox/normal/sample.cpp](../../../../../rocm/cuRAND/Host/philox/normal/sample.cpp) |
| required cases | 5/5 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `662c8bddce2d956bf4d0276cf208d3ea7c0702f0cbd53bb12630211ab10b43ea` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`host0_offset0`, `host0_offset16`, `host1_offset0`, `host1_offset16`, `original_profile`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：—；实现 hash：`2cbe19fee79706bdb35e3048171444f2ec03e31d37e4f3664abd2ec9ce10aede`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

```bash
HIP_VISIBLE_DEVICES=2 tools/migration/run_rocm.sh --filter cuRAND/Host/philox/normal
```

- [migration/reports/evidence/20261109T074106.668062Z/rocm/cuRAND_Host_philox_normal](../../../../reports/evidence/20261109T074106.668062Z/rocm/cuRAND_Host_philox_normal)
- [migration/reports/evidence/20261109T074136.696317Z/rocm/cuRAND_Host_philox_normal](../../../../reports/evidence/20261109T074136.696317Z/rocm/cuRAND_Host_philox_normal)
- [migration/reports/evidence/20261109T074302.621128Z/rocm/cuRAND_Host_philox_normal](../../../../reports/evidence/20261109T074302.621128Z/rocm/cuRAND_Host_philox_normal)
- [migration/reports/evidence/20261109T074409.357725Z/rocm/cuRAND_Host_philox_normal](../../../../reports/evidence/20261109T074409.357725Z/rocm/cuRAND_Host_philox_normal)
- [migration/reports/evidence/20261109T075141.556119Z/rocm/cuRAND_Host_philox_normal](../../../../reports/evidence/20261109T075141.556119Z/rocm/cuRAND_Host_philox_normal)
- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuRAND_Host_philox_curand_philox_normal_example.cpp](../../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuRAND_Host_philox_curand_philox_normal_example.cpp)
- [migration/reports/evidence/20261109T081304.129128Z/rocm/cuRAND_Host_philox_normal](../../../../reports/evidence/20261109T081304.129128Z/rocm/cuRAND_Host_philox_normal)
- [migration/reports/evidence/20261109T081927.659318Z/rocm/cuRAND_Host_philox_normal](../../../../reports/evidence/20261109T081927.659318Z/rocm/cuRAND_Host_philox_normal)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuRAND_Host_philox_curand_philox_normal_example.cpp](../../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuRAND_Host_philox_curand_philox_normal_example.cpp)
- [migration/reports/evidence/20261109T084257.296664Z/original-rocm/cuRAND_Host_philox_curand_philox_normal_example.cpp](../../../../reports/evidence/20261109T084257.296664Z/original-rocm/cuRAND_Host_philox_curand_philox_normal_example.cpp)
- [migration/reports/evidence/20261109T084900.390579Z/rng-validation/cuRAND_Host_philox_curand_philox_normal_example.cpp](../../../../reports/evidence/20261109T084900.390579Z/rng-validation/cuRAND_Host_philox_curand_philox_normal_example.cpp)
- [migration/reports/evidence/20261109T085047.464207Z/rng-validation/cuRAND_Host_philox_curand_philox_normal_example.cpp](../../../../reports/evidence/20261109T085047.464207Z/rng-validation/cuRAND_Host_philox_curand_philox_normal_example.cpp)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuRAND_Host_philox_curand_philox_normal_example.cpp](../../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuRAND_Host_philox_curand_philox_normal_example.cpp)
- [migration/reports/additional-comparison.json](../../../../reports/additional-comparison.json)
