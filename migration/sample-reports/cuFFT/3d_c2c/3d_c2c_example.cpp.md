# cuFFT/3d_c2c::3d_c2c_example.cpp

**PASSED / L4**

使用 hipFFT/rocFFT 保留原始尺寸、batch 和 GPU scaling，全部数值经独立 CPU FFT 检查；2D 实现修复原始 real 输出显示的 padded stride，并显式同步异步回传。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuFFT/3d_c2c/3d_c2c_example.cpp](../../../../cuFFT/3d_c2c/3d_c2c_example.cpp) |
| 实际库 / 后端 | hipFFT / rocFFT |
| 候选路线 | hipFFT, rocFFT, RCCL + HIP (distributed alternative) |
| 代码 | [rocm/ported/cuFFT/3d_c2c/3d_c2c_example.cpp](../../../../rocm/ported/cuFFT/3d_c2c/3d_c2c_example.cpp) |
| required cases | 2/2 |
| CUDA baseline / comparison | PASSED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `181f133c1eeb292674c0dce724e190f413b9d5d6bc52f9c41b3eac435694b99f` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-3d-forward-all-values-cpu`, `original-3d-gpu-normalization-roundtrip`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：AMD 已通过所列 CPU/数学参考，但同输入跨 GPU 独立对照尚未完成。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipfft；实现 hash：`cb635a520c63f0726237e2890fc1e792b6c7244619ce5fcf3e6ab844328e949a`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuFFT_3d_c2c_3d_c2c_example.cpp](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuFFT_3d_c2c_3d_c2c_example.cpp)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuFFT_3d_c2c_3d_c2c_example.cpp](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuFFT_3d_c2c_3d_c2c_example.cpp)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuFFT_3d_c2c_3d_c2c_example.cpp](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuFFT_3d_c2c_3d_c2c_example.cpp)
- [migration/reports/evidence/20261109T085509.301265Z/original-rocm/cuFFT_3d_c2c_3d_c2c_example.cpp](../../../reports/evidence/20261109T085509.301265Z/original-rocm/cuFFT_3d_c2c_3d_c2c_example.cpp)
- [migration/reports/evidence/20261109T090451.232153Z/original-rocm/cuFFT_3d_c2c_3d_c2c_example.cpp](../../../reports/evidence/20261109T090451.232153Z/original-rocm/cuFFT_3d_c2c_3d_c2c_example.cpp)
- [migration/reports/small-fft-validation.json](../../../reports/small-fft-validation.json)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_3d_c2c_3d_c2c_example.cpp](../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_3d_c2c_3d_c2c_example.cpp)
