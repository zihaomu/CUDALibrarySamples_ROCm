# cuSPARSELt Library

## Description

This folder demonstrates cuSPARSELt Generic APIs usage.

[cuSPARSELt Documentation](https://docs.nvidia.com/cuda/cusparselt/index.html)

## cuSPARSELt Samples

* [Structured Matrix-Matrix Multiplication - Basic Concepts](matmul/)

    The sample demonstrates how to exploit *Sparse Tensor Cores* for performing Structured Matrix-Matrix Multiplication

* [Batched GEMM, Activation Function, and Bias](matmul_advanced/)

    The sample extends the previous code to demonstrate how to perform batched GEMM computation, Split-K, and how to set up the activation function and bias

<!-- ROCM-MIGRATION:START -->
## ROCm 支持情况

2 个独立源入口；PASSED 2，PARTIAL 0，FAILED 0，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：hipSPARSELt。候选不等于已使用；基础探针成功也不等于整库迁移成功。

hipSPARSELt 已编译并真实运行，gfx1201 kernel 数据缺失；锁定源码的支持架构列表也不接受 gfx1201，不能用 dense GEMM 代替结构化稀疏。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [matmul/matmul_example.cpp](matmul/matmul_example.cpp) · [详情](../migration/sample-reports/cuSPARSELt/matmul/matmul_example.cpp.md) | project HIP GPU TILE prune + packed 2:4 values/metadata + sparse-only matmul / HIP GPU; CPU descriptor/constant-mask setup only | L4 / PASSED | 项目HIP真实TILE最大L1 2:4裁剪/压缩metadata/稀疏乘法：FP16+FP32累积，basic实际GPU搜索；advanced双batch/stride/bias/ReLU。7场景通过独立容量DP与FP64参考；原生CUDA原例另验，数学对照使用同HIP裁剪A及显式CUDA packing，合法tie不要求相同mask。17注入/10非法descriptor/真实GPU metadata损坏/稀疏核轨迹及独立复核通过；原生hipSPARSELt/gfx1201失败单独保留，不声称原生加速或opaque布局兼容。 | PASSED / PASSED | [记录](../migration/reports/evidence/rewrite/R7/cuSPARSELt_matmul__matmul_example.cpp/20261110T113200.713147Z-R7-composite-qualification-b5e684af2f)；[记录](../migration/reports/rewrite-R7-qualification.json) |
| [matmul_advanced/matmul_advanced_example.cpp](matmul_advanced/matmul_advanced_example.cpp) · [详情](../migration/sample-reports/cuSPARSELt/matmul_advanced/matmul_advanced_example.cpp.md) | project HIP GPU TILE prune + packed 2:4 values/metadata + sparse-only matmul / HIP GPU; CPU descriptor/constant-mask setup only | L4 / PASSED | 项目HIP真实TILE最大L1 2:4裁剪/压缩metadata/稀疏乘法：FP16+FP32累积，basic实际GPU搜索；advanced双batch/stride/bias/ReLU。7场景通过独立容量DP与FP64参考；原生CUDA原例另验，数学对照使用同HIP裁剪A及显式CUDA packing，合法tie不要求相同mask。17注入/10非法descriptor/真实GPU metadata损坏/稀疏核轨迹及独立复核通过；原生hipSPARSELt/gfx1201失败单独保留，不声称原生加速或opaque布局兼容。 | PASSED / PASSED | [记录](../migration/reports/evidence/rewrite/R7/cuSPARSELt_matmul_advanced__matmul_advanced_example.cpp/20261110T113201.453874Z-R7-composite-qualification-696b878907)；[记录](../migration/reports/rewrite-R7-qualification.json) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
