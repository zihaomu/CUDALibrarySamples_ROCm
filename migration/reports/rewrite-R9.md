# R9：九个矩阵helper与CRC32 benchmark

状态：IN_PROGRESS，尚未签发整例资格。基线231/639通过、117功能族。合同：migration/rewrite/helpers-benchmark.json。

helper：真实C++及标准Fortran ISO_C_BINDING入口；项目CPU描述符对象借用用户host形状数组与HIP GPU数据/指针表，不冒充GPU求解算法。元数据、可选字段、指针重绑、原nnz保持、完整数据与销毁后用户storage检查。源语言差异按原例保留。第一版45 AMD/CPU与45 native cuDSS/CPU通过后，前置审查发现C++ batch原始host shape别名及6个irregular覆盖不足；已补原始别名和真实CSR/leading-dimension变化，旧证据保留，新版重验中。

CRC benchmark：保留原始harness/CLI与默认扫描规则；以HIP分段IEEE CRC32和GPU GF2合并实现真实配置搜索，每格最终event覆盖全部计算。默认hipRAND seed42不声称逐位等于cuRAND；默认各自真实输入独立CPU验收，冻结小storage同字节三方比较。有效格-inf/NaN/非正耗时不可验收，-1只代表容量跳过。大于4GiB的长度运算另设独立边界探针。

实验：[事件索引](rewrite-experiments.jsonl)、[helper构建](rewrite-R9-helper-build.json)、[AMD与CPU](rewrite-R9-helper-rocm.json)、[原生CUDA构建](rewrite-R9-helper-native-build.json)、[原生CUDA与CPU](rewrite-R9-helper-cuda.json)。Fortran原CUDA编译器/module限制与兼容C++原生API数学对照分列。

最终运行：45 helper AMD/CPU＋45 native cuDSS/CPU全部通过；30故障、9非法语言入口、22 ABI检查。CRC默认16 GiB在AMD物理GPU1和RTX5090分别执行（26有效/10跳过），四个小输入同字节三方通过；complete小输入66有效/55跳过。GPU trace确认12次分段和74次合并，符合三配置搜索及最终完整重算；另一次实际重复一致。7故障、8 CLI、6 GPU/libz长度边界全部通过。

[CRC构建](rewrite-R9-crc-benchmark-build.json) · [AMD](rewrite-R9-crc-benchmark-rocm.json) · [原生CUDA](rewrite-R9-crc-benchmark-cuda.json) · [故障及运行检查](rewrite-R9-crc-benchmark-checks.json) · [真实GPU trace与重复](rewrite-R9-crc-benchmark-trace.json)。首次默认显存分配及归档收集失败均完整保留。


## 逐入口范围

| 原始入口 | AMD实现 | 验收范围 | 原CUDA语言基线 |
| --- | --- | --- | --- |
| `cuDSS/simple_dense_matrix_helpers/simple_dense_matrix_helpers.cpp` | C++ → ProjectMatrixHelpers host描述符＋HIP数据/指针表 | original, changed-values, irregular, padding, repeat；metadata/值/索引/指针别名/上下文与销毁后用户storage | 原始CUDA C++程序通过 |
| `cuDSS/simple_sparse_matrix_helpers/simple_sparse_matrix_helpers.cpp` | C++ → ProjectMatrixHelpers host描述符＋HIP数据/指针表 | original, changed-values, irregular, alternate-base, repeat；metadata/值/索引/指针别名/上下文与销毁后用户storage | 原始CUDA C++程序通过 |
| `cuDSS/simple_batch_sparse_matrix_helpers/simple_batch_sparse_matrix_helpers.cpp` | C++ → ProjectMatrixHelpers host描述符＋HIP数据/指针表 | original, changed-values, irregular, alternate-base, repeat；metadata/值/索引/指针别名/上下文与销毁后用户storage | 原始CUDA C++程序通过 |
| `cuDSS/fortran/dense_matrix_helpers/dense_matrix_helpers.f90` | 标准Fortran ISO_C_BINDING → ProjectMatrixHelpers host描述符＋HIP数据/指针表 | original, changed-values, irregular, padding, repeat；metadata/值/索引/指针别名/上下文与销毁后用户storage | BLOCKED：5090无原始Fortran工具链；native C++ cuDSS API同输入对照通过 |
| `cuDSS/fortran/sparse_matrix_helpers/sparse_matrix_helpers.f90` | 标准Fortran ISO_C_BINDING → ProjectMatrixHelpers host描述符＋HIP数据/指针表 | original, changed-values, irregular, alternate-base, repeat；metadata/值/索引/指针别名/上下文与销毁后用户storage | BLOCKED：5090无原始Fortran工具链；native C++ cuDSS API同输入对照通过 |
| `cuDSS/fortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.f90` | 标准Fortran ISO_C_BINDING → ProjectMatrixHelpers host描述符＋HIP数据/指针表 | original, changed-values, irregular, alternate-base, repeat；metadata/值/索引/指针别名/上下文与销毁后用户storage | BLOCKED：5090无原始Fortran工具链；native C++ cuDSS API同输入对照通过 |
| `cuDSS/nvfortran/dense_matrix_helpers/dense_matrix_helpers.cuf` | 标准Fortran ISO_C_BINDING → ProjectMatrixHelpers host描述符＋HIP数据/指针表 | original, changed-values, irregular, padding, repeat；metadata/值/索引/指针别名/上下文与销毁后用户storage | BLOCKED：5090无原始Fortran工具链；native C++ cuDSS API同输入对照通过 |
| `cuDSS/nvfortran/sparse_matrix_helpers/sparse_matrix_helpers.cuf` | 标准Fortran ISO_C_BINDING → ProjectMatrixHelpers host描述符＋HIP数据/指针表 | original, changed-values, irregular, alternate-base, repeat；metadata/值/索引/指针别名/上下文与销毁后用户storage | BLOCKED：5090无原始Fortran工具链；native C++ cuDSS API同输入对照通过 |
| `cuDSS/nvfortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.cuf` | 标准Fortran ISO_C_BINDING → ProjectMatrixHelpers host描述符＋HIP数据/指针表 | original, changed-values, irregular, alternate-base, repeat；metadata/值/索引/指针别名/上下文与销毁后用户storage | BLOCKED：5090无原始Fortran工具链；native C++ cuDSS API同输入对照通过 |
| `nvCOMP/benchmarks/benchmark_crc32.cpp` | 原harness＋HIP分段IEEE CRC32/GF2＋hipRAND | 默认16GiB、bounded/complete/changed/repeat、逐chunk zlib、全部CSV与计时语义、配置搜索、全量重算、CLI错误、64位长度、真实GPU trace | 原生nvCOMP/curand原harness＋只读观测通过；默认RNG数据各自CPU核对 |

六个nvfortran/Fortran来源实现均用ROCm环境flang编译标准Fortran，不能解读为NVIDIA CUDA Fortran编译器支持。描述符对象属于host，用户数据和batch指针表真实分配在HIP GPU；原始只演示元数据的例子不强加不存在的GPU求解。三个C++原程序另验，六个Fortran只用兼容原生API基线。原始稀疏列序、SetCsrPointers后的nnz保持、Fortran第二值更新及batch host shape别名全部分别保留。

## 复现

先核对设备占用和PCI映射，使用项目锁定launcher进入ROCm10.1环境；物理GPU3禁用。完整默认CRC要求16GiB输入及额外工作区，使用有足够空闲显存的允许设备。本文通过运行使用物理GPU1（PCI 0000:23:00.0），原始HIP ordinal与物理编号不同。

```bash
python3 tools/migration/bootstrap_sdk.py
python3 tools/moat/build_helpers.py
python3 tools/moat/run_helpers.py
python3 tools/moat/helper_negative.py
python3 tools/moat/helper_runtime.py
python3 tools/moat/build_crc_benchmark.py
python3 tools/moat/run_crc_benchmark.py
python3 tools/moat/crc_benchmark_checks.py
python3 tools/moat/profile_crc_benchmark.py
```

CMake登记：`rewrite_matrix_helpers` 和 `rewrite_crc32_benchmark`。CUDA对照分别为`cuda_helpers.py`、`cuda_helper_originals.py`、`cuda_crc_benchmark.py`，运行在5090机器并记录实际SDK与二进制身份。审查后资格命令为 `qualify_r9.py` 和 `qualify_r9.py --only crc`，只有复合资格通过才能由`publish_r9.py`更新支持状态。

[干净副本构建与13个原始/小规模重放](rewrite-R9-clean-replay.json)包含16项既有CTest；独立于两后端默认16GiB主实验，不把bounded冷重放称为默认规模冷复现。大型原始输入保留在实验机器本地/5090远端，seal记录大小与SHA；发布归档保留命令、原始stdout/stderr、CSV、全部chunk校验、环境、源码CAS、失败证据和远端input receipt。
