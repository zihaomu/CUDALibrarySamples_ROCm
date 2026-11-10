# R5 Fortran 稀疏绑定验收

8 个原始来源入口：`cuDSS/{fortran,nvfortran}/{batch,uniform_batch,reordering_phase,residual}`。保留原始 CUDA/Fortran 文件，移植入口实际用 ROCm flang 编译并运行标准 Fortran `ISO_C_BINDING`；不声称 NVIDIA 编译器可用。

实际路线：CPU 稀疏符号最小度排序和布局编排，项目 HIP CSR pivot LU/solve 数值核心。查询的 P 经独立 LU 重构检查确实用于 GPU 分解；GENERAL 不做对称展开。验证尺寸为 5/6/7/9，FP64；实现 n<=64 与绝对 pivot 阈值1e-13是限制，未外推任意矩阵。

| 功能 | 恢复的原始合同 |
| --- | --- |
| batch | 两种尺寸/CSR、独立数组/解和状态 |
| uniform_batch | 共同pattern、两份常驻GPU factor；全批后index1更新values/B并重分解求解到X slot0，未选factor/另一slot保持；实际3次factor+3solve |
| reordering_phase | 独立查询排列及size_t字节数后继续GPU分解/求解；最小度排序与厂商METIS顺序不保证相同，原Fortran差异为警告 |
| residual | 原始GENERAL CSR、2 RHS、ldb7/ldx10；Fortran程序自身计算每RHS与最大相对残差并按1e-12拒绝，独立CPU另核对 |

56个语言入口case通过AMD与独立FP64参考，含48正向和8奇异info场景；24种不同正向输入通过真实native cuDSS C++数学核心。native共28种输入27通过，额外GENERAL奇异输入即便factor同步后仍返回INFO0和NaN；后solve INFO探针也为0。该项保留为**原生数值失败**，`numeric_baseline_passed=false`，不推断内部原因，不计三方数值通过。HIP对该非法/奇异场景返回非零info。

17项故障注入含成对污染native padding、实际UBATCH GPU RHS/values回读；8个真实Fortran非法descriptor；13项C ABI宽度/阶段/生命周期与values更新；4组真实GPU trace；9项证据身份反例。构建依赖精确绑定封存result/depfile/源对象和实际8个二进制，native构建身份、SDK和266个输入文件也固定。

**CUDA原语言baseline仍BLOCKED**：5090主机缺少匹配的Fortran编译器/vendor module。CUDA C++ cuDSS同字节数学对照通过，单独标记，不能写为原Fortran程序运行通过。

[复合资格](rewrite-R5-qualification.json)、[独立复审](rewrite-R5-review.json)、[AMD/CPU](rewrite-sparse-binding-rocm-validation.json)、[native/CPU](rewrite-sparse-binding-cuda-validation.json)、[原生失败观察](rewrite-sparse-native-failure.json)、[17故障](rewrite-sparse-binding-negative.json)、[运行边界](rewrite-sparse-binding-runtime.json)、[C ABI](rewrite-sparse-binding-abi.json)、[真实GPU核](rewrite-sparse-binding-traces.json)、[完整逐次索引](rewrite-experiments.jsonl)。

C++ `simple_reordering_phase` 历史漏验已撤回整例资格。缺少的factor/solve已修复并满足原始2e-15解误差，但严格METIS向量与最小度算法不同仍PARTIAL。[修复与剩余原因](rewrite-reordering-cpp-repair.json)。其余65个前端入口仍需对应GPU核心和原语言合同，不随本8例升级。
