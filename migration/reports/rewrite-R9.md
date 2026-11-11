# R9：九个矩阵helper与CRC32 benchmark

状态：IN_PROGRESS，尚未签发整例资格。基线231/639通过、117功能族。合同：migration/rewrite/helpers-benchmark.json。

helper：真实C++及标准Fortran ISO_C_BINDING入口；项目CPU描述符对象借用用户host形状数组与HIP GPU数据/指针表，不冒充GPU求解算法。元数据、可选字段、指针重绑、原nnz保持、完整数据与销毁后用户storage检查。源语言差异按原例保留。第一版45 AMD/CPU与45 native cuDSS/CPU通过后，前置审查发现C++ batch原始host shape别名及6个irregular覆盖不足；已补原始别名和真实CSR/leading-dimension变化，旧证据保留，新版重验中。

CRC benchmark：保留原始harness/CLI与默认扫描规则；以HIP分段IEEE CRC32和GPU GF2合并实现真实配置搜索，每格最终event覆盖全部计算。默认hipRAND seed42不声称逐位等于cuRAND；默认各自真实输入独立CPU验收，冻结小storage同字节三方比较。有效格-inf/NaN/非正耗时不可验收，-1只代表容量跳过。大于4GiB的长度运算另设独立边界探针。

实验：[事件索引](rewrite-experiments.jsonl)、[helper构建](rewrite-R9-helper-build.json)、[AMD与CPU](rewrite-R9-helper-rocm.json)、[原生CUDA构建](rewrite-R9-helper-native-build.json)、[原生CUDA与CPU](rewrite-R9-helper-cuda.json)。Fortran原CUDA编译器/module限制与兼容C++原生API数学对照分列。

最终运行：45 helper AMD/CPU＋45 native cuDSS/CPU全部通过；30故障、9非法语言入口、22 ABI检查。CRC默认16 GiB在AMD物理GPU1和RTX5090分别执行（26有效/10跳过），四个小输入同字节三方通过；complete小输入66有效/55跳过。GPU trace确认12次分段和74次合并，符合三配置搜索及最终完整重算；另一次实际重复一致。7故障、8 CLI、6 GPU/libz长度边界全部通过。

[CRC构建](rewrite-R9-crc-benchmark-build.json) · [AMD](rewrite-R9-crc-benchmark-rocm.json) · [原生CUDA](rewrite-R9-crc-benchmark-cuda.json) · [故障及运行检查](rewrite-R9-crc-benchmark-checks.json) · [真实GPU trace与重复](rewrite-R9-crc-benchmark-trace.json)。首次默认显存分配及归档收集失败均完整保留。
