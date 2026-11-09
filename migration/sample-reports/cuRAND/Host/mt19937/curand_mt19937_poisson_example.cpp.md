# cuRAND/Host/mt19937::curand_mt19937_poisson_example.cpp

**PASSED / L4**

hipRAND/rocRAND 原始源码 n 的 host/device 路径、同 seed/offset 可复现性与 n=98304 的解析分布矩验证通过；不要求 cuRAND/rocRAND 序列逐值相同。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuRAND/Host/mt19937/curand_mt19937_poisson_example.cpp](../../../../../cuRAND/Host/mt19937/curand_mt19937_poisson_example.cpp) |
| 实际库 / 后端 | hipRAND / rocRAND |
| 候选路线 | hipRAND, rocRAND |
| 代码 | [rocm/ported/cuRAND/Host/mt19937/curand_mt19937_poisson_example.cpp](../../../../../rocm/ported/cuRAND/Host/mt19937/curand_mt19937_poisson_example.cpp) |
| required cases | 6/6 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `9a3f93b797478021293a30d1d372c3c67841971126d37b6568e405d90ec826b8` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`host-and-device-n12-run0`, `host-and-device-n12-run1`, `host-and-device-n98304-run2`, `same-seed-or-offset-repeat-host-and-device`, `analytic-poisson-moments-host`, `analytic-poisson-moments-device`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

run 失败： TIMEOUT

尝试库：—；实现 hash：`bca6ee8894b89aa7d84f3e818cdb093f08112f7e00e47689ca7e2a0772eb28be`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuRAND_Host_mt19937_curand_mt19937_poisson_example.cpp](../../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuRAND_Host_mt19937_curand_mt19937_poisson_example.cpp)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuRAND_Host_mt19937_curand_mt19937_poisson_example.cpp](../../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuRAND_Host_mt19937_curand_mt19937_poisson_example.cpp)
- [migration/reports/evidence/20261109T084257.296664Z/original-rocm/cuRAND_Host_mt19937_curand_mt19937_poisson_example.cpp](../../../../reports/evidence/20261109T084257.296664Z/original-rocm/cuRAND_Host_mt19937_curand_mt19937_poisson_example.cpp)
- [migration/reports/evidence/20261109T085311.932378Z/rng-validation/cuRAND_Host_mt19937_curand_mt19937_poisson_example.cpp](../../../../reports/evidence/20261109T085311.932378Z/rng-validation/cuRAND_Host_mt19937_curand_mt19937_poisson_example.cpp)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuRAND_Host_mt19937_curand_mt19937_poisson_example.cpp](../../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuRAND_Host_mt19937_curand_mt19937_poisson_example.cpp)
- [migration/reports/additional-comparison.json](../../../../reports/additional-comparison.json)
