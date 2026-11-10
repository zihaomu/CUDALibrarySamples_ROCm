# cuSPARSELt/matmul_advanced::matmul_advanced_example.cpp

**PASSED / L4**

项目HIP真实TILE最大L1 2:4裁剪/压缩metadata/稀疏乘法：FP16+FP32累积，basic实际GPU搜索；advanced双batch/stride/bias/ReLU。7场景通过独立容量DP与FP64参考；原生CUDA原例另验，数学对照使用同HIP裁剪A及显式CUDA packing，合法tie不要求相同mask。17注入/10非法descriptor/真实GPU metadata损坏/稀疏核轨迹及独立复核通过；原生hipSPARSELt/gfx1201失败单独保留，不声称原生加速或opaque布局兼容。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSPARSELt/matmul_advanced/matmul_advanced_example.cpp](../../../../cuSPARSELt/matmul_advanced/matmul_advanced_example.cpp) |
| 实际库 / 后端 | project HIP GPU TILE prune + packed 2:4 values/metadata + sparse-only matmul / HIP GPU; CPU descriptor/constant-mask setup only |
| 候选路线 | hipSPARSELt |
| 代码 | [rocm/ported/cuSPARSELt/matmul_advanced/matmul_advanced_example.cpp](../../../../rocm/ported/cuSPARSELt/matmul_advanced/matmul_advanced_example.cpp) |
| required cases | 14/14 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `9262f190a73481136ab49718c0afefb5f7590decc7930aacdf533f8bfdd059bc` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite/R7/original`, `rewrite/R7/changed-values`, `rewrite/R7/layout`, `rewrite/R7/irregular`, `rewrite/R7/zero-A`, `rewrite/R7/ties`, `rewrite/R7/repeat`, `rewrite/R7/native-original`, `rewrite/R7/native-sparse-math`, `rewrite/R7/17-semantic-faults`, `rewrite/R7/10-descriptors`, `rewrite/R7/real-GPU-metadata-check`, `rewrite/R7/GPU-trace`, `rewrite/R7/review`。

实现方式：`PROJECT_HIP_ALGORITHM_REWRITE`。

恢复/扩展条件：使用有匹配 kernel bundle 的受支持 GPU，或新的 gfx1201 hipSPARSELt 实现/包；重新跑 prune/compress/matmul 与 CPU 参考。

CUDA 对照限制：Default FP16 A/B/C/bias, FP32 accumulate; TILE optimal L1 ties may differ. Actual native originals checked separately. Native sparse compression/matmul baseline consumes corresponding HIP-pruned A and uses CUDA packing for vendor descriptor limits. Project packed format: two FP16 values and one metadata byte per group; low four bits encode positions. No native hipSPARSELt or vendor opaque-format compatibility claim.

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

run 失败：CUSPARSE API failed at line 313 with error: function is not implemented (10)

尝试库：hipsparselt, hipsparse；实现 hash：`105e07cfecc10d798f7506f8b5043efa88648a9abd547ad010868e87a3efd640`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuSPARSELt_matmul_advanced_matmul_advanced_example.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/cuSPARSELt_matmul_advanced_matmul_advanced_example.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSPARSELt_matmul_advanced_matmul_advanced_example.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/cuSPARSELt_matmul_advanced_matmul_advanced_example.cpp)
- [migration/reports/evidence/20261109T091606.225939Z/original-rocm/cuSPARSELt_matmul_advanced_matmul_advanced_example.cpp](../../../reports/evidence/20261109T091606.225939Z/original-rocm/cuSPARSELt_matmul_advanced_matmul_advanced_example.cpp)
- [migration/reports/evidence/20261109T091904.671567Z/original-rocm/cuSPARSELt_matmul_advanced_matmul_advanced_example.cpp](../../../reports/evidence/20261109T091904.671567Z/original-rocm/cuSPARSELt_matmul_advanced_matmul_advanced_example.cpp)
- [migration/reports/evidence/20261109T092720.531889Z/original-rocm/cuSPARSELt_matmul_advanced_matmul_advanced_example.cpp](../../../reports/evidence/20261109T092720.531889Z/original-rocm/cuSPARSELt_matmul_advanced_matmul_advanced_example.cpp)
- [migration/reports/upstream-support/hipsparselt-gfx1201-configure.log](../../../reports/upstream-support/hipsparselt-gfx1201-configure.log)
- [migration/reports/upstream-support/sources.json](../../../reports/upstream-support/sources.json)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSPARSELt_matmul_advanced_matmul_advanced_example.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/cuSPARSELt_matmul_advanced_matmul_advanced_example.cpp)
- [migration/reports/evidence/rewrite/R7/cuSPARSELt_matmul_advanced__matmul_advanced_example.cpp/20261110T110208.886413Z-R7-rocm-e78d101558](../../../reports/evidence/rewrite/R7/cuSPARSELt_matmul_advanced__matmul_advanced_example.cpp/20261110T110208.886413Z-R7-rocm-e78d101558)
- [migration/reports/rewrite-sparseLt-native-route.json](../../../reports/rewrite-sparseLt-native-route.json)
- [migration/reports/evidence/rewrite/R7/cuSPARSELt_matmul_advanced__matmul_advanced_example.cpp/20261110T113201.453874Z-R7-composite-qualification-696b878907](../../../reports/evidence/rewrite/R7/cuSPARSELt_matmul_advanced__matmul_advanced_example.cpp/20261110T113201.453874Z-R7-composite-qualification-696b878907)
- [migration/reports/rewrite-R7-qualification.json](../../../reports/rewrite-R7-qualification.json)
