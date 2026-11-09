# cuBLASLt/LtSgemm::main.cpp

**PASSED / L4**

使用 hipBLASLt（hipBLASLt native）成功实现原始 profile 和 5 个数值用例，并通过 CUDA 对照

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLASLt/LtSgemm/main.cpp](../../../../cuBLASLt/LtSgemm/main.cpp) |
| 实际库 / 后端 | hipBLASLt / hipBLASLt native |
| 候选路线 | hipBLASLt |
| 代码 | [rocm/cuBLASLt/LtSgemm/sample.cpp](../../../../rocm/cuBLASLt/LtSgemm/sample.cpp) |
| required cases | 5/5 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `0cc94667445db5d34f43d322df2586e69a512cedbdb16724e5c4334b6769481b` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`transpose0_beta0.000000`, `transpose0_beta0.500000`, `transpose1_beta0.000000`, `transpose1_beta0.500000`, `original_profile`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipblaslt；实现 hash：`56e8413cf05f57a8d6c0e7f7af80b2856cedf7e7b1fae8292de7d537da99dc89`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

```bash
HIP_VISIBLE_DEVICES=2 tools/migration/run_rocm.sh --filter cuBLASLt/LtSgemm
```

- [migration/reports/evidence/20261109T074106.668062Z/rocm/cuBLASLt_LtSgemm](../../../reports/evidence/20261109T074106.668062Z/rocm/cuBLASLt_LtSgemm)
- [migration/reports/evidence/20261109T074136.696317Z/rocm/cuBLASLt_LtSgemm](../../../reports/evidence/20261109T074136.696317Z/rocm/cuBLASLt_LtSgemm)
- [migration/reports/evidence/20261109T074302.621128Z/rocm/cuBLASLt_LtSgemm](../../../reports/evidence/20261109T074302.621128Z/rocm/cuBLASLt_LtSgemm)
- [migration/reports/evidence/20261109T074409.357725Z/rocm/cuBLASLt_LtSgemm](../../../reports/evidence/20261109T074409.357725Z/rocm/cuBLASLt_LtSgemm)
- [migration/reports/evidence/20261109T075141.556119Z/rocm/cuBLASLt_LtSgemm](../../../reports/evidence/20261109T075141.556119Z/rocm/cuBLASLt_LtSgemm)
- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuBLASLt_LtSgemm_main.cpp](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuBLASLt_LtSgemm_main.cpp)
- [migration/reports/evidence/20261109T081304.129128Z/rocm/cuBLASLt_LtSgemm](../../../reports/evidence/20261109T081304.129128Z/rocm/cuBLASLt_LtSgemm)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuBLASLt_LtSgemm_main.cpp](../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuBLASLt_LtSgemm_main.cpp)
- [migration/reports/evidence/20261109T081401.539900Z/rocm/cuBLASLt_LtSgemm](../../../reports/evidence/20261109T081401.539900Z/rocm/cuBLASLt_LtSgemm)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuBLASLt_LtSgemm_main.cpp](../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuBLASLt_LtSgemm_main.cpp)
- [migration/reports/evidence/20261109T081927.659318Z/rocm/cuBLASLt_LtSgemm](../../../reports/evidence/20261109T081927.659318Z/rocm/cuBLASLt_LtSgemm)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuBLASLt_LtSgemm_main.cpp](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuBLASLt_LtSgemm_main.cpp)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuBLASLt_LtSgemm_main.cpp](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuBLASLt_LtSgemm_main.cpp)
- [migration/reports/evidence/20261109T085205.912828Z/original-rocm/cuBLASLt_LtSgemm_main.cpp](../../../reports/evidence/20261109T085205.912828Z/original-rocm/cuBLASLt_LtSgemm_main.cpp)
- [migration/reports/evidence/20261109T085413.622888Z/original-rocm/cuBLASLt_LtSgemm_main.cpp](../../../reports/evidence/20261109T085413.622888Z/original-rocm/cuBLASLt_LtSgemm_main.cpp)
- [migration/reports/evidence/20261109T085546.110648Z/original-rocm/cuBLASLt_LtSgemm_main.cpp](../../../reports/evidence/20261109T085546.110648Z/original-rocm/cuBLASLt_LtSgemm_main.cpp)
- [migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtSgemm_main.cpp](../../../reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtSgemm_main.cpp)
- [migration/reports/blaslt-original-validation.json](../../../reports/blaslt-original-validation.json)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtSgemm_main.cpp](../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtSgemm_main.cpp)
