# R3 NCC 与 batched rank-SVD 验收

2 个原始入口完成全合同复合资格：15 个输入在 AMD、独立 CPU、同字节 CUDA 检查通过；NCC 另用真正原生 NPP 全输出比较，SVD 原始配置另用原生 gesvda。24 项输出故障注入、18 项实际 CLI/descriptor 检查通过。

| 入口 | 路线与范围 | 资格 |
| --- | --- | --- |
| `NPP/templateMatching::templateMatching.cpp` | 固定2048×1024 RAW、全部原CLI/PGM/GPU timing；HIP NCC/argmax；8输入 | [PASSED](evidence/rewrite/R3/NPP_templateMatching__templateMatching.cpp/20261110T092525.448735Z-R3-composite-qualification-ad7d1f1dc9/qualification.json) |
| `cuSOLVER/gesvdaStridedBatched::cusolver_gesvdaStridedBatched_example.cu` | 原FP32 3×2双batch；hipSOLVER/rocSOLVER full GPU SVD + HIP rank截断/VT→V/FP64残差；7输入 | [PASSED](evidence/rewrite/R3/cuSOLVER_gesvdaStridedBatched__cusolver_gesvdaStridedBatched_example.cu/20261110T092526.610000Z-R3-composite-qualification-e9da6e4aed/qualification.json) |

NCC：原生 NPP 大图路径的常量模板为 FLT_MAX，常量图块近零；32×24 小图探针不能直接推广。最初错误策略的 HIP 定位失败与早期 oracle 保留，修复后默认原例定位到(1300,850)，全部score与native最大差约1.06e-4。常量输入原始harness返回1的歧义路径也逐项重现。[原生逐像素比较](rewrite-ncc-native-comparison.json)、[独立FP64/PGM/最大值验收](rewrite-ncc-validation.json)、[四类故障注入](rewrite-ncc-negative.json)、[CLI](rewrite-ncc-runtime.json)。

SVD：完整SVD是明确登记的替代算法，不声称与NVIDIA内部近似实现相同。GPU核计算截断与返回Frobenius残差；CPU独立检查奇异值、正交性、Eckart–Young最优截断、全文件大小/有限性/padding/非负范数。[AMD](rewrite-extension-rocm-validation.json)、[CUDA数学基线](rewrite-extension-cuda-validation.json)、[原生gesvda及其实际返回估计残差](rewrite-extension-native-approx-validation.json)、[20类故障注入](rewrite-svd-negative.json)、[11种非法descriptor](rewrite-svd-runtime.json)。

执行位置：[实际kernel轨迹](rewrite-solver-backend-traces.json)含rocSOLVER bdsqr_compute等求解核。Xgeev三例仅有数据拷贝与原例残差验证BLAS，仍不能计作GPU特征分解支持。

[独立复审](rewrite-R3-review.json)、[反例身份测试](rewrite-R3-qualification-tests.json)、[全量封存审计](rewrite-evidence-audit.json)、[原24项逐例合同缺口](rewrite-R3-gaps.md)、[逐次事件](rewrite-experiments.jsonl)。

其余22个PARTIAL仍有原始descriptor、低精度collective、像素/metadata、CPU回退、RNG序列、NVBENCH或JPEG后端等缺项；静态合同复审不是新增GPU成功。性能无跨设备速度结论。
