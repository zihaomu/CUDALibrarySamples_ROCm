# cuTENSOR - Samples#

* [Documentation](https://docs.nvidia.com/cuda/cutensor/index.html)

# Install

## Linux 

You can use make or cmake to compile the cuTENSOR samples.

With make

```
export CUTENSOR_ROOT=<path_to_cutensor_root>
make
```

With cmake

```
cmake -S. -B build -DCUTENSOR_ROOT=<path_to_cutensor_root>
make --build build -j 8
```

## Windows

We recommend using cmake with Ninja generator to compile:

```
cmake -S. -B build -DCUTENSOR_ROOT=<path_to_cutensor_root> -G Ninja
cmake --build build
```

To run the examples, make sure the library files are located in a directory included in your %PATH%

<!-- ROCM-MIGRATION:START -->
## ROCm 迁移实时状态

13 个独立源入口；PASSED 5，PARTIAL 0，FAILED 8，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：hipTensor, rocBLAS + HIP permutations。候选不等于已使用；基础探针成功也不等于整库迁移成功。

hipTensor 的 binary/trinary、permutation、reduction 原始 extents 与小尺寸全部输出通过 CPU/CUDA；FP32 contraction 架构 gate 缺口由 rocBLAS + HIP 排列补足；其它高级/绑定场景仍失败。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [python/cutensor/tensorflow/einsum_test.py](python/cutensor/tensorflow/einsum_test.py) · [详情](../migration/sample-reports/cuTENSOR/python/cutensor/tensorflow/einsum_test.py.md) | 未验证使用库 | L0 / FAILED | Python 原始入口依赖 parameterized, parameterized, tensorflow, tensorflow.python.platform, tensorflow.test, cutensor.tensorflow；锁定 AMD 环境中的 import 资格检查未通过，尚无保留该例 API/算法的 AMD Python 改写。安装 CPU 包不能充作 GPU 迁移。 日志：/python/cpython-3.13.13-linux-x86_64-gnu/lib/python3.13/importlib/__init__.py", line 88, in import_module     return _bootstrap._gcd_import(name[level:], package, level)            ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "<frozen importlib._bootstrap>", line 1395, in _gcd_import   File "<frozen importlib._bootstrap>", line 1360, in _find_and_load   File "<frozen importlib._bootstrap>", line 1324, in _find_and_load_unlocked ModuleNotFoundError: No module named 'parameterized'  | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084354.110802Z/languages/cuTENSOR_python_cutensor_tensorflow_einsum_test.py)；[记录](../migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuTENSOR_python_cutensor_tensorflow_einsum_test.py) |
| [python/cutensor/torch/einsum_test.py](python/cutensor/torch/einsum_test.py) · [详情](../migration/sample-reports/cuTENSOR/python/cutensor/torch/einsum_test.py.md) | 未验证使用库 | L0 / FAILED | Python 原始入口依赖 torch, unittest, parameterized, parameterized, cutensor.torch；锁定 AMD 环境中的 import 资格检查未通过，尚无保留该例 API/算法的 AMD Python 改写。安装 CPU 包不能充作 GPU 迁移。 日志：/python/cpython-3.13.13-linux-x86_64-gnu/lib/python3.13/importlib/__init__.py", line 88, in import_module     return _bootstrap._gcd_import(name[level:], package, level)            ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "<frozen importlib._bootstrap>", line 1395, in _gcd_import   File "<frozen importlib._bootstrap>", line 1360, in _find_and_load   File "<frozen importlib._bootstrap>", line 1324, in _find_and_load_unlocked ModuleNotFoundError: No module named 'parameterized'  | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084354.110802Z/languages/cuTENSOR_python_cutensor_torch_einsum_test.py)；[记录](../migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuTENSOR_python_cutensor_torch_einsum_test.py) |
| [blocksparse.cu](blocksparse.cu) · [详情](../migration/sample-reports/cuTENSOR/blocksparse.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuTENSOR/blocksparse.cu:65:7: error: unknown type name 'cutensorBlockSparseTensorDescriptor_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuTENSOR/blocksparse.cu:119:5: error: unknown type name 'cutensorBlockSparseTensorDescriptor_t' | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_blocksparse.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_blocksparse.cu) |
| [contraction.cu](contraction.cu) · [详情](../migration/sample-reports/cuTENSOR/contraction.cu.md) | rocBLAS + HIP / FP32 GEMM and GPU tensor permutations | L4 / PASSED | hipTensor 在 gfx1201 拒绝 FP32 contraction，FP16 compute 探针亦有数值失败；选用 rocBLAS SGEMM + HIP 排列，保留原始 modes/extents、FP32、alpha=1.1/beta=0。小尺寸全量 CPU（beta=0.5）及原始规模全量有限值/32 个双精度 CPU 抽样点通过。未声称原始随机输入逐值等同或 JIT/cache 已实现。 | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T091046.204877Z/native-probes/tensor_rocblas)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_contraction.cu) |
| [contraction_jit.cu](contraction_jit.cu) · [详情](../migration/sample-reports/cuTENSOR/contraction_jit.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuTENSOR/contraction_jit.cu:43:48: error: use of undeclared identifier 'CUTENSOR_COMPUTE_DESC_3XTF32'; did you mean 'HIPTENSOR_COMPUTE_DESC_32F'?；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuTENSOR/contraction_jit.cu:213:34: error: use of undeclared identifier 'CUTENSOR_ALGO_GETT' | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_contraction_jit.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_contraction_jit.cu) |
| [contraction_plan_cache.cu](contraction_plan_cache.cu) · [详情](../migration/sample-reports/cuTENSOR/contraction_plan_cache.cu.md) | hiptensor / hipTensor | L2 / FAILED | run 失败：Total memory: 0.45 GiB File (./planCache.bin) doesn't seem to exist. Exception caught! Exiting. HIPTENSOR_STATUS_ARCH_MISMATCH  | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_contraction_plan_cache.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_contraction_plan_cache.cu) |
| [contraction_trinary.cu](contraction_trinary.cu) · [详情](../migration/sample-reports/cuTENSOR/contraction_trinary.cu.md) | hiptensor / hipTensor | L2 / FAILED | run 失败： TIMEOUT | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_contraction_trinary.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_contraction_trinary.cu) |
| [einsum.cu](einsum.cu) · [详情](../migration/sample-reports/cuTENSOR/einsum.cu.md) | hiptensor / hipTensor | L2 / FAILED | run 失败：Exception caught! Exiting. HIPTENSOR_STATUS_ARCH_MISMATCH  | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_einsum.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_einsum.cu) |
| [elementwise_binary.cu](elementwise_binary.cu) · [详情](../migration/sample-reports/cuTENSOR/elementwise_binary.cu.md) | hipTensor / hipTensor | L4 / PASSED | 使用 hipTensor / hipTensor 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T120648.693848Z/batch2-cuda/cuTENSOR_elementwise_binary.cu) |
| [elementwise_permute.cu](elementwise_permute.cu) · [详情](../migration/sample-reports/cuTENSOR/elementwise_permute.cu.md) | hipTensor / hipTensor | L4 / PASSED | 使用 hipTensor / hipTensor 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T120648.693848Z/batch2-cuda/cuTENSOR_elementwise_permute.cu) |
| [elementwise_permute_padding.cu](elementwise_permute_padding.cu) · [详情](../migration/sample-reports/cuTENSOR/elementwise_permute_padding.cu.md) | hiptensor / hipTensor | L2 / FAILED | run 失败： | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_elementwise_permute_padding.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_elementwise_permute_padding.cu) |
| [elementwise_trinary.cu](elementwise_trinary.cu) · [详情](../migration/sample-reports/cuTENSOR/elementwise_trinary.cu.md) | hipTensor / hipTensor | L4 / PASSED | 使用 hipTensor / hipTensor 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T120648.693848Z/batch2-cuda/cuTENSOR_elementwise_trinary.cu) |
| [reduction.cu](reduction.cu) · [详情](../migration/sample-reports/cuTENSOR/reduction.cu.md) | hipTensor / hipTensor | L4 / PASSED | 使用 hipTensor / hipTensor 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。 | PASSED / PASSED | [记录](../migration/reports/batch2-validation.json)；[记录](../migration/reports/evidence/20261109T120648.693848Z/batch2-cuda/cuTENSOR_reduction.cu) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
