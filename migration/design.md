# CUDA Samples on ROCm：生态库迁移与验证方案

日期：2026-11-09。阶段：M0–M5 已逐批执行并完成最终核对与归档；全部入口均有尝试结果，具体成功与缺口见第 12 节。当前进度见第 11、12 节，初始盘点表保留为历史记录。

## 1. 项目目标与本次交付

以 `CUDALibrarySamples_ROCm` 中的 NVIDIA CUDA Library Samples 为逐例参照，为每个样例选择最合适的 AMD/ROCm 生态库，实现可独立构建、运行、验证的 ROCm 版本。例如，cuBLAS 样例优先评估 **hipBLAS（AMD 后端为 rocBLAS）**，也允许直接使用 rocBLAS，以实际功能、目标 GPU 支持和验证结果决定选型。

项目最终应回答三个问题：

1. 这个 CUDA 样例在 AMD 上用了什么库、哪些 API、如何实现？
2. 原样例的哪些功能已在什么环境下验证成功，哪些仍未完成？
3. 如果失败，失败在哪个阶段、根因是什么、有什么可复现证据和下一步？

迁移目标包括数值结果、数据布局以及原样例重点展示的行为。只替换 CUDA 调用名称、只编译成功，或用 CPU 算完结果，都不能自动记为“ROCm 迁移成功”。自定义 HIP kernel 可以补充库功能，但须明确记录；不能将所有样例重写成自定义 kernel 后宣称完成了 AMD 生态库对标。

本文保留设计规则与初始环境盘点，并在第 11 节逐步记录实施。M0–M5 均已执行；可运行实现、逐例失败/缺口、CUDA/CPU 对照与证据随仓库交付，最终结果见第 12 节。未完成的原始功能仍明确显示 FAILED/PARTIAL/BLOCKED，不将计划执行完毕解释为全部迁移成功。

## 2. 实际仓库与环境快照

仓库：`/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm`。

| 项目 | 2026-11-09 盘点结果 |
| --- | --- |
| 起始 Git commit | `8b0573b11d183d9b3a36cd2955aa31c16cc61b95` |
| commit 说明 | `nvJPEG2k: Update samples for nvJPEG2k 0.12.0` |
| 起始工作区 | `git status --short` 无输出 |
| 已跟踪文件 | 2,188 个 |
| 顶层样例目录 | 25 个；将 MathDx 拆成 6 个库后，按 30 个库级子项目管理 |
| 构建文件 | 362 个 `CMakeLists.txt`；另有 Makefile 等，不能只扫描 CMake |
| 源文件 | `.cu` 352、`.cpp` 160、`.c` 79、`.f90` 98、`.cuf` 36、`.py` 141，共 866 个 |
| 现有 ROCm 成果 | 在本次源码及构建/说明文件盘点中未发现 ROCm 移植或验证记录；已证实成功为 0，未开展尝试，不报告迁移失败数 |

**866 是源文件数，不是样例数。** 其中有工具、辅助模块和测试；一个目录也可能构建多个可执行文件，例如 `cuRAND/Host/philox` 有 uniform、normal、lognormal、poisson 四个程序。后续须以独立可运行目标/脚本为最小样例单位，再展开测试参数。

以实际文件及构建定义为准，不只依赖原 README：例如 `cuSOLVER` 的 README 有 `MgGetrs` 链接，而实际目录是 `MgGetrf`；`cuTENSORMp` 实际存在但没有自身 README。迁移清单必须覆盖这类遗漏。

### 2.1 AMD 环境

遵循现有工作区 [`AGENTS.md`](../../AGENTS.md)：新实验使用 **ROCm 10.1.0**，通过现有 [`rocm10-launch.sh`](../../rocm10-launch.sh) 启动锁定基础环境，禁止静默回退到 ROCm 7。

已读取的基础锁文件为 [`foundation.lock.json`](../../deepinfer_workspace/DeepInfer/docker/rocm10/foundation.lock.json)（链接相对本文目录），其中记录：

- profile：`rocm10-foundation-r9700-v1`；目标架构 `gfx1201`。
- image ID：`sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03`。
- HIP build：`7.16.26385`。这是 ROCm 10.1 环境的 HIP 组件版本，不要求 HIP 版本也以 10 开头。
- 排除物理 GPU3；小规模实验优先使用空闲 GPU0/1；使用 GPU4–7 前检查占用及已有 reservation 文件。

以上是**读取已有锁文件**的结果，本次未重新执行 AMD 环境资格检查。后续须另建本项目的环境锁，核验每个需要的头文件、动态库、CMake package、库版本及 `gfx1201` kernel；基础镜像通过验证不代表所有 ROCm 数学/媒体库均已安装或适配该 GPU。

### 2.2 CUDA 对照机器

已通过现有 SSH alias `nvidia-5090x2` 完成只读查询：

| 项目 | 实际查询结果 |
| --- | --- |
| GPU | 2 × NVIDIA GeForce RTX 5090，每卡显示 32,607 MiB |
| NVIDIA 驱动 | `615.71.09` |
| CUDA 编译器 | `/usr/local/cuda-13.4/bin/nvcc`，`13.4.92` |
| PATH | 非交互 SSH 默认 PATH 中未发现 `nvcc`，需显式指定 Toolkit 路径 |
| 双卡拓扑 | `nvidia-smi topo -m` 报告 `NODE`，不可按 NVLink 环境设计实验 |

仅确认机器与编译器存在，未验证 cuDSS、MathDx、cuEST、cuPQC 等独立 SDK 是否齐备，未验证 P2P 能力，也未运行 CUDA 样例。实验前重查 GPU 占用；本次查询时的空闲状态不能作为以后使用的依据。

## 3. 库选择规则

按以下顺序决策，但不强制所有样例使用同一层接口：

1. **AMD 官方库优先。** 优先选择能完整表达样例语义、支持实际 GPU 的现成库。
2. **兼容接口有利于保留原示例结构时使用 hip*。** 常规 BLAS、SPARSE、SOLVER、FFT、RAND 优先探查 hipBLAS、hipSPARSE、hipSOLVER、hipFFT、hipRAND，并记录实际 AMD 后端。
3. **兼容层缺接口或原生接口更适合时使用 roc*。** 比较功能、工作区、数据布局和性能后选择 rocBLAS、rocSPARSE、rocSOLVER、rocFFT、rocRAND；不能假定绕过一层封装就一定更快。
4. **组合多个库时明确算法实现。** 例如 rocBLAS + RCCL + MPI 只是分布式 GEMM 的组成部分，仍需实现分布、通信及调度逻辑。
5. **缺乏现成接口时，先记录能力缺口再考虑补充 HIP kernel。** 第三方 ROCm 后端或 CPU 实现可作参考、探索方案，但单独标注来源和执行设备。

hipBLAS 是封装层，AMD 上使用 rocBLAS 后端；README 必须同时写清“直接调用库”和“后端库”。[hipBLAS 官方说明](https://rocm.docs.amd.com/projects/hipBLAS/en/latest/)。常用数学库的定位参考 [ROCm 数学与计算库](https://rocm.docs.amd.com/en/develop/components/math-and-compute-libs.html)。具体功能仍以锁定版本和最小复现验证为准。

## 4. 全部库级子项目的候选实现矩阵

**以下是设计时的候选路线，实时状态以项目 README、各库级 README 及 `migration/samples.yaml` 为准。** “候选库”表示拟评估路线；“边界”表示需要验证或补齐的工作。所有库均需单独核验 ROCm 10.1.0 / `gfx1201` 可用性。

| 子项目 | 首选/候选 AMD 生态实现 | 实现边界与重点 |
| --- | --- | --- |
| `cuBLAS` | hipBLAS → rocBLAS；必要时直接 rocBLAS | 常规 Level 1/2/3 先行；Extensions、grouped、3m、Emulation 独立评估，不用普通 GEMM 冒充原特性 |
| `cuBLASLt` | hipBLASLt | 分别核对 descriptor、layout、epilogue、heuristic、batch、数据类型；算法 ID 不跨厂商复用 |
| `cuBLASMp` | rocBLAS/hipBLASLt + RCCL + MPI | TP 通信计算组合与 2D block-cyclic/PBLAS 分开实现；通信库本身不是分布式 BLAS |
| `cuDSS` | 优先调查 AMD 稀疏直接求解路径；rocSOLVER CSR refactorization 仅作适用子集候选 | 需覆盖分析、排序、数值分解、求解；固定模式 refactorization 不能直接替代完整 cuDSS；混合内存、batch、多节点逐项评估 |
| `cuEST` | 尚未确定完整 AMD 对应库；rocBLAS/hipTensor 仅作底层算子候选 | 电子积分、DFT、SCF、梯度及 Python/C 接口需专项调研；替换 GEMM 不能完成量子化学功能 |
| `cuFFT` | hipFFT → rocFFT；必要时直接 rocFFT | 单卡先行；Xt/多卡、布局和 callback 独立验收 |
| `cuFFTMp` | hipFFT MPI 接口 / rocFFT + GPU-aware MPI | 核验分布布局、reshape、slab/pencil、Fortran/JAX；MPI 构建开关及通信依赖需确认 |
| `cuPQC` | 尚未确认完整 AMD 对应库；HIP + rocPRIM 可作部分基础设施候选 | 6 个示例含 ML-KEM、ML-DSA、SHA2/3、Poseidon2、Merkle；需独立算法实现及标准测试向量 |
| `cuRAND` | hipRAND → rocRAND | 按 generator × distribution 管理；序列一致性和分布性质分别验收 |
| `cuSOLVER` | hipSOLVER → rocSOLVER；必要时直接 rocSOLVER | 稠密单卡先行；X/64-bit、Jacobi、近似 SVD、稀疏 QR、Mg 单列 |
| `cuSOLVERMp` | rocSOLVER + rocBLAS + MPI/RCCL 的算法组合，或专项评估第三方 ROCm 后端 | 需要分布式分解/求解算法及数据分布，不能将单卡求解记为多卡完成 |
| `cuSOLVERSp2cuDSS` | 按求解语义评估 hipSOLVER/rocSOLVER 稀疏子集 | 复现 sparse solve、refactorization、特征值等目标；AMD 没有相同的“NVIDIA 旧 API 到 cuDSS”迁移流程 |
| `cuSPARSE` | hipSPARSE → rocSPARSE；必要时直接 rocSPARSE | CSR/COO 先行；SELL、BSR、blocked ELL、custom operators、reuse、graph 等独立探查 |
| `cuSPARSELt` | hipSPARSELt | 稀疏模式、prune/compress、精度、布局及实际 GPU 支持必须验证；密集乘法仅能作参考 |
| `cuTENSOR` | hipTensor；可映射为 GEMM 的子集评估 rocBLAS/hipBLASLt | contraction、reduction、permutation、plan/cache 及 Python 接口逐项确认 |
| `cuTENSORMg` | hipTensor + RCCL/MPI 的分块计算 | 验证完整张量分布、跨卡归约和内存语义 |
| `cuTENSORMp` | hipTensor + MPI/RCCL | contraction、redistribute、unfold/fold 三个程序分别登记 |
| `MathDx/cuBLASDx` | rocWMMA / Composable Kernel + HIP | 块内计算与融合需保留；host 侧 hipBLAS 仅作数值参考，不算设备端接口完成 |
| `MathDx/cuFFTDx` | 评估设备端 FFT 实现；HIP kernel；rocFFT 作参考或降级路线 | thread/block FFT、融合和 LTO/device API 需专项实现；host FFT 不等同于 device FFT |
| `MathDx/cuRANDDx` | rocRAND device API / hipRAND device API | 线程状态、seed/subsequence/offset、执行映射及 NVRTC 迁移分别验证 |
| `MathDx/cuSolverDx` | 评估设备端求解库/自定义 HIP；rocSOLVER 作参考或降级路线 | 块内 LU/QR/Cholesky 等不能直接用 host 侧 rocSOLVER 替换 |
| `MathDx/libmathdx` | HIPRTC + 可用的设备端算法实现 | 运行时编译路径需重做；HIPRTC 本身不提供 MathDx 算法或兼容 LTO ABI |
| `MathDx/nvCOMPDx` | 评估 hipCOMP 算法复用及设备端 HIP 实现 | hipCOMP 的 host 接口不代表具有设备端等价 API；LZ4、ANS、NVRTC 分开管理 |
| `NPP` | RPP（HIP 后端）；必要时 HIP + rocPRIM | 对每个图像算子确认 API 与边界语义；连通域、距离变换、watershed 等不能按整库对应推断支持 |
| `NPP+` | RPP（HIP 后端）+ HIP + rocPRIM | 另核对 C++ 封装和 Python 示例；与 NPP 相似的样例也分别登记 |
| `nvJPEG` | 解码优先 rocJPEG；resize/watermark 评估 RPP/HIP | 编码另行选型；rocJPEG 当前公开定位为 JPEG 解码，不能覆盖 encoder 样例 |
| `nvJPEG2000` | 尚未确定完整 AMD GPU 编解码库；专项调研 | JPEG2000 不是 JPEG；tile/partial/pipeline 和编码分别评估，CPU codec 只能作参考或标明降级 |
| `nvTIFF` | 尚未确定完整 AMD GPU 对应库；容器解析 + GPU codec/图像处理拆分评估 | TIFF/GeoTIFF、多页、ROI、编码选项都需保留；CPU TIFF I/O 不等于 GPU 编解码迁移 |
| `nvCOMP` | hipCOMP；必要时 HIP + rocPRIM | 按 codec、压缩/解压方向、低/高层 API 分别核验；当前预览版本不能假定覆盖本仓库所有 nvCOMP 功能 |
| `nvMatmulHeuristics` | hipBLASLt heuristics/tuning；进一步评估 AMD 算法选择组件 | 数学乘法可对应；运行时间/能耗预测、配置导出、smem carveout 不保证对应 |

选择依据与边界来自以下官方材料；表中的组合方案是本项目设计推断，并非这些库承诺的完整替代关系：

- [hipBLASLt](https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/)、[hipSPARSELt](https://rocm.docs.amd.com/projects/hipSPARSELt/en/latest/)、[hipTensor](https://rocm.docs.amd.com/projects/hipTensor/en/latest/)：对应 GEMM、结构化稀疏矩阵运算和张量原语的评估入口。
- [rocSOLVER sparse refactorization](https://rocm.docs.amd.com/projects/rocSOLVER/en/latest/reference/refact.html)：提供共享稀疏模式的再分解/求解功能；据此只能确定特定子集路线。
- [rocFFT distributed transforms](https://rocm.docs.amd.com/projects/rocFFT/en/latest/how-to/distributed-transforms.html)：已有单进程多设备和 MPI 支持；MPI 需相应构建选项与 GPU-aware MPI。结合 [hipFFT API](https://rocm.docs.amd.com/projects/hipFFT/en/latest/reference/hipfft-api-usage.html) 逐样例选择兼容层或原生层。
- [RCCL](https://rocm.docs.amd.com/projects/rccl/en/latest/) 提供集合通信；[rocWMMA](https://rocm.docs.amd.com/projects/rocWMMA/en/latest/) 提供矩阵乘累加构件；二者都不能单独证明上表的完整组合方案已成立。
- [RPP](https://rocm.docs.amd.com/projects/rpp/en/latest/index.html) 提供图像处理能力，但须选择 HIP 后端并逐算子确认；[rocJPEG](https://rocm.docs.amd.com/projects/rocJPEG/en/latest/) 的公开接口定位为 JPEG 解码。
- [hipCOMP-core](https://github.com/ROCm/hipCOMP-core/) 当前 README 标为早期预览：列出 LZ4、Snappy、Cascaded、RLE；ZSTD、Deflate/GZIP 为实验性仅解压；Bitcomp、ANS、GDeflate 未支持。其已测试环境列表不构成本项目 ROCm 10.1.0 验证，需要固定源码 commit 后实测。

上述链接的 `latest`/`develop` 会变化。每次确定选型须把实际采用的版本、文档日期或源码 commit 写入项目清单，不能用未来页面内容覆盖历史实验结论。

## 5. 样例级盘点与迁移方式

### 5.1 唯一样例清单

已创建 `migration/samples.yaml`，作为全项目状态的唯一数据源。当前扫描覆盖 866 个源文件及 477 个构建文件，得到 629 个入口候选；仍须人工审计构建图和辅助文件，不能将候选数当成最终样例总数。扫描不到或不满足本机架构条件的目标也必须登记，不允许仅统计本机成功构建出的目标。

每个样例 ID 采用 `原路径::原构建目标或脚本`。多文件链接成一个可执行程序算一个目标；同一个源码的静态/动态链接等构建变体作为该目标下的独立 profile；若教学语义不同再拆分。数据类型、shape、GPU 数、精度模式是测试 case，不重复增加源样例分母。

例如 `cuRAND/Host/philox` 下四个分布程序分别登记；`cuSOLVER/csrqr` 下多个程序不能只留一个目录级成功记录。辅助源码、benchmark、Python 测试分别分类，是否纳入迁移分母及理由写入清单，不能为了提高完成率隐藏困难样例。

清单至少记录：

| 字段组 | 必须记录的内容 |
| --- | --- |
| 身份 | sample ID、family、原路径、target/entrypoint、上游 commit、原源码 hash、源语言 |
| 语义 | 原样例目的、CUDA API、数据类型、layout、index width、batch、设备数、关键特性 |
| 选型 | 候选库、最终直接调用库、后端库、依赖版本、实现文件、选型理由、替代方案未采用原因 |
| 等价性 | `API_PORT` / `LIBRARY_REWRITE` / `HYBRID_HIP` / `DEGRADED`，保留能力、缺失能力、CPU 工作范围 |
| 进度 | 下节状态、代码完成级别、required cases、通过 case 数、阻塞/失败原因 |
| 环境 | AMD/CUDA 各自环境锁、GPU 型号/UUID、架构、驱动、编译器、实际加载库 |
| 验证 | 输入 fixture/hash、参考实现、容差、编译/运行/正确性结果、CUDA 对比状态、证据目录 |
| 性能 | 单独的 benchmark 状态、计时范围、重复次数、统计值、每设备结果 |
| 追踪 | run ID、时间、代码 commit/patch hash、历史 attempt、下一步 |

每次运行生成不可覆盖的独立 run 记录，README 从清单选择当前有效结果生成。不能用一次较早的成功掩盖当前 commit 在目标环境的失败。

### 5.2 代码布局

建议保留全部现有 CUDA 路径，在仓库内增加镜像 ROCm 源码树：

```text
CUDALibrarySamples_ROCm/
├── cuBLAS/ ...                    # 原始 CUDA 样例继续作为对照
├── MathDx/ ...
├── rocm/
│   ├── CMakeLists.txt             # 新 ROCm 入口，不依赖 CUDA Toolkit
│   ├── common/                   # 错误检查、计时、fixture I/O、验证工具
│   ├── cuBLAS/Level-3/gemm/
│   └── ...                       # 对齐原样例相对路径
├── migration/
│   ├── samples.yaml
│   ├── environments/             # ROCm/CUDA 环境锁和 qualification
│   └── reports/                  # 可提交的小型结论、逐例失败说明
├── tools/migration/              # 盘点、运行、比较、生成 README；待实现
├── tests/fixtures/               # 小型输入及元数据；大数据只存索引/hash
├── artifacts/<run-id>/           # 原始日志/输出/指标，通常忽略大文件
└── README.md
```

公共代码只处理 HIP runtime、fixture、计时和检查；各样例显式调用选定库，使读者看得出 cuBLAS 如何变成 hipBLAS/rocBLAS。避免用宏把全部库 API 隐藏起来。

HIPIFY 可以生成初稿。随后必须审查函数签名、枚举、复数类型、workspace 单位、指针模式、stream、同步、溢出和错误处理；自动转换工具的成功退出不是迁移成功。CUDA 原始文件如需适配 Toolkit，只在独立 patch 中保存，并记录 baseline commit + patch hash。

ROCm 构建要求：CMake 的 CXX/HIP 目标与 CUDA 目标分离；根据实际安装路径发现库，不硬编码 `/opt/rocm`；按 GPU 架构设置编译目标；所有可选 SDK 逐项探测。C++ host-only 调用与 HIP kernel 分别设置语言；Fortran 使用经过验证的 C ABI/ISO_C_BINDING 或 hipFORT 路线，CUDA Fortran `.cuf` 需要专门改写。

构建缓存按平台、GPU 架构、编译器、库锁划分。一个可选依赖缺失应报告对应样例的阻塞，不让全仓库基础样例无法构建。新增 root preset、runner 和 CTest 后再把真实命令写进使用说明。

## 6. 完成程度与成功/失败判定

### 6.1 状态

| 状态 | 中文含义与入场条件 |
| --- | --- |
| `NOT_STARTED` | 尚未移植；只有候选路线不代表实现 |
| `IN_PROGRESS` | 已开始实现/验证，但 required cases 尚未完整通过 |
| `BLOCKED` | 环境、SDK、GPU、输入或访问等前置条件欠缺；必须写明恢复条件 |
| `PARTIAL` | 已有经过验证的可用子集，但原样例关键特性、类型或 required cases 尚未覆盖 |
| `PASSED` | 在记录的 AMD 环境完成构建、GPU 执行和全部预先定义的必需功能/正确性验证；无未声明降级 |
| `FAILED` | 已实际尝试，某阶段失败；保留命令、日志、输入及根因/待定位假设 |
| `UNSUPPORTED` | 有锁定版本的文档/源码或最小复现证据证明必要能力缺失；仅限所记录版本/硬件/路线 |

另设代码级别：`L0` 未实现、`L1` 有源码、`L2` 编译通过、`L3` AMD 运行通过、`L4` 必需正确性用例全部通过；性能另列，不作为正确性完成度。L3 不能自动进入 `PASSED`。

`cuda_baseline`、`cuda_comparison`、`benchmark` 使用独立的 `NOT_RUN/PASSED/FAILED/BLOCKED` 状态。CUDA SDK 不可用时，AMD 可在独立 CPU/数学参考验证充分的情况下记为 `PASSED`，但必须显示“CUDA 对比待完成”；双端对照里程碑仍未完成。不存在跨 GPU 对照时不填写速度比。

`DEGRADED` 实现即使较小范围数值通过，也只能作为原样例的 `PARTIAL` 或独立派生样例。例如：

- 多 GPU 改成单 GPU；device fusion 改成多个 host 调用。
- FP64/FP8 改成 FP32；64-bit 索引缩成 32-bit。
- sparse direct solver 改成迭代法或把稀疏矩阵转 dense。
- 以 CPU codec 代替 GPU codec；以稠密 GEMM 代替结构化稀疏执行。

### 6.2 README 展示约定

根 README 展示 30 个库级子项目的汇总，每个库级 README 列出所有子样例及详细状态，逐例 ROCm README 给出实际构建命令、所选库、验证、缺口与证据。暂时没有实现的目录也显示 `NOT_STARTED`。

固定列为：`CUDA 样例 | 实际使用库/后端 | 完成级别 | 状态 | 已覆盖/缺失功能 | CUDA 对照 | 成功说明或失败原因 | 证据`。未开始时“实际使用库”为空，单独列候选库，不把规划写成事实。

成功写法模板（**非本次实测结果**）：

> 使用 hipBLAS（rocBLAS 后端）成功实现 GEMM；在指定 ROCm 10.1.0 / GPU 环境中通过 FP32、转置、leading dimension 等所列 required cases；CUDA 对照状态及日志见证据链接。

失败写法模板（**非本次实测结果**）：

> 使用库 A 的版本 V 尝试实现特性 F，在指定 GPU 的 plan 创建阶段返回错误 E。最小复现与 API 支持依据见链接；替代路线 B 因缺少特性 G 尚未采用。当前标记为 FAILED/UNSUPPORTED，而不是已完成。

每个汇总至少展示 `total / passed / partial / failed / blocked / unsupported / not_started / in_progress`，保证总数相等。**完成率 = PASSED / 纳入范围的样例总数**；困难样例仍在分母，部分完成不折算为成功。尚未确定样例总数时显示“待盘点”，不用 866 源文件伪造分母。

### 6.3 失败归因

| reason_code | 必须解释的内容 |
| --- | --- |
| `ENV_MISSING_DEP` | 哪个 SDK、头文件、库或构建选项缺失，补齐办法 |
| `HW_UNSUPPORTED` | 哪个实际架构/精度/媒体引擎/P2P 能力不满足；不要泛化成所有 AMD GPU 不支持 |
| `API_GAP` | 缺失的确切 API/参数组合及版本证据；替代接口能否保留语义 |
| `SEMANTIC_GAP` | 已可运行但少了哪些原样例特性，例如融合、64-bit 或布局 |
| `BUILD_ERROR` / `LINK_ERROR` | 最小命令、首个有效错误、头文件/链接库版本 |
| `RUNTIME_ERROR` / `TIMEOUT` | 返回码、运行输入、设备、同步点、复现频率 |
| `NUMERICAL_MISMATCH` | 参考输出、误差指标、容差、首个失败 case、是否存在 NaN/Inf |
| `BASELINE_UNAVAILABLE` | CUDA 基线依赖或硬件限制；与 ROCm 自身失败区分 |
| `PERF_REGRESSION` | 正确性已通过但性能目标未达；作为性能结果记录，不抹去功能成功 |

`NOT_IMPLEMENTED` 等错误需查明是否因本地安装、参数、架构或真正 API 缺口导致。查不到对应函数的搜索结果只能标为待调研，不能作为“不支持”的充分证据。

## 7. 正确性与 CUDA 对照设计

### 7.1 输入及参考结果

每例至少保留原始小样例，再加入能暴露迁移问题的边界 case。由公共 host 工具一次生成输入并保存二进制数据、shape、dtype、stride、layout、seed、字节序和 SHA-256，传给 CUDA 与 ROCm 两端。不得只给两端相同 seed 后各自产生矩阵并假设输入相同。

验证采用三方：CUDA 原实现、ROCm 实现、独立参考。小规模参考用明确的 CPU 算法或经固定版本的 BLAS/LAPACK/FFT 实现；大规模辅以残差、不变量和抽样。两端比较通过不能排除共有错误，不能只看程序打印了 `PASS` 或返回 0。

### 7.2 按问题类型验收

| 类别 | 必需的验证方式 |
| --- | --- |
| BLAS / GEMM / Tensor | 对齐数学表达式、alpha/beta、transpose/conjugate、行列主序、leading dimension、stride、batch；覆盖零/非零 beta、非整齐尺寸，按 API 合法范围测试 |
| Sparse | 验证 index base、32/64-bit、格式、空行、重复索引的约定及排序；结果允许合法的不同存储排序，比较前规范化，但不隐藏缺失项 |
| Solver | 检查 info/status，使用 `||AX-B||/(||A||·||X||+||B||)` 等残差；分解做重构，特征/SVD 验证重构与正交性；允许符号、相位及退化子空间的非唯一性 |
| FFT | 比较正/逆变换、归一化、Hermitian 布局、in-place padding、stride/batch；验证 round-trip 与独立参考，检查分布式输出的全局布局 |
| RNG | 相同算法也不先验要求跨库序列逐位相同；根据原样例目的分别验证可复现性、状态/offset、分布范围与统计性质。若目标本身要求序列等价，必须另设精确验证 |
| 图像/媒体 | 对齐 ROI、pitch、通道顺序、颜色空间、插值、边界策略和 rounding；无损输出逐字节比较，有损/不同 JPEG IDCT 路线用预设像素误差或质量指标 |
| Compression | 无损 round-trip 精确相等；只有承诺兼容的码流才做跨端压缩/解压互操作；压缩率不同不一定失败，codec/容器不兼容不能忽略 |
| PQC / Hash | 使用已确认来源的算法测试向量和 byte-exact 检查；随机参数固定于测试层。功能样例通过不等于生产密码学安全审计通过 |
| 多 GPU/MPI | 检查各 rank 的状态与全局结果、数据分布、通信语义；单节点双卡不能证明多节点功能；任一 rank 失败应协调退出，避免其他 rank 挂起 |

浮点基础比较采用 `abs(actual-ref) <= atol + rtol * abs(ref)`，并报告最大绝对误差、相对范数误差及异常值。小型、条件良好的 FP32 case 可从 `atol=1e-6, rtol=1e-5` 起步，FP64 从 `1e-12, 1e-10` 起步；这只是制定验收集的初始建议，不是所有算法通用阈值。长度、累加精度、条件数、FFT 规模和低精度量化决定最终门限，须在运行前固定于 case 配置。失败后不能单纯放宽阈值到通过。

FP16/BF16/FP8/NVFP4/MXFP8 分别写明输入、累加及输出精度、scale 和饱和规则；禁止静默退回高精度再标低精度成功。RNG 采用固定测试集合和预先定义的统计标准，保留多重检验的误报处理约定，不因一次随机波动直接判断实现错误。

### 7.3 性能对照

性能是正确性通过后的独立输出。原样例的微小矩阵通常只能用于 smoke test；性能 profile 另设，保留与原样例的语义关系。

- 双端使用相同输入、shape、精度/累加模式、batch、workspace 上限、stream 数和算法要求；分别报告严格 FP32 与允许降精度的模式。
- 建议起点为 10 次预热、至少 100 次计时，分 3 组独立重复；短算子批量计时，长算子按固定最短计时窗口调整，记录实际次数。
- 分别报告 plan/初始化、纯 GPU 计算、端到端（明确是否包括 H2D/D2H、布局转换、压缩、通信和分配）。算法搜索成本与稳态执行分开。
- 单 GPU 用 CUDA/HIP event；提交与异步错误在明确同步点检查。多 GPU/MPI 使用所有参与者完成的 wall time，以最慢 rank 为全局完成时间，不能只计其中一张卡。
- 报告中位数、p95、重复组波动、吞吐和适用的 FLOP/s/GB/s；记录功耗/温度/频率或是否未采集。后台干扰显著的结果不纳入结论。
- `CUDA/ROCm latency ratio = CUDA 时间 / ROCm 时间`，只用于该硬件组合下的观察。R9700 与 RTX 5090 是不同硬件，不能据此声称是迁移代码或库单独带来的加速。
- 单卡 5090 对单卡 AMD；双卡对双卡作为另一组。记录 PCIe/P2P、NUMA、MPI/RCCL 路径；两卡跑同一个任务的两份副本不算分布式样例成功。

## 8. 分批实施与明确验收门槛

### M0：清单与运行基础（基础已建立，构建图审计待完成）

产出完整样例清单、30 类库级 README、AMD/CUDA 环境锁、项目专用依赖资格检查、fixture/结果格式、独立构建入口、日志归档及 README 生成工具。所有现有目标均归档为未开始或有依据的阻塞，不能漏掉 Makefile、Fortran、Python、条件编译目标。

先做最小库探针：链接、创建 handle/plan、执行小规模数学运算、同步并核对结果。分别记录“库安装存在”“实际 GPU 可执行”“所需特性支持”，三者不合并。本次在 M0 基础工具建立后，以 M1 的 16 个试点验证完整运行流程；全量静态构建图审计现已完成，条件配置未全部生成执行的边界见第 12 节。

### M1：首批 16 个具体目标，建立完整验证闭环（16/16 原始行为与 95 cases 已验收）

以下均是仓库中存在的路径；最终 sample ID 由 M0 解析真实 target 后确定。

| 顺序 | 原样例路径/程序 | 首选路线 | 首批验证重点 |
| --- | --- | --- | --- |
| 1 | `cuBLAS/Level-1/axpy` | hipBLAS → rocBLAS | 数据搬运、stride、alpha |
| 2 | `cuBLAS/Level-1/dot` | hipBLAS → rocBLAS | 标量返回及 pointer mode |
| 3 | `cuBLAS/Level-2/gemv` | hipBLAS → rocBLAS | layout、transpose、leading dimension |
| 4 | `cuBLAS/Level-3/gemm` | hipBLAS → rocBLAS | 按原源码使用 FP64 GEMM，验证 alpha/beta、非整齐尺寸；FP32 后续另列 |
| 5 | `cuBLAS/Level-3/gemmStridedBatched` | hipBLAS → rocBLAS | batch stride 与边界 |
| 6 | `cuBLAS/Extensions/GemmEx` | hipBLAS/rocBLAS | 显式混合精度与支持参数组合 |
| 7 | `cuBLASLt/LtSgemm` | hipBLASLt | descriptor、heuristics、workspace |
| 8 | `cuSPARSE/spmv_csr` | hipSPARSE → rocSPARSE | CSR 索引、空行、alpha/beta |
| 9 | `cuSPARSE/spmm_csr` | hipSPARSE → rocSPARSE | sparse/dense 布局 |
| 10 | `cuSPARSE/spsv_csr` | hipSPARSE/rocSPARSE | analysis/solve、三角矩阵残差 |
| 11 | `cuSOLVER/getrf` | hipSOLVER/rocSOLVER | pivot、info、求解残差 |
| 12 | `cuSOLVER/potrfBatched` | hipSOLVER/rocSOLVER | SPD 输入、每 batch 状态 |
| 13 | `cuFFT/1d_c2c` | hipFFT → rocFFT | 正逆变换与归一化 |
| 14 | `cuFFT/1d_r2c_c2r` | hipFFT → rocFFT | Hermitian 存储、padding |
| 15 | `cuRAND/Host/philox/curand_philox_uniform_example.cpp` | hipRAND → rocRAND | uniform、seed/offset、统计 |
| 16 | `cuRAND/Host/philox/curand_philox_normal_example.cpp` | hipRAND → rocRAND | normal 分布与可复现性 |

M1 每例必须有最终库选型、可执行源码、构建/运行指令、AMD 正确性证据及 CUDA 对照结果，或明确列出的阻塞/失败报告。成功数量以实际验收为准，不预先承诺 16/16。随后从成功样例中选择适合的规模做性能对照。

### M2：基础单卡库全覆盖

扩展 cuBLAS 常规 Level 1/2/3、可用 Extensions、cuSPARSE CSR/COO 与转换、cuSOLVER 常规稠密、cuFFT 单卡及 cuRAND 的所有 generator/distribution。逐项处理：复数共轭、64-bit、Jacobi/近似算法、SpGEMM reuse、custom operators、graph capture、callback。

扩展成功指全部已登记并有结果，而非要求所有功能都成功。对明确缺口形成 `UNSUPPORTED`/`PARTIAL` 报告，并保留可重试条件。

### M3：张量、结构化稀疏、媒体与压缩

在实际 GPU 支持探针之后推进 hipTensor、hipSPARSELt、hipCOMP、RPP、rocJPEG。优先从存在完整 AMD 路线的具体算子/codec 开始。JPEG 编码、JPEG2000、TIFF 和 NPP 特殊算子单独调查，不把一个 decode 或 resize 的成功扩展成整库完成。

### M4：多 GPU/多进程

先验证一机两卡通信与分布式输入/输出，再推进 cuFFT 多卡、cuFFTMp、cuBLASMp、cuTENSORMg/Mp，最后处理分布式求解。每例明确是单进程多卡、单机多进程还是多节点。双 5090 与 AMD 双卡分别验证拓扑/P2P；多节点没有硬件时保留 `BLOCKED`。

### M5：设备端、特殊 SDK 与能力缺口

MathDx 六个子库、cuDSS 高级功能、cuEST、cuPQC、nvMatmulHeuristics 专项推进。可以先做小型可行性探针避免晚发现关键缺口，再决定完整实现。只有证明保留原目标的融合、分布或算法特性后才能将整个样例标为成功。

每批结束更新清单、逐例 README、库级 README 与根 README；同步提交源码、验证脚本及小型证据索引，不等到全仓库结束才补报告。耗时按 M1 实际吞吐估算后再排期，不以源文件数直接推断总工时。

## 9. 后续实验入口与证据结构

现有环境入口可按如下方式使用；下面只做资格查询，不代表本次已执行 AMD 实验：

```bash
cd /home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm
# 先确认物理 GPU0 空闲；项目资格检查还需单独完成。
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh bash
```

在新容器中把新增的 compiler/JIT cache 指向本项目目录，按 image ID、实际架构和编译器分隔；不修改共享 foundation，不复用其他项目的可变构建目录。需要补库时使用项目 overlay 并单独锁定；编译路径应由 SDK 探测得到。

已实测可用的 CUDA 查询入口：

```bash
ssh -o BatchMode=yes nvidia-5090x2 \
  'nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv,noheader'
ssh -o BatchMode=yes nvidia-5090x2 '/usr/local/cuda-13.4/bin/nvcc --version'
```

后续在该机器创建本项目独立 checkout/worktree 和 build 目录，固定相同 CUDA 原始 commit。通过显式 `CUDAToolkit_ROOT`/编译器路径避免 PATH 差异；架构选项由设备与 nvcc 支持能力确认。独立 CUDA SDK 的版本与二进制 hash 一并锁定。只同步本项目源码、fixture 和结果，实验 runner 明确设备数、设备选择与超时。

每次运行建议保存：

```text
artifacts/<run-id>/<sample-id>/<backend>/<case-id>/
  environment.json       # 硬件、镜像、编译器、库、代码身份
  commands.txt           # cwd、完整命令、必要环境变量
  build.log
  run.log
  inputs.json            # fixture 路径/hash/规格
  output.bin             # 需要完整比较时保留；大输出用外部制品存储
  correctness.json       # 指标、门限、case 结论、参考身份
  benchmark.json         # 未测时省略，不能填 0 假装结果
  summary.json
```

证据必须绑定代码 commit/未提交 patch hash、上游快照、实际加载库及输入 hash。大日志/输出可放持久制品存储，仓库保留可访问 URI、hash 和简短报告；不能只有本机临时 `/tmp` 路径。失败日志与成功日志同样保留。

## 10. 设计阶段交付检查

- 已覆盖 25 个顶层样例目录，MathDx 展开后为 30 个库级子项目。
- 根 README 明确展示本项目的 ROCm 迁移目标、候选库、尚未实现状态及后续成功/失败报告规范。
- 已区分方案、现有文件、只读环境查询与真实实验，未编造成功、失败或性能数字。
- 已规定逐样例清单、功能完成级别、失败归因、双端对照、独立参考及复现证据。
- 后续首个实施步骤为 M0，然后以 M1 的 16 个真实目标建立完整闭环。

## 11. 实时实施日志

本节在每个实施步骤结束后更新，成功结论以归档证据为准。设计阶段的“未开始”描述是初始快照，当前状态以本节及仓库内清单为准。

| 步骤 | 状态 | 实际结果与证据 | 下一步 |
| --- | --- | --- | --- |
| S01 启动与环境复核 | 已完成依赖检查 | foundation verifier 通过；首批 11 个直接/后端库均存在且可加载，架构为 R9700/gfx1201。hipTensor、rocJPEG 在当前 SDK 库目录未发现，不能推断所有环境不支持。证据：`migration/environments/amd-rocm10-inspection.json` | 编译并验证首批库功能 |
| S02 全源文件盘点 | 已完成自动扫描，构建图审计待完成 | `tools/migration/catalog.py` 基于固定上游 commit 扫描 866 个源文件及 477 个构建文件，发现 629 个入口候选；逐文件 hash、分类、库候选和状态已写入 `migration/samples.yaml`（JSON 格式的合法 YAML 1.2） | 逐目标核实映射，629 尚不是最终样例总数 |
| S03 首批源码与验证基础 | 已实现，正在编译运行 | 已新增 16 个显式调用 AMD 库的验证程序、共享 binary fixture、独立 CPU 参考计算、必需 case 集合及逐程序构建/运行日志工具。覆盖非整齐尺寸、transpose、stride/padding、beta、pointer mode、稀疏 index base、求解残差、FFT DFT/round-trip、RNG host/device/offset/重复性与统计 | 在实际 ROCm 环境编译并逐项记录错误；原样例行为尚未全部核对，暂不标全功能成功 |
| S04 首次构建与工具链修正 | 首轮失败已归档，正在修复 | 16 个程序首次构建均被 hipcc 默认设备库查找失败阻断，证据 run `20261109T074106.668062Z`；未归因为库功能不支持。这批程序只有 host 侧库调用，改用同一 ROCm 10.1 SDK 的 amdclang++ 编译 C++ 并显式链接 HIP runtime；库内 GPU 计算仍需实际执行验证 | 重新构建并检查数值结果 |
| S05 SDK 头文件定位与 CUDA 首轮 | 已定位并修复构建配置，复测中 | wheel runtime 目录没有数学库头文件，实际匹配版本头文件位于 `/opt/rocm/core-10.1/include`，现已显式加入。CUDA 首轮大部分扩展程序通过 CPU 参考；修复 FFT inverse 枚举映射和 uplo case 名称的跨平台差异，未修改数学容差 | 重新运行双端验证，收集逐 case 对照 |
| S06 首轮 GPU 数值验证 | 已完成首轮 | 修复 wheel 缺少无版本 `.so` 链接后，16/16 编译成功，AMD 扩展验证 14/16 通过；getrf 和 SpMV 有实际运行错误待定位。CUDA 共享 fixture 的 16/16 扩展验证通过；原始 CUDA 16/16 构建与 smoke 运行通过（原样例返回 0 不单独证明数值正确）。全部保留日志 | 修复两个 AMD 运行问题，做逐 case 双端比较并生成文档 |
| S07 运行差异处理与实时文档生成 | getrf 已修复，SpMV 继续定位 | hipSOLVER 的 getrs 在 no-pivot LU 后仍要求有效 ipiv；传入 identity pivots 保留无主元算法，pivot on/off 和残差均通过。hipSPARSE SpMV 加 preprocess 后默认算法仍返回 status=3，继续检查具体算法路径。已建立根 README、30 个库级逐例表及 16 个实现 README 的自动生成器 | 检查 SpMV 指定算法，验证 CMake/CTest 并核对对照输出 |
| S08 双端输出比较与独立构建入口 | 已完成第一轮 | `migration/reports/m1-comparison.json` 已记录 15 个实现逐 case 对照通过、1 个因 AMD SpMV 失败而阻塞；RNG 对比分布统计，不对比随机序列。独立 CMake 16/16 构建通过，CTest 15/16 通过，唯一失败也是 SpMV。根及全部库级 README 已由清单生成 | 评估 rocSPARSE 原生 SpMV 路线；原始教学 profile、完整构建图审计、性能实验仍未完成 |
| S09 SpMV 根因定位与原生路线验证 | 原生 v2 已通过，兼容层复测中 | `rocSPARSE v2` 在 index base 0/1、beta 0/0.5 的 4 个 case 全部通过。定位到公共 Device 包装对零字节工作区仍分配 1 字节，导致库收到应为空却非空的指针；原生接口报告 invalid_size。现已修正零字节工作区为 nullptr，并重新测试 hipSPARSE；此前失败不构成 API/硬件不支持的证据 | 保留两条实现与历史失败，按语义及维护成本确定默认路线，重跑受公共修复影响的首批用例 |
| S10 首批扩展验证全部通过 | 已完成 GPU 回归 | 修复后 hipSPARSE SpMV 4/4 用例通过；默认选择更接近原 API 的 hipSPARSE，保留 `sample_rocsparse_v2.cpp` 作为已验证替代。首批 16/16 程序、66 个扩展 case 全部通过 AMD 数值验证，run `20261109T075141.556119Z`。进一步为 getrf 补上原始输入的 LU 重构验证，正在双端重测该项 | 完成最后的对照/CTest 和证据归档，继续保留未覆盖行为的 PARTIAL 状态 |
| S11 对照、回归与证据归档 | 已完成 | 首批 16/16、合计 68 个 case 的 AMD/CPU/CUDA 验证与对照通过；原始 CUDA 16/16 smoke 通过。独立 CMake/CTest 16/16 通过，新增 getrf 重构检查后又单独重建复测通过。585 个 JSON/文本证据文件归档到 `migration/reports/evidence/`，保留先前失败。当前整例状态为 1 PASSED、15 PARTIAL、613 NOT_STARTED | 优先完成 M0 构建图审计及其余 15 个原始 profile，对性能尚不作结论 |
| S12 文档、清单和环境身份核对 | 已完成 | 已校验 629 个唯一入口候选、16 个当前实现源码 hash、68 个双端 case、证据路径及新文档链接；Python 工具语法与 Git whitespace 检查通过。环境头文件 hash 已补齐，项目环境锁写入 `migration/environments/project.lock.json`。README 和本文已统一为当前状态 | 下一步按第 12 节顺序继续；M0 全量审计与 M1 剩余原始 profile 尚未完成 |
| S13 全计划持续执行 | 进行中 | 用户要求执行完全部计划前不停止；已建立持续目标与自动实施日志工具，重新核对 GPU 占用并继续使用锁定 ROCm 10.1.0。发现完整 SDK 原生 lib 目录含 rocJPEG、RPP，先前 wheel 子目录未发现不能视为整体缺失。 | 完成构建图审计，同时生成 M2 数学库逐例 HIP 初稿 |
| S14 构建定义与源码分类审计 | 已完成 | 477 个构建定义已提取 766 个声明；所有 866 个源码均关联入口或辅助模块类别，补入 Python 及 NVBench 宏生成入口。56 个变量/条件声明保留原文供后续解析，尚不宣称动态构建图全部展开。数学库 276 个文件 HIPIFY 初稿已落盘。 | 编译原始输入版本，保留每个错误和其替代路线 |
| 批量原始 profile rocm 25/224 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 50/224 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 75/224 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 100/224 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S16 HIP 设备编译资格检查 | 进行中 | 项目 SDK overlay 通过运行自定义 HIP kernel 探针，补齐 wheel 缺少无版本链接的问题，未修改共享镜像。批量构建发现 .cu 在纯 host 编译器下被误判为 CUDA 语言，已给 host 接口程序显式设置 -x c++，保留首轮失败日志。 | 继续批量验证，并补入 FFT 的 GPU scaling 模块 |
| 批量原始 profile rocm 125/224 | 进行中 | 本轮已有 16 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 150/224 | 进行中 | 本轮已有 23 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 175/224 | 进行中 | 本轮已有 23 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 200/224 | 进行中 | 本轮已有 31 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 224 项中 47 项构建运行通过，证据 artifacts/20261109T080822.795958Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| 批量原始 profile rocm 25/141 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 50/141 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 75/141 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 100/141 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 125/141 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 141 项中 0 项构建运行通过，证据 artifacts/20261109T081329.986729Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| 批量原始 profile rocm 25/141 | 进行中 | 本轮已有 6 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 50/141 | 进行中 | 本轮已有 29 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 75/141 | 进行中 | 本轮已有 52 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S17 首批原始行为补齐 | 进行中 | 16 个试点现已加入原始教学输入；Cholesky 增加非正定 info=2 和原始分解重构，SpMV/SpMM 增加空行，FFT 恢复设备端 scaling kernel，RNG 增加 n=12 host/device 重复性。必需 case 从 68 扩展为 95，AMD 数值验证分批通过，正在重做 CUDA 对照。 | 完成 M1 三方复核，同时逐例修复 M2 原始输入移植 |
| 批量原始 profile rocm 100/141 | 进行中 | 本轮已有 59 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 125/141 | 进行中 | 本轮已有 61 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 141 项中 72 项构建运行通过，证据 artifacts/20261109T081449.022777Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| 批量原始 profile rocm 25/62 | 进行中 | 本轮已有 3 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 50/62 | 进行中 | 本轮已有 11 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 62 项中 15 项构建运行通过，证据 artifacts/20261109T081655.531829Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S18 M1 原始 profile 与扩展门槛完成 | 已完成 | 首批 16 个程序共 95 个必需 case 已通过 AMD/独立 CPU/CUDA 对照；包含原始输入、非正定 Cholesky、空行与 GPU 端 FFT scaling。所有 M1 示例达到当前声明范围的 L4，保留先前失败与修复历史。 | 继续完成 M0 变量/构建变体审计及 M2 批量数值验收 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 16 项中 0 项构建运行通过，证据 artifacts/20261109T081730.474917Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S19 实际 GPU 身份校正 | 进行中 | 发现 HIP 编号与 AMD-SMI 物理编号不一致：HIP 0 对应 PCI 63:00.0，即应排除的物理 GPU3；先前按 HIP 0 执行的探针/原始 profile 记录保留但不纳入最终资格结论。改用 HIP 2（PCI 03:00.0，物理 GPU0），并增加执行前 PCI guard。HIP 1 对应物理 GPU2，首批原有验证在该允许设备上完成。 | 重跑受影响的原始 profile；所有后续 GPU 结论绑定 PCI 地址 |
| 批量原始 profile rocm 25/224 | 进行中 | 本轮已有 8 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 50/224 | 进行中 | 本轮已有 31 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 75/224 | 进行中 | 本轮已有 55 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 100/224 | 进行中 | 本轮已有 62 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 16 项中 16 项构建运行通过，证据 artifacts/20261109T082146.087295Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S20 原始输出观测与生命周期修正 | 进行中 | 为 BLAS 原始输入版本加入不改变计算的完整精度输出观测，以便独立 CPU 参考逐项检查；发现上游不同 RNG 示例的 generator 生命周期不一致，逐函数补齐销毁并避免 ROCm 缓存在 hipDeviceReset 后清理。后续批次固定编译前源码 hash，拒绝编译中变更。 | 在允许 GPU 上重跑，完成逐例原始数值门槛并推进媒体/压缩库探针 |
| 批量原始 profile rocm 125/224 | 进行中 | 本轮已有 70 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 150/224 | 进行中 | 本轮已有 73 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 175/224 | 进行中 | 本轮已有 82 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 200/224 | 进行中 | 本轮已有 104 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 224 项中 122 项构建运行通过，证据 artifacts/20261109T081929.210831Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| 批量原始 profile rocm 25/82 | 进行中 | 本轮已有 8 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S21 扩展生态依赖实查与构建 | 进行中 | 完整 SDK 实查确认 RPP、rocJPEG、hipSPARSELt、RCCL、HIPRTC 可加载；hipTensor 与 hipCOMP 需项目级构建。已固定 hipCOMP-core 源码 commit 03df9f7369211ee15d370817165224c73fdc9a46，并在 ROCm 10.1.0/gfx1201 下编译；hipTensor 最新官方源码明确新增 gfx1201 支持，正在本项目独立构建，不再依据旧版支持表判断。 | 验证压缩 round-trip、张量能力和媒体解码，逐例记录真实支持边界 |
| 批量原始 profile rocm 50/82 | 进行中 | 本轮已有 31 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 75/82 | 进行中 | 本轮已有 55 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 82 项中 62 项构建运行通过，证据 artifacts/20261109T082832.792069Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S22 全范围转换初稿扩展 | 进行中 | 已开始为 M3–M5 所有 C/C++/设备端入口保留逐例转换初稿与实际编译证据；最终成功仍要求原始语义验证。hipTensor 官方当前源码支持 gfx1201，hipCOMP-core 已进入链接阶段。M1 95 个用例已再次在允许设备完成 AMD 验证，原始 BLAS CPU 数学参考与无损输出观测已建立。 | 完成全部子项目能力探针、编译及替代路线评估 |
| S23 M3–M5 逐入口编译与能力路线 | 进行中 | 所有非首批 C/C++ 库级子项目进入逐入口构建探查，保留原始代码、候选库、具体 API/头文件缺口及编译证据；同时为有现成 AMD API 的媒体、结构化稀疏、张量和压缩功能实现原生验证程序。hipCOMP 已在 gfx1201 编译通过，hipTensor 配置成功并持续构建。 | 把转换草稿失败与原生替代验证分别记录，不将缺少 NVIDIA 头文件直接等同于 AMD 不支持 |
| 批量原始 profile rocm 25/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 50/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 75/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 100/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 125/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 150/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 175/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 200/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 225/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 250/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 275/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 300/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 325/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 339 项中 0 项构建运行通过，证据 artifacts/20261109T083217.050455Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S24 | 已完成 | hipCOMP LZ4 在 128/32768/65536 字节 GPU 往返逐字节一致；RPP 的 U8 单通道/三通道 identity resize 通过；rocJPEG 已真实硬件解码仓库 baseline JPEG（独立像素对照另存）。各探针不能替代整库迁移验收。证据 migration/reports/native-probes.json | 继续媒体像素对照、双卡与各原始 profile 验收 |
| S25 | 已完成 | 双卡物理 GPU0/1 上 hipBLAS 分块 GEMM + RCCL AllGather 通过，两张卡分别核对完整结果；rocJPEG 64×64 baseline RGB 对 Pillow/libjpeg 最大误差 2、均值 0.0452。共享预约变为 GPU2/6，guard 已拒绝该卡上的后续任务，后续只选 GPU0/1。 | 推进原始多卡 profile 与 Fortran/Python、张量和压缩 API 适配 |
| 批量原始 profile rocm 25/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 50/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 75/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 100/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 125/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 150/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 175/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 200/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 225/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 250/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S26 Fortran/Python 入口实际资格与改写尝试 | 已完成 | 76 个非 C++ 入口均保留独立命令/编译或 import 错误；Fortran ISO_C_BINDING 到 HIP GPU 内存往返返回码 0。未将 CPU 路线记为成功。 | 继续逐功能后端验证与差异说明 |
| 批量原始 profile rocm 275/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 300/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 325/339 | 进行中 | 本轮已有 0 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 339 项中 0 项构建运行通过，证据 artifacts/20261109T084256.329631Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| 批量原始 profile rocm 25/36 | 进行中 | 本轮已有 22 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 36 项中 33 项构建运行通过，证据 artifacts/20261109T084257.296664Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| 批量原始 profile rocm 25/106 | 进行中 | 本轮已有 4 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 50/106 | 进行中 | 本轮已有 10 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 75/106 | 进行中 | 本轮已有 29 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| 批量原始 profile rocm 100/106 | 进行中 | 本轮已有 48 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 106 项中 53 项构建运行通过，证据 artifacts/20261109T084753.304309Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S27 RNG 原始 profile 解析分布验收 | 已完成 | 32 项中 12 通过；MT19937 的实际初始化超时另记失败，未跳换 generator。 | 处理数值差异与 CUDA 统计对照 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 1 项中 1 项构建运行通过，证据 artifacts/20261109T085046.961770Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S27 RNG 原始 profile 解析分布验收 | 已完成 | 32 项中 32 通过；MT19937 的实际初始化超时另记失败，未跳换 generator。 | 处理数值差异与 CUDA 统计对照 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 20 项中 0 项构建运行通过，证据 artifacts/20261109T085205.912828Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S28 | 已完成 | 639 个独立源入口（563 C/C++、76 Fortran/Python）均已有实际转换/编译或绑定尝试及逐例日志；477 个构建定义与 866 个源文件完成静态审计，659 个源文件绑定构建声明。52 个动态表达式均归因为外部 SDK 源、测试生成输入、可选链接路径或已有入口的通信变体，不隐去这些条件。 | 保留失败状态并继续替代库改写、独立验证和性能稳定性检查 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 4 项中 0 项构建运行通过，证据 artifacts/20261109T085413.622888Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S29 | 已完成 | rocSOLVER CSRRF 的真实稀疏 Cholesky 路线已通过 cuDSS simple 同一 5×5 SPD 矩阵的解与 CSR 残差检查，并完成同结构数值 refactor；没有稀疏转 dense。当前实现显式提供该小矩阵的符号 L 模式，不能扩展宣称 cuDSS 自动符号分析/高级模式已完成。 | 绑定原始样例与严格容差，继续高级能力与媒体/张量验证 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 10 项中 6 项构建运行通过，证据 artifacts/20261109T085509.301265Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 20 项中 3 项构建运行通过，证据 artifacts/20261109T085546.110648Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 1 项中 0 项构建运行通过，证据 artifacts/20261109T085730.270757Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 1 项中 1 项构建运行通过，证据 artifacts/20261109T085759.859059Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| 批量原始 profile rocm 25/39 | 进行中 | 本轮已有 7 项运行通过；其余保留具体编译/运行错误。运行通过尚不等于完成正确性验收。 | 继续处理剩余样例 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 39 项中 19 项构建运行通过，证据 artifacts/20261109T085841.111146Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 20 项中 3 项构建运行通过，证据 artifacts/20261109T090201.483404Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S30 | 已完成 | M1 最终 CMake/CTest 16/16 通过，95 个数值用例及 GPU FFT scaling 复核完成；额外 8 个求解器原始矩阵通过 NumPy/SciPy 奇异值/特征值、重构、残差及正交性检查。双卡 3D FFT 相对单卡 L2 误差分别 1.98e-7/3.12e-7；legacy device callback 对独立 reference pipeline L2=0。 | 继续 FFT 独立 CPU 对照、性能稳定性及专项 SDK 最终验收 |
| S27 RNG 原始 profile 解析分布验收 | 已完成 | 4 项中 4 通过；初始化超时及本轮结果均保留，未跳换 generator。 | 处理数值差异与 CUDA 统计对照 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 10 项中 7 项构建运行通过，证据 artifacts/20261109T090451.232153Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 11 项中 4 项构建运行通过，证据 artifacts/20261109T091118.060291Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 2 项中 0 项构建运行通过，证据 artifacts/20261109T091606.225939Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 2 项中 2 项构建运行通过，证据 artifacts/20261109T091608.933062Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 2 项中 0 项构建运行通过，证据 artifacts/20261109T091904.671567Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S31 | 已完成 | 36/36 RNG generator/distribution 已完成 AMD 与 CUDA 的原始 n、seed/offset 重复性及 98304 点解析分布检查；两种 stream association 下双卡 3D FFT 与独立 CPU 全量对照通过。标准 Fortran 与 CUDA Fortran simple 已经 ISO_C_BINDING/C ABI 连接真正的 GPU CSRRF 稀疏求解通过，符号分析为通用 CPU 稀疏图消元。 | 补 JIT SPIR-V callback、最终逐例库选型/失败重试说明、归档和一致性审核 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 2 项中 0 项构建运行通过，证据 artifacts/20261109T092720.531889Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 1 项中 1 项构建运行通过，证据 artifacts/20261109T092937.851298Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 1 项中 1 项构建运行通过，证据 artifacts/20261109T093236.589333Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S32 | 已完成 | SPIR-V AOT callback 与 HIPRTC 运行时 SPIR-V callback 均已保留 FFT device JIT 融合，830×328 全量输出经独立 CPU FFT/filter/inverse 验证（相对 L2≈2.75e-7）；2D in-place FFT 已修复 padded stride 显示及异步同步，全部数值通过。hipSPARSELt 两例成功编译但实机缺 gfx1201 kernels，锁定上游构建支持列表也排除该架构，按库/版本/硬件限定记录缺口。 | 同步完整 CUDA 对照、封存环境/源码/证据，生成最终逐例报告与计划结果 |
| S15 rocm 原始 profile 批次完成 | 已完成 | 1 项中 1 项构建运行通过，证据 artifacts/20261109T094106.862809Z/original-rocm；失败原因逐例入清单，尚待独立数值检查 | 修复共同问题并完成原始行为验收 |
| S33 M3–M5 补充验收 | 已完成 | Fortran ISO_C_BINDING 与 C++ simple 稀疏 CSRRF 在正式 M0/L0 初始化前提下重新通过；两种 SPIR-V JIT callback 完整 272240 值 CPU 对照通过；双卡 1D FFT 替代路线通过。hipSPARSELt 的锁定 gfx1201 架构检查实际失败，仅据此范围报告不支持。 | 完成剩余 CUDA 同输入对照、状态核对、证据归档与最终检查 |
| S34 CUDA 补充对照与状态核对 | 已完成 | 新增 54 组专项对照全部通过：36 RNG、2 自有 SHA、3 callback、3 实际双卡 FFT、2 HSH Lt、8 solver。所有 639 入口均有结果，141 PASSED / 31 PARTIAL / 464 FAILED / 2 UNSUPPORTED / 1 BLOCKED。CUDA 基线/前端资格覆盖所有入口但保留缺 SDK/输入等阻塞；不将 imports 或返回 0 算正确性。 | 封存源码/日志、生成 README 和设计快照、运行最终一致性检查 |
| S35 全量执行交付与最终检查 | 已完成 | M0–M5 均已执行并保留失败/部分完成；141 个 PASSED 的当前源码均有匹配正确性证据；原始 866 源文件与 477 构建定义未修改。639 逐例页、30 库级表与根 README 已生成，6781 个生成链接核对通过，M1 16/95、CTest 16/16 和新增 54 对照均通过。小型证据及最终源码内容对象归档完成，6 个 GEMM 性能对照因 GPU 竞争明确 BLOCKED。 | 执行阶段结束；未迁移功能与外部阻塞按逐例报告保留，不计为成功 |
| S36 fork 首页支持文档 | 已完成 | 首页新增 30 模块支持矩阵，按模块去重为 75 个已验收算子/功能族（9 模块、141 个通过样例）；列出全部算子名称、验证范围，以及编译/API、语言绑定、运行、超时、缺独立参考、功能子集、硬件版本缺口和前置条件的逐类原因。fork 已核实为 zihaomu/CUDALibrarySamples_ROCm，目标默认分支 main。 | 核对归档与可提交文件，提交全部 ROCm 实现/证据/文档并推送 fork |
| S37 fork 发布验证 | 已完成 | 全部 ROCm 实现、逐例证据和首页详细文档已推送 zihaomu/CUDALibrarySamples_ROCm/main，发布提交 82496755ea474d7ae622cd5bc3264653d507d780；GitHub 远端提交与 README blob hash 已核对一致。干净 checkout 验证通过，首页 30 模块、75 已验收算子/功能族、141 通过样例均可追溯。 | 附入发布验证记录并同步推送文档收尾提交 |
| S38 第二批 17 项启动 | 已完成 | 按用户指定顺序：SpVV/SpGEMM/reuse 3 项、BLAS 8 项、tensor 4 项、solver 2 项。预先登记 original 与边界/参数变化 cases；AMD 物理 GPU0 空闲，HIP ordinal2，经 ROCm10.1 guard 校验。源码保持原始数学 API，补结果观测与显式输入 case。 | 先运行并独立验收稀疏 3 项和 BLAS 8 项 |
| S39 稀疏 3 项与 BLAS 8 项收口 | 已完成 | 11 个原始入口及 31 个输入 case 经 AMD/独立 CPU/CUDA 三方验收通过。SpGEMM reuse 更改数值后重算；BLAS 覆盖并列索引、空输入、旋转 flags、正负 alpha。发现并保留原生 rocBLAS rotmg 重复缩放 H 错误证据；项目 GPU 修正路径通过极小/极大/非对称权重，未修改共享 SDK。 | 继续 tensor 4 项与 solver 2 项，补完整输出及重构/残差验收 |
| S40 tensor 4 项与 solver 2 项收口 | 已完成 | 第二批 17/17、45 个输入 case 全部通过 AMD/独立 CPU/CUDA 三方验收；tensor 原始规模全部输出检查与小尺寸变化通过，solver QR/Cholesky 重构及残差通过。27 个 tensor 输入 buffer 按 seed 重建后 SHA256 全部一致。21 个故意损坏的数值/NaN 输出均被 oracle 拒绝。当前 158 PASSED / 14 PARTIAL，去重算子族 87。 | 更新 README 与阶段报告、归档全部证据、最终一致性检查并同步 fork |
| S41 第二批最终一致性检查 | 已完成 | 17/17、45 cases 的 CPU/ROCm/CUDA 三方验收通过；158 个当前 PASSED 实现均有匹配源码证据，首页 87 算子/功能族、30 模块与 639 逐例页已核对；21 个损坏输出拒绝检查与 27 个输入精确重建通过。原 CUDA 源文件/构建定义均未修改，小型日志已归档。 | 提交第二批实现、文档与证据，推送 fork/main 并核对远端 |
| S42 第二批 fork 发布验证 | 已完成 | 第二批主提交 c0ebdcb0d292d57204d91bbeb4cf3ff3022c505f 已推送 zihaomu/CUDALibrarySamples_ROCm/main；远端提交及首页 README blob 已核对。干净 checkout 检查通过，17/17、45 cases、87 算子族、158 成功样例的全部链接/证据有效。 | 发布验证记录随文档收尾提交同步，第二批执行结束 |
| S43 | 已完成 | 第三批锁定8个样例与26个必需输入case；ROCm10.1镜像与物理GPU0 guard通过，5090两卡空闲；构建补齐稀疏的hipBLAS/cuBLAS链接。 | 先执行稀疏3项：原始700×700网格及变体、五对角interleaved布局与独立CPU残差。 |
| S44 | 已完成 | 稀疏3项共9/9输入已通过ROCm/CPU/CUDA三方数值验收；CG/BiCGSTAB检查CSR、独立无预条件CPU求解、真实Ax-b与阈值、迭代上限；gpsv逐batch求解并检查六个interleaved输入和输出布局。BiCG变体的GPU生成RHS末位差异另存，改用捕获的共享RHS后输入hash相同。 | 开始solver4项：逐batch SVD/特征对与meig选区检查。 |
| S45 | 已完成 | solver启动前动态guard发现物理GPU0已被其它任务预约，按规则未执行任何分配；物理GPU1忙，GPU2空闲。保留预约变化证据，改选HIP ordinal1→物理GPU2。CUDA solver14个用例均已运行成功，待AMD与CPU验收。 | 使用物理GPU2执行solver与后续Graph Capture。 |
| S46 | 已完成 | solver4项14/14输入三方通过：gesvdjBatched逐batch奇异值/重构/完整U和V正交性，含秩亏；syevjBatched未排序原例、排序与扰动，保持W/V配对；syevdx/sygvdx索引、值域、全量、空区间，只观察meig个结果并检查普通/B正交性。AMD在物理GPU2执行。 | 执行SpVV真实Graph Capture和三次输入变化replay，检查非空图及GPU kernel节点。 |
| S47 | 已完成 | Graph Capture的3/3输入三方通过：原规模65536元素、1000次SpVV捕获2000个GPU kernel节点；每case三次实际replay，修改Y后结果变化，零输入回零。切换device pointer mode，修正原例未初始化输入与未验输出。24/24有限值/NaN/特征配对/meig/空图/无kernel/假replay反向检查均拒绝；36/36稀疏输入buffer重建或固定fixture hash核对通过。 | 更新首页、逐例矩阵、可复现实验报告与最终完整性检查，然后推送fork。 |
| S48 | 已完成 | 第三批交付完整性检查通过：639入口终态、166份当前源码验收证明、30模块矩阵、639详情页、6883个生成相对链接、866源文件与477构建定义保持原样；8/26三方、24反向与36输入身份均通过，历史M1/第二批证明无回归。当前166 PASSED、6 PARTIAL、464 FAILED、2 UNSUPPORTED、1 BLOCKED，算子/功能族91。 | 提交第三批实现与证据，干净检出离线复核，推送fork并验证远端README。 |
| S49 | 已完成 | 第三批实现提交c9f83141已推送zihaomu/CUDALibrarySamples_ROCm main；无build产物/CPU依赖/外部doc的干净检出离线复核通过166份源码证明，远端main SHA和GitHub首页README blob均与本地匹配。报告、逐例库/范围/缺口和8/26验收已发布。 | 同步发布验证记录与设计快照，确认最终远端与工作区干净。 |
| S50 | 已完成 | 按用户要求增加统一支持方式与详细log总表：639入口、30模块详细表及JSON索引；逐项记录实际库/后端、实现方式、源码hash、已过/必需case、范围或失败原因、AMD/CUDA直接log与CPU验收报告。通过项按当前源码hash选择证明，CUDA历史尝试明确标注。首页添加入口，并更正第三批样例仍待验收的过期描述。 | 封存文档生成器并做完整性复核，提交推送fork。 |

## 12. 当前实施快照（工具刷新）

本节替代设计阶段的未开始快照。逐步过程保留在第 11 节；整例成功、部分功能、路线失败分别报告，不将执行过计划解释为所有功能均已迁移成功。

更新时间：2026-11-09T14:33:30.233352+00:00。

清单为 **639 个独立可执行/脚本源入口**（563 C/C++、76 Fortran/Python），逐例均有实际尝试记录。当前：`PASSED` 166；`PARTIAL` 6；`FAILED` 464；`BLOCKED` 1；`UNSUPPORTED` 2；`NOT_STARTED` 0；`IN_PROGRESS` 0。

M0 静态审计覆盖全部 477 个构建定义和 866 个源文件，记录 863 个声明、682 个源文件构建绑定；53 个 SDK/测试生成输入/条件变体表达式逐项归类，不重复膨胀入口数量。这不是全部 SDK 条件配置均已生成运行的声明。

| 里程碑 | 实际结果与边界 |
| --- | --- |
| M0 | 完成入口清单、静态构建审计、30 库级表与逐例报告、ROCm/CUDA 锁、runner、fixture、证据结构。 |
| M1 | 16/16 个原始 profile + 共 95 个必需用例，ROCm/独立 CPU 参考/CUDA 共享输入对照通过。包含原始非 SPD info 行为和真实 GPU FFT scaling；LU 无 pivot 路径显式补身份 pivots。 |
| M2 | 全部 224 个基础数学 C/C++ 入口已尝试；BLAS 三方、稀疏 expected、全部 generator 分布检查逐项附报告。未通过的 API/signature、算法或执行结果保留 FAILED/PARTIAL。 |
| M3 | hipCOMP 源码构建、LZ4 GPU 往返通过；RPP U8 resize 能力探针通过；rocJPEG baseline 与 CPU libjpeg 最大像素差 2，后两者不代表整个原始样例通过。hipTensor 已建成，gfx1201 FP32 contraction 返回 ARCH_MISMATCH；保留 FP32 的 rocBLAS + HIP 排列替代通过原始 extents/模式，全部有限值和 32 CPU 抽样点及小尺寸全量检查。hipSPARSELt 的 gfx1201 kernel 缺失有实机与锁定源码架构 gate 证据，2 例限定为 UNSUPPORTED。 |
| M4 | 两卡 hipBLAS + RCCL GEMM 探针通过；3D C2C/real-pair 保留原始双 GPU descriptor，1D Xt 缺口由两卡 hipFFT + RCCL + HIP 合并实现。3 个多卡 FFT 同输入 CUDA 全量对照通过。原始 MPI/多节点与分布式高级 API 缺口逐例保留，单卡不冒充多卡。 |
| M5 | 所有 MathDx/特殊 SDK 入口已实际构建/前端尝试；SHA2/32-lane SHA3 各 14 输入与 hashlib 及同实现 CUDA 精确对照；cuPQC vendor SDK 基线缺失另记。cuDSS simple C++ 及 2 个 Fortran 原始入口改用 CPU 稀疏符号图分析 + rocSOLVER CSRRF GPU 数值分解/求解并通过残差，未转 dense，未覆盖高级 API。其余 Fortran/Python 只做前端/绑定尝试，原样复制不计为已实现代码。 |

报告入口在 `CUDALibrarySamples_ROCm/migration/reports/`；全部入口详情在 `migration/sample-reports/`。失败不等于整个 ROCm 或硬件不支持；只有确定版本能力缺失时才用 UNSUPPORTED。未替换的 NVIDIA API、未实现的 AMD 算法改写与缺失 SDK/输入分别给出证据和恢复条件。

AMD 使用 immutable ROCm 10.1.0 foundation 和项目 overlay。**HIP ordinal 2 → 物理 GPU0，ordinal 3 → 物理 GPU1**，按 PCI 地址校验，物理 GPU3 禁用；共享预约动态读取。早期误将 HIP ordinal0 当成物理 GPU0 的批次已在第 11 节说明，仅作历史调试记录，不用于最终验收。两机器时钟存在约两分钟偏差，使用 run ID 与 source/input hash 关联。

复现 M1：

```bash
cd /home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm
HIP_VISIBLE_DEVICES=2 tools/migration/run_rocm.sh
python3 tools/migration/compare.py
python3 tools/migration/render.py
```

新增 54 个双端专项对照通过（36 RNG、2 SHA、3 callback、3 双卡 FFT、2 HSH Lt、8 solver）；M1/BLAS 三方对照另记，不重复计入入口完成率。JIT callback 分别经离线 SPIR-V 与 HIPRTC 运行时 SPIR-V 路径，保留 device callback 融合，272240 个语义输出全部通过 CPU 和 CUDA 检查。

**性能结果为 BLOCKED**：已执行 6 个 FP32/FP64 GEMM profile，但 AMD 卡存在其它任务，实际空闲 gate 失败。不报告合格速度比；原始计时、三组统计、CPU 误差与恢复条件在 `migration/reports/performance-comparison.md/json`。

专项原始 profile、native probes、Fortran/Python、分布检查和性能复现命令分别保存在逐例详情及证据 `commands.json`。CPU 参考依赖在 `build/python-reference`，native 依赖在 `build/`，不修改共享 foundation。小型日志已归档，最终源码/fixture 身份在 `migration/source-tree.json`，CUDA 观测副本可从内容对象恢复。全部批次的终态结果不等于全部 API 已迁移；失败与未实现能力保留在本次交付中。

第二批：17/17 样例、45 个输入 case 通过独立 CPU，CUDA 对照 17/17。覆盖稀疏 3、BLAS 8、tensor 4、solver 2；tensor 保留原始规模，全部语义输出检查，加小尺寸/非零系数/零系数。27 个共享大/小输入 buffer 可按 seed=20261109 重建并逐文件核对 SHA256。原生 rotmg 重复缩放 H 错误由项目 HIP GPU 修正；原生失败与精确失败源码另存。详细见 `migration/reports/batch2.md` 与 `rotmg-scale-fix.md`。CUDA 侧 cuTENSOR 2.8.1 仅安装在项目 build overlay，单独锁定 library/wheel hash。

第三批：8/8 样例、26 个输入 case 三方通过。稀疏3项 → solver4项 → Graph Capture1项依次完成。CG/BiCGSTAB 保留原始700×700网格，独立CSR/CPU求解/真实残差/收敛检查；BiCG变体共享捕获RHS消除生成顺序造成的末位差异，36个输入buffer可重建或按固定fixture核对hash。solver按batch和实际meig检查，含秩亏、未排序配对及索引/值域/全量/空区间。原规模SpVV图含2000个GPU kernel节点，三次输入变化replay通过；24个数值/图语义反向检查全部拒绝。AMD稀疏用物理GPU0，之后该卡被预约，guard阻止启动，solver/graph改用HIP ordinal1→物理GPU2。报告：`migration/reports/batch3.md`。

## 附录 A：按目录核对的初始范围

下表的“源文件”仅统计 Git 跟踪的 `.cu/.cpp/.c/.f90/.cuf/.py`，包含辅助文件，**不能作为完成率分母**。库级样例数量由 M0 的目标清单确定。

| 子项目 | 跟踪源文件数 | CMakeLists 数 |
| --- | ---: | ---: |
| `MathDx/cuBLASDx` | 36 | 1 |
| `MathDx/cuFFTDx` | 49 | 5 |
| `MathDx/cuRANDDx` | 7 | 1 |
| `MathDx/cuSolverDx` | 43 | 1 |
| `MathDx/libmathdx` | 12 | 1 |
| `MathDx/nvCOMPDx` | 7 | 1 |
| `NPP` | 9 | 8 |
| `NPP+` | 6 | 5 |
| `cuBLAS` | 83 | 79 |
| `cuBLASLt` | 39 | 21 |
| `cuBLASMp` | 14 | 1 |
| `cuDSS` | 149 | 59 |
| `cuEST` | 141 | 68 |
| `cuFFT` | 13 | 8 |
| `cuFFTMp` | 30 | 1 |
| `cuPQC` | 6 | 0 |
| `cuRAND` | 36 | 9 |
| `cuSOLVER` | 39 | 30 |
| `cuSOLVERMp` | 16 | 1 |
| `cuSOLVERSp2cuDSS` | 7 | 1 |
| `cuSPARSE` | 37 | 37 |
| `cuSPARSELt` | 2 | 2 |
| `cuTENSOR` | 23 | 1 |
| `cuTENSORMg` | 2 | 1 |
| `cuTENSORMp` | 3 | 1 |
| `nvCOMP` | 33 | 2 |
| `nvJPEG` | 7 | 6 |
| `nvJPEG2000` | 4 | 5 |
| `nvMatmulHeuristics` | 7 | 0 |
| `nvTIFF` | 6 | 6 |
| **合计** | **866** | **362** |
