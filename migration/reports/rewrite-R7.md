# R7 真实 2:4 结构化稀疏实现验收

两个原始默认FP16入口 `cuSPARSELt/matmul`、`matmul_advanced` 完成项目HIP算法重写。实际使用HIP GPU，原始NVIDIA源文件保留。

| 阶段 | 实际实现 |
| --- | --- |
| TILE prune | GPU枚举90种合法4×4 mask，用精确FP64 L1评分选择每行/列各2位置；CPU只准备常量mask，独立oracle使用容量DP |
| compress/check | GPU保存每组2个FP16值和1字节metadata（低4位编码两个索引）；GPU检查行/列结构；数学输入存储为dense FP16的62.5%，不把全程序显存说成压缩后占用 |
| sparse matmul | GPU核只读压缩values/metadata和B/C，不读dense A；FP32累积、FP16输出 |
| basic | 原32×32×64、N/T、alpha=beta=1；两种真实GPU映射候选使用HIP event搜索，最终按本次计时选择；不据此声称跨设备速度提升 |
| advanced | 原32×16×32双batch，三个stride均额外128；FP16 bias、阈值1/上界15的ReLU；原C只随机初始化16/32行、余行零也按真实字节保留。项目plan查询为实际单kernel splitK=1/buffers=0 |

14组输入通过AMD/独立FP64容量DP与矩阵参考，14组原生CUDA稀疏数学对照也通过，最大输出误差实测0 FP16 ULP（验收门槛2 ULP）。CUDA对照使用对应HIP裁剪的A，显式GPU packing为原生支持的contiguous descriptor，再调用真实 `cusparseLtSpMMACompress` 和 `cusparseLtMatmul`。这是独立稀疏数学对照；合法最大L1裁剪tie允许不同mask，不声称整个pipeline与厂商逐位相同。

两个真正原始CUDA算法程序也单独运行和验收，原生prune结果各自满足独立DP与数学参考。观察副本只加D2H输出、固定默认随机seed和定义inactive padding；原树未改。最初错误C初始化fixture和原生padded LDA拒绝日志保留，已分别纠正/明确加入CUDA layout adapter。

17项语义故障注入命中预期拒绝；10个实际非法descriptor被程序拒绝；GPU checker另跑1有效+3损坏metadata。真实trace包含prune/compress/check和9次basic或1次advanced稀疏乘法，runtime copyBuffer核另列，未将拷贝计作数值计算。10项身份反例检查包括裁剪依赖表、替换build/run/输入parent、原例输出重定向和CPU摘要篡改。

原生hipSPARSELt在当前ROCm10.1/gfx1201仍失败：基础例缺Tensile gfx1201 kernel bundle；高级例遇到未实现的属性接口。项目HIP重写的PASSED与原生库能力分别登记；项目压缩格式与厂商opaque格式也分别登记。FP8/INT8可选编译分支未在本批支持范围。

[复合资格](rewrite-R7-qualification.json)、[独立复审](rewrite-R7-review.json)、[AMD/CPU](rewrite-sparse24-rocm-validation.json)、[native稀疏/CPU](rewrite-sparse24-cuda-validation.json)、[原CUDA程序/CPU](rewrite-sparse24-original-validation.json)、[原生AMD失败](rewrite-sparseLt-native-route.json)、[17故障](rewrite-sparse24-negative.json)、[10运行边界](rewrite-sparse24-runtime.json)、[实际GPU metadata损坏](rewrite-sparse24-GPU-negative.json)、[实际GPU核](rewrite-sparse24-traces.json)、[逐次事件](rewrite-experiments.jsonl)。

TILE语义依据：[NVIDIA cuSPARSELt函数文档](https://docs.nvidia.com/cuda/cusparselt/functions.html)、[AMD hipSPARSELt prune类型定义](https://rocm.docs.amd.com/projects/hipSPARSELt/en/docs-7.2.4/doxygen/html/group__types__module.html)。文档用于核对算法合同，运行证据均为锁定ROCm10.1环境。
