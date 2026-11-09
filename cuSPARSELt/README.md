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

2 个独立源入口；PASSED 0，PARTIAL 0，FAILED 0，BLOCKED 0，UNSUPPORTED 2，NOT_STARTED 0，IN_PROGRESS 0。

候选库：hipSPARSELt。候选不等于已使用；基础探针成功也不等于整库迁移成功。

hipSPARSELt 已编译并真实运行，gfx1201 kernel 数据缺失；锁定源码的支持架构列表也不接受 gfx1201，不能用 dense GEMM 代替结构化稀疏。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [matmul/matmul_example.cpp](matmul/matmul_example.cpp) · [详情](../migration/sample-reports/cuSPARSELt/matmul/matmul_example.cpp.md) | hipsparselt+hipsparse / hipSPARSELt | L2 / UNSUPPORTED | 锁定 ROCm 10.1.0 hipSPARSELt 已编译，但 gfx1201 缺少 kernel bundle；实机返回 NOT_IMPLEMENTED/无法加载 TensileLibrary_lazy_gfx1201，固定源码架构检查也拒绝 gfx1201。仅限此版本/硬件/后端；保留 structured prune/compress/matmul 契约，未改成 dense。 | BLOCKED / BLOCKED | [记录](../migration/reports/upstream-support/sources.json)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSPARSELt_matmul_matmul_example.cpp) |
| [matmul_advanced/matmul_advanced_example.cpp](matmul_advanced/matmul_advanced_example.cpp) · [详情](../migration/sample-reports/cuSPARSELt/matmul_advanced/matmul_advanced_example.cpp.md) | hipsparselt+hipsparse / hipSPARSELt | L2 / UNSUPPORTED | 锁定 ROCm 10.1.0 hipSPARSELt 已编译，但 gfx1201 缺少 kernel bundle；实机返回 NOT_IMPLEMENTED/无法加载 TensileLibrary_lazy_gfx1201，固定源码架构检查也拒绝 gfx1201。仅限此版本/硬件/后端；保留 structured prune/compress/matmul 契约，未改成 dense。 | BLOCKED / BLOCKED | [记录](../migration/reports/upstream-support/sources.json)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSPARSELt_matmul_advanced_matmul_advanced_example.cpp) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
