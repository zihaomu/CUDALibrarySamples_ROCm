# IMG-02：Watershed 完整入口实施记录

状态：IN_PROGRESS。两个原入口仍为 PARTIAL；下述新模型尚未作为生产 GPU 实现签发资格。

## 已确定的图像语义

原生 NPP 13.2.0 与 NPP+ 12.4.0 在 5090 物理 GPU1 上各运行 18 个小输入、4/8 两种邻域、五种边界模式、三种 scratch 初值，共各 540 次调用、1080 件产品。返回状态与 padding 均正常；重复结果及两库结果一致。该结论限定此次输入，不能推断所有尺寸/调度均确定。

八邻域分割灰度可由独立严格下降森林复现：只选择比本像素严格更低的邻居；最低高度相同时按行优先，随后沿固定下降方向到终点。不让平台内部像素无条件沿等高方向流到平台出口。18 个小输入及 6 张原始大图的灰度全部逐像素一致。

五种原生边界模式的图像输出也已定位：用最终灰度与上方、左方像素比较生成边界；NONE 保持灰度、BLACK/WHITE 分别置 0/255、ONLY 黑边白底、CONTRAST 在边界以灰度 `<128` 选白，否则选黑。18 个小输入及 NPP+ 三张原图的 ONLY/CONTRAST 全部逐字节复现。边界依据灰度，不能用任意八邻域标签差异代替。

| 研究 | 结论/证据 |
| --- | --- |
| 原生重复与双库核对 | [semantic reference](image-watershed-semantics-reference.json) |
| 严格下降 tie 顺序、原图 | [tie research](image-watershed-tie-research.json) |
| 输出灰度连通块 | [label topology](image-watershed-label-research.json)：灰度相同不能自动合并全部 marker |
| 无向标签等价图 | [seed graph](image-watershed-seed-graph-research.json)：会过合并，不能直接采用 |
| 有向最小标签不动点 | [directed model](image-watershed-directed-labels-research.json) |
| 边界规则及原图 | [gray boundary](image-watershed-gray-boundary-research.json) |
| 编号来源/瞬态更新 | [label origin](image-watershed-label-origin-research.json)、[cell update](image-watershed-cell-labels-research.json)：仍不能宣称原生分区完全一致 |

## Marker 标签的剩余差异

已测原生标签并不总是一标签一灰度：六原图分别有 2、11、37、39、46、25 个 marker 同时包含不同分割灰度。只凭这一观察不能断言厂商缺陷；可能与其标签初始化、更新或复用规则有关，后续报告保留这些事实。

一个不依赖厂商编号的确定性候选是：固定上述严格下降森林；终点可以接收相邻像素最终下降终点的标签，但仅当最终灰度相同；反复取自身及这些有向可达终点的最小行优先索引，再把标签传回下降森林。每个标签保持单一灰度，ID 是有意义的图论规格，不依赖 scratch 初值或线程更新顺序。

此候选在六原图上的 marker 上/左差异 OR 边界掩码一致率为 99.9295%–99.9950%，按候选区域多数映射的像素一致率为 99.9530%–100%；18 个小输入中 17 个分区完全一致，量化随机输入上述 OR 掩码一致率 98.3550%、多数映射像素一致率 97.9221%。OR 掩码不是逐邻接关系：两个方向的变化可能互相掩盖。独立复审已指出此命名问题，正式统计改为分别计数水平、垂直及对角边，旧 JSON 指标保留并注明。上述均为开发测量，**不是已经冻结的通过阈值**。多数映射也不等于一一匹配，正式报告必须同时检查合并和拆分。

独立合同复审确认可以采用明确的 ALGORITHM_VARIANT：图像灰度及全部边界模式与原生 EXACT，marker 采用上述公开确定性图规则，与独立 CPU 精确核对，同时检查每个区域的八连通、恒定灰度、下降/向前可达关系、逐边邻接及压紧标签双射。**marker 区域划分会变化，不仅是编号变化，不宣传厂商分区等价。** 原生 marker 的合并/拆分、完整交叉计数、一对一匹配及未匹配惩罚、逐区域 IoU、小区/宏平均/面积加权差异作为兼容性诊断，不能仅用全图相似度掩盖问题。新保留输入和必需反向检查在下一轮运行前冻结；源图/边界的 EXACT 门槛不放宽。

隔离 HIP 核心已完成18开发输入的 padded/ROI 执行，独立 CPU 改用强连通分量缩点和 DAG 可达最小值求解，避免复用 GPU 迭代。首次验证工具在读取 `run.json` 时误用 `result.json` 默认值，修复前失败和恢复均保留；正式资格尚未签发。

## 接续工作

1. 评审并冻结候选完整合同、保留输入与反向检查；原生分区精确与算法变体必须区分。
2. HIP 生产实现与独立图论 CPU oracle；ROI、pitch、padding、容量、资源和失败行为检查。
3. 两个原入口全部 8 次原图使用/22 件产品、GPU trace、变化输入、冷构建和复合资格。
4. 通过后逐项更新主表与支持日志；此前维持图像 14/26、全项目 253 PASSED。

原始失败仍见 [旧 Watershed 报告](image-watershed.md)。所有实验、源快照与命令由 `Experiment` 记录，实时计划在 [image-completion-plan.md](../image-completion-plan.md)。

## 60 输入完整候选与原生参考差异

已冻结 36 个新保留输入，连同 18 个开发输入、6 张原图组成 [60 输入合同](../rewrite/image-watershed-completion-contract.json)。合同的[独立规范](../rewrite/image-watershed-completion-spec-v1.json)不依赖候选源码修改；初次 freeze 与独立绑定记录都保留。HIP 的 compact、padded/ROI、inplace 各输出 420 件产品，null marker 输出 300 件产品。padded 与 compact 的全部 CPU 产品、逐区连通/恒灰及 NPP 图像模式均通过，但 **NPP+ 的 3 张保留坡度图失败，原完整合同结论仍为 NUMERIC_MISMATCH**。不能将执行退出 0 当作这组验收通过。

NPP+ 12.4.0 在 `heldout-ramp-x`、`heldout-ramp-y`、`heldout-ramp-diagonal` 的分割和边界图与 NPP 13.2.0、独立 CPU 和 HIP 不同。[原失败](image-watershed-completion-reference-padded.json)与[逐值定位](image-watershed-native-ramp-diagnosis.json)均保留；固定 31–66 步截断假设不符合实测，未把该猜测写成原因。

另冻结 [24 个解析坡度](../rewrite/image-watershed-monotone-native-profile.json)：17、33、49、65、97、129 边长，水平、垂直、对角、反向四类。每个非零像素都有更低邻居，所有终点灰度均为 0，因此完整严格下降结果可独立证明为全零。NPP 两种 pitch 与 HIP 全部五图像模式精确；NPP+ 两种 pitch 都有 16 个输入出现非零残留，连续调用还会改变残留。这是[实测的参考分歧](image-watershed-monotone-reference.json)，不是已经接受的误差容限，也不武断断言闭源实现内部原因。

准备评审明确的参考修订：继续要求全部输入 CPU 与 NPP EXACT、其余 57 个输入 NPP+ EXACT；仅上述三个已定位的单调坡度在“每个非零像素均有更低邻居、终点全零”的解析不变量及第二原生参考同时成立时，保留 NPP+ `NATIVE_MISMATCH`，按项目确定性数学规格验收。24 个额外解析输入加入确认范围。该修订不能把 NPP+ 原始比较改成 PASSED，也不允许放宽像素误差或新增任意例外；通过独立复核并封存修订前不签发资格。

## 复审与反向检查

独立代码审查确认：8 次 pointer jumping 覆盖 8 位严格下降最长 255 条边；GPU 传播、收敛上界、stream、空 marker 和资源释放未发现可证实错误。SCC 规格也经 1241 个小图的独立可达搜索核对（审查观察，不代替 GPU 证明）。

复审指出 P1：原比较器只核查 seal，不能拒绝将合法 NPP 记录代替 NPP+ 或将 compact 记录代替 padded。已增加 [严格绑定](../../tools/moat/image_watershed_completion_binding.py)：规范封存、60 输入身份、actual vendor/SDK、实际命令中的布局、构建源码/可执行文件 SHA、允许 GPU/ROCm 环境以及上传原生输入逐项交叉检查。[16 项身份正反控制](image-watershed-binding-controls.json)通过；合同和构建证明纳入明确引用闭包。

另有 [18 非法视图/9 分配失败/恢复](image-watershed-v2-controls.json)与 [14 类数值和证据反向控制](image-watershed-validator-controls.json)通过。修复后的全合同验收、生产入口、trace、冷构建和最终资格尚待完成。

## 原入口与修订门槛复核

四份 amended 验收各有 60 个唯一输入、245 项通过检查。CPU/HIP 与 NPP 的全部 60 输入保持精确；NPP+ 的 57 个输入保持精确，三个固定长坡度输入保留 `NATIVE_MISMATCH`。严格旧报告仍为 `NUMERIC_MISMATCH`，14 项修订反向控制通过。独立复审已确认此前身份绑定、连续调用和例外限定问题闭合；这不替代最终整例资格。

- 两原入口全部 22 件产品通过独立 SCC CPU 参考及相应原生图像模式对照。
- 两个真实 GPU trace 通过，NPP 5 图调用下降 5 次、指针跳跃 40 次、marker 传播 296 次、灰度与输出各 5 次；NPP+ 3 图对应 3/24/272/3/3，另有三个 GPU 压紧阶段各 3 次。全部 kernel 在物理 GPU1 / PCI `0000:23:00.0`，trace 输出与未 profile 输出完全一致。
- 首图按预登记 `255-v` 变换后，全部 22 件产品再次通过独立 CPU；首图产品均变化，其他图像产品不变。
- 两程序各覆盖缺首图、缺末图、首图少一字节、首个输出路径为目录，共 8 次实际失败流程；非零退出、具体诊断、无错误图像伪成功产品、之前已完成产品字节均检查通过。

证明见 `image-watershed-completion-entry-trace.json`、`image-watershed-completion-entry-replay.json`、`image-watershed-completion-replay-reference.json`、`image-watershed-completion-entry-negative.json`。下一步固定提交冷构建、最终复审与资格签发，当前主表尚未提升。
