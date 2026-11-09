# cuFFT/lto_callback_window_1d/src::r2c_c2r_legacy_callback_example.cu

**PASSED / L4**

使用 hipFFT/rocFFT 保留原始 device load callback 融合与原始 window/batch 配置；全量输出通过独立 CPU Independent CPU rfft, frequency truncation at bin32, irfft*328 on all 830 signals，相对 L2=2.746302811829082e-07。性能未验收。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuFFT/lto_callback_window_1d/src/r2c_c2r_legacy_callback_example.cu](../../../../../cuFFT/lto_callback_window_1d/src/r2c_c2r_legacy_callback_example.cu) |
| 实际库 / 后端 | hipFFT / rocFFT |
| 候选路线 | hipFFT, rocFFT, RCCL + HIP (distributed alternative) |
| 代码 | [rocm/ported/cuFFT/lto_callback_window_1d/src/r2c_c2r_legacy_callback_example.cu](../../../../../rocm/ported/cuFFT/lto_callback_window_1d/src/r2c_c2r_legacy_callback_example.cu) |
| required cases | 2/2 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `e29fb3de6af3ad2f91cb6edf97983985e04eafceb7668873dacd5cf6cf87a29a` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-profile-independent-cpu`, `original-profile-reference-pipeline`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipfft；实现 hash：`ccfb3e1bb99e4195d864bcfd0abc51d135c4db41ae0a96d0637382845eba99c8`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu](../../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu](../../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu](../../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu)
- [migration/reports/evidence/20261109T085509.301265Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu](../../../../reports/evidence/20261109T085509.301265Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu)
- [migration/reports/evidence/20261109T085730.270757Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu](../../../../reports/evidence/20261109T085730.270757Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu)
- [migration/reports/evidence/20261109T085759.859059Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu](../../../../reports/evidence/20261109T085759.859059Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu)
- [migration/reports/evidence/20261109T090451.232153Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu](../../../../reports/evidence/20261109T090451.232153Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu)
- [migration/reports/fft-original-validation.json](../../../../reports/fft-original-validation.json)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu](../../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_lto_callback_window_1d_src_r2c_c2r_legacy_callback_example.cu)
- [migration/reports/additional-comparison.json](../../../../reports/additional-comparison.json)
