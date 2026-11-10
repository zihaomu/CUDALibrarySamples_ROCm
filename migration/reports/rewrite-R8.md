# R8：阶段回归、证明审计与交付

状态：**COMPLETED_SCOPED（本轮回归与交付）**。固定审查/复现源码 `97dab6202fb02b578932a50c145661448dc3fa7d`。三位独立审查批准，实际干净检出证据再次独立CPU复验通过；[复审记录](rewrite-R8-review.json)。R5等未实现范围继续保留，不表示全量计划算子均实现。

| 交付项 | 当前结果 | 证据 |
| --- | --- | --- |
| 原始 CUDA 保护 | 866源文件、477构建定义、639稳定入口保留，原始源码未改 | [全量审计](final-validation.json) |
| 既有 GPU 回归 | 当前 CMake/CTest 16/16通过 | [实验](rewrite-cmake-regression.json) |
| 新资格当前依赖 | 21项通过，完整数值/参考/fixture传递闭包；690个唯一引用封存记录纳入核对 | [逐例闭包](rewrite-selected-proof-audit.json) |
| 历史证明 | 原始B批报告不覆盖；新资格按封存证明替代，旧CPP错误资格单独撤销 | [撤销后的实际修复与剩余排列差异](rewrite-reordering-cpp-repair.json) |
| 干净检出 | 第二次fresh clone通过16CTest＋21个原始profile AMD/CPU；第一次CPU LAPACK符号缺失未计通过 | [完整复现报告](rewrite-clean-checkout.json) |
| 全部未完成范围 | 408条有精确源码身份、原错误/日志、路线、成本、最小后续实验和重试条件 | [逐例表](rewrite-remaining-assessment.md) |

## 本轮实现与范围

| 阶段 | 新通过入口 | 预登记case | 实际实现与边界 |
| --- | ---: | ---: | --- |
| R1/R2 | 8 | 51 | 3M、FP16 planar、INT8 native hipBLAS与真实GPU布局、device LU/POSV/TRSM；[明细](rewrite-R1-R2.md) |
| R3 | 2 | 15 | NCC原始文件/CLI、原始FP32 rank-SVD；[明细](rewrite-R3.md) |
| R4 | 1 | 7 | IEEE/PKZIP CRC32；包含一项空chunk拒绝语义，不把CRC32C当CRC32；[明细](rewrite-R4.md) |
| R5 | 8 | 56 | 标准Fortran真实入口+C ABI共享HIP；包含8项奇异输入拒绝。原CUDA Fortran工具链BLOCKED保留，GENERAL额外奇异native cuDSS输出NaN不计数学通过；[明细](rewrite-R5.md) |
| R7 | 2 | 14 | 实际GPU TILE裁剪/packed压缩/metadata/稀疏乘法；默认FP16限定。原生hipSPARSELt失败与项目重写成功分列；[明细](rewrite-R7.md) |

21项新资格，共143个预登记case（含错误/拒绝语义），不同于143个算子。撤销1项旧资格后，支持211→231，净增20；111→117个功能族、17→18个模块。当前231 PASSED/23 PARTIAL/385 FAILED，0 UNSUPPORTED不意味着全部支持。

剩余408项：R3 22、R4 96、R5 66、R6 224。R5原始73前端仅8整例验收、65仍待实现，另1旧CPP排列合同未满足；R6是研究评估完成，未完成224个实现。wave64、Windows、多节点和性能比率均未验收。MOAT全项目surface仍owed，无completed或waiver冒充。

## 日志与复现边界

每次GPU构建/运行/数值核对/失败都有独立ID，命令、cwd、环境差异、stdout/stderr、时间、返回码、源码CAS、输入与输出hash、seal和恢复原因。源码封存覆盖共享头、构建配方、oracle和fixture。选中资格固定首次Git发布的seal；R5/R7完整引用清单固定到各自发布提交。仅允许经过审查且精确内容hash限定的记录器/构建元数据扩展，不允许变化的数学或oracle沿用旧证明。

干净检出复现不复制历史构建产物：重新配置/编译16个M1及21个新入口，运行21个原始AMD profile与独立CPU检查。镜像自带LP64 CPU OpenBLAS显式提供LAPACK符号，路径/hash/ABI记录；数值oracle源未改。真实输出目录、fresh Fortran构建命令及结果递归进入父实验封存；大输出留在本机raw artifacts，以SHA索引，公开归档保留完整文本和可恢复身份。其它机器仅clone并不拥有全部历史大输出，需同步raw或按冻结输入重跑；不声称已在冷clone重验所有历史原生CUDA实验。

默认分支是 `rocm`；最终交付推送用户fork，不向AMD/NVIDIA upstream发布或提交PR。


最终宿主校验：[冷恢复与反例测试](rewrite-R8-host-checks.json)、[全部封存实验与schema审计](rewrite-evidence-audit.json)、[639入口与源码/文档一致性](final-validation.json)。本轮交付的机器可读汇总：[rewrite-R8.json](rewrite-R8.json)。当前2454份封存记录，无遗留失联/未封存尝试。690个唯一引用的资格传递闭包核对通过；各自原始case范围保留，未把本轮21个原始profile复现外推为全部历史变体重跑。
