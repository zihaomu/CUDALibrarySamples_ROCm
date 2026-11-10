# R6：长尾 SDK、设备算法与分布式研究

状态：**ASSESSMENT_COMPLETE_PORTS_PENDING**。224 个 R6 入口全部保留未支持结论；另评估 R4/R5 相关路线。以下实测只证明基础能力或格式边界，不签发整例资格。

| 专题 | R6 入口 | 可实施路线 | 已完成探测 / 尚缺条件 | 工程量与恢复条件 |
| --- | ---: | --- | --- | --- |
| MathDx device BLAS / FFT / solver / RNG / codec | 132 | 调用方 HIP kernel 内算法；rocRAND device 按序列合同复用 | 原 vendor include 在锁定 AMD SDK 编译失败已留完整 stderr；R1/R2 的三个 solver 不覆盖这里132例 | L–XL；保持 device-callable/fusion、原 dtype/布局/同步，逐例冻结原生输入和独立 oracle |
| libmathdx JIT | 12 | HIPRTC 生成 AMD 源码并通过 HIP module API 加载 HSACO | 实际 compile→GetCode→LoadData→Launch：[1,2,3,4]→[3,5,7,9]通过 | XL；实现各生成器的 options/error/recompile；不能直接加载 NVIDIA cubin/PTX |
| 分布式 BLAS / solver / FFT / tensor | 36 | MPI＋RCCL＋局部数学库＋HIP 分布 | 实际物理 GPU0/2 上局部 GEMM＋AllGather 与 CPU 全值对比通过；不代表 MPI descriptor、二维 process grid、子矩阵或多节点算法 | XL；原全局布局、rank、通信 dtype、异卡与边界验证，多节点另备环境 |
| cuEST | 29 | LibintX 积分、GauXC XC、QUICK 特定 HF/DFT 子功能候选 | 固定三个源码提交、HIP 开关和许可 hash；镜像无对应 Python 模块、无 cuEST API；尚未构建候选 GPU 算法 | XL；先构建依赖，再逐原例 AO/basis/operator/gradient 比较；ECP/PCM/VV10 不能由普通积分库推定覆盖 |
| cuPQC | 4 | HIP NTT/Keccak/有限域；独立标准参考与 KAT | cupqc/cuhash includes 不可用；已有 SHA 不代表 ML-KEM/ML-DSA/Poseidon2/Merkle | XL；冻结原例参数/格式，KAT、无效输入拒绝、精确字节编码与实际 GPU 工作 |
| JPEG 框架 | 1 | rocJPEG 与显式文件/metadata 层 | SDK/符号调查已存；原框架仍需移植 | L；原 CLI、像素格式、stride、batch、错误行为与 GPU 解码轨迹 |
| JPEG2000 | 4 | HIP DWT＋tier-1/2 编解码研究 | 对仓库真实 JP2 运行 rocJPEG parser，实际拒绝并记录输入 hash；只否定 JPEG parser 路线 | XL；lossy/lossless、bit depth、ROI/tile，OpenJPEG/native 对照与跨解码 |
| TIFF | 6 | hipCIM JPEG tile reader 候选；额外 container/encoder | 对真实 TIFF 运行 rocJPEG parser，实际拒绝；hipCIM 未安装/未构建 | XL；文档测试 profile 与本机 Python3.13/gfx1201/ROCm10.1不同；保持 ROCm 锁定，评估兼容构建并区分 CPU/GPU codec |

M/L/XL 是任务量估计，不承诺日期。全部入口精确源码 SHA、API token、缺失 case、原错误、下一探针和历史日志见 [408 入口逐项清单](rewrite-remaining-assessment.md)及[机器可读表](rewrite-remaining-assessment.json)。R5 原始73个前端已验收8个、仍有65个；额外一项旧 C++ 排序资格撤销后计入 R5 待办，共66个。R4本轮完成一个经过独立审查的 CRC32 小批，其余96个有明确去向。

## 候选与不能原样移植的边界

候选不记入实际使用库。GitHub API 匿名请求返回403的四次失败保留；改用 git ls-remote 固定 HEAD，从该提交读取 README/CMake/许可文件并记录 SHA256。没有因此声称编译或运行成功。[四个候选源码、提交与日志](rewrite-R6-candidate-sources.json)。

- [LibintX](https://github.com/ValeevGroup/libintx)声明 HIP Gaussian integral backend；[GauXC](https://github.com/wavefunction91/GauXC)声明 HIP XC/K integrator；[QUICK](https://github.com/merzlab/QUICK)有 HIP HF/DFT 路线。它们是组件候选，完整 [cuEST 方法面](https://docs.nvidia.com/cuda/cuest/api_methods.html)还包括 ECP、PCM、VV10、梯度等合同。
- [hipCIM 功能表](https://rocm.docs.amd.com/projects/hipCIM/en/docs-26.08/reference/supported-functionality.html)区分 JPEG 压缩 TIFF tile GPU decode 与其它压缩的 CPU 路径；[安装文档](https://rocm.docs.amd.com/projects/hipCIM/en/latest/installation/installation.html)的测试环境不能当作本机已验证兼容。
- [FIPS 203 ML-KEM](https://csrc.nist.gov/pubs/fips/203/final)、[FIPS 204 ML-DSA](https://csrc.nist.gov/pubs/fips/204/final)是后续标准参考入口；具体参数和勘误在实现时固定。Poseidon2/Field2048 参数以原例代码为准，不猜测有限域。

不能原样移植的是 NVIDIA 专用二进制格式、硬件资源划分/私有算法 ID 和精确厂商策略身份；这与公开数学算法能否在 AMD 上重写分别判断。目前没有把“缺头文件”登记为数学算法永远不可能实现。缺基线、工具链、资源或尚未实现的条目仍保持未支持。

## 实验入口

- [HIPRTC 与真实 JP2/TIFF parser 输入和结果](rewrite-R6-foundation-probes.json)。
- [实际双物理 GPU GEMM＋AllGather](rewrite-R6-distributed-probe.json)。
- [SDK header 编译、库符号与 Python 模块调查](rewrite-R4-R6-SDK-surfaces.json)。符号存在不等于 GPU 算法执行。
- [固定候选源码与首次403失败的后续恢复](rewrite-R6-candidate-sources.json)。
- [完整实验事件索引](rewrite-experiments.jsonl)。每条 JSON 的 evidence 指向完整 reproduce.json、logs、source.json、sealed.json；失败同样归档。

GPU3 没有参加计算；双卡探针明确记录物理0/2与PCI地址。首次严格空闲检查未通过的 ENV_BLOCKED 也保留；后续小型功能探针记录可用性，不签发性能比率。
