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
## ROCm 迁移实时状态

2 个独立源入口；PASSED 0，PARTIAL 2，FAILED 0，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：hipSPARSELt。候选不等于已使用；基础探针成功也不等于整库迁移成功。

hipSPARSELt 已编译并真实运行，gfx1201 kernel 数据缺失；锁定源码的支持架构列表也不接受 gfx1201，不能用 dense GEMM 代替结构化稀疏。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [matmul/matmul_example.cpp](matmul/matmul_example.cpp) · [详情](../migration/sample-reports/cuSPARSELt/matmul/matmul_example.cpp.md) | project HIP GPU TILE prune + packed 2:4 values/metadata + sparse-only matmul / HIP GPU; CPU descriptor/constant-mask setup only | L3 / PARTIAL | 原生hipSPARSELt路线仍缺gfx1201 bundle/高级属性；已实现项目HIP真实2:4 TILE裁剪、压缩metadata与稀疏乘法，14 AMD/CPU场景通过。原始CUDA两例通过，完整扩展CUDA对照、负向、运行边界、轨迹和独立复核尚待收口。不是dense GEMM回退或原生Sparse Tensor Core支持。 | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/rewrite/R7/cuSPARSELt_matmul__matmul_example.cpp/20261110T110155.523031Z-R7-rocm-e4da9f1bd1)；[记录](../migration/reports/rewrite-sparseLt-native-route.json) |
| [matmul_advanced/matmul_advanced_example.cpp](matmul_advanced/matmul_advanced_example.cpp) · [详情](../migration/sample-reports/cuSPARSELt/matmul_advanced/matmul_advanced_example.cpp.md) | project HIP GPU TILE prune + packed 2:4 values/metadata + sparse-only matmul / HIP GPU; CPU descriptor/constant-mask setup only | L3 / PARTIAL | 原生hipSPARSELt路线仍缺gfx1201 bundle/高级属性；已实现项目HIP真实2:4 TILE裁剪、压缩metadata与稀疏乘法，14 AMD/CPU场景通过。原始CUDA两例通过，完整扩展CUDA对照、负向、运行边界、轨迹和独立复核尚待收口。不是dense GEMM回退或原生Sparse Tensor Core支持。 | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/rewrite/R7/cuSPARSELt_matmul_advanced__matmul_advanced_example.cpp/20261110T110208.886413Z-R7-rocm-e78d101558)；[记录](../migration/reports/rewrite-sparseLt-native-route.json) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
