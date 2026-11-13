# 图像库功能等价实施方案

日期：2026-11-11。状态：**IN_PROGRESS**。逐步实施中；仅封存资格会增加支持数。

2026-11-13 已依据最新源码和资格制定[剩余图像模块完整实现计划](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/migration/image-completion-plan.md)，细化后续13个欠项和26入口最终验收。本页保留早期方案，实时数量以文末检查点和支持主表为准。

本方案落实用户“合理差异可以接受”的要求，是[完整图像库计划](image-libraries-plan.md)的执行细化。[生效验收政策](rewrite/image-acceptance-policy.json)和[差异复评](reports/image-difference-acceptance.md)作为依据。目标仍为原定 26 个入口：方案起点为 2 通过、8 部分、16 失败，新增目标为 24 个；完整模式和输入分支不删减。此处历史检查点曾发布 9 通过、7 部分、10 失败，不作为当前数量。

## 1. 执行原则与前置工作

采用“明确项目算法 → 独立 CPU 验收 → NVIDIA 对照及差异说明 → 原始完整入口验收 → 发布支持”的顺序。通过项按 `EXACT`、`NUMERICAL_TOLERANCE`、`ALGORITHM_VARIANT` 注明比较方式，完整功能等价通过同样计入支持。

I0 调整为公共基线和各入口前置合同两部分。原始源码身份、SDK/环境及证据工具已有检查点；每个即将实现的入口仍须先固定完整合同、输入和验收配置。Canny 所需前置完成后可签发其资格，**不等待所有 JPEG2000 纵向研究结束**。JPEG/JPEG2000 研究及其未完成合同继续留在 I0，不把整个 I0 提前标为完成。这是对原先 I0→I1 整体依赖的明确细化，不删除任何入口的前置验收。

每个入口保留两类结果：

- 主验收：是否满足已声明的项目算法、功能、数据格式和 GPU 执行要求。
- 跨厂商比较：精确程度、质量/结构差异及兼容范围；合理差异可接受，并保存完整原始输出与指标。

## 2. 首批：先完成一个 NPP+ Canny 入口

目标为 `NPP+/cannyEdgeDetectorPython::cannyEdgeDetector.py`，通过后图像范围可由 2/26 增至 **3/26**。当前 3 个外圈像素差异不再作为厂商复刻的阻塞；最终 HIP mask 和原始 Python 流程仍须实际实现和验收。

| 步骤 | 实现与交付物 | 完成条件 |
| --- | --- | --- |
| 1. 固定入口合同 | 将 C1 Sobel3/L2、NMS、局部阈值/边界规则和原例预处理写成独立 profile；登记全量输入、错误情况和指标 | CPU 模型已有证据与原始 Python 预处理分开标注；BGR/RGB 解释、灰度权重和舍入明确；不更换被否定的 boundary-self 假设 |
| 2. 补全 HIP mask | 复用 `rocm/common/image/canny_stages.*`，增加 GPU 阈值/连接及 pitched 8-bit mask 输出 | 对明确的项目 CPU 定义逐像素一致；跨 vendor 单独报告边界差异；CPU 不承担生产像素计算 |
| 3. 完成 C ABI | 补充 workspace、尺寸/pitch、stream、返回码与资源生命周期接口 | 非默认 stream、重复调用、输入变化、非法尺寸/dtype/pitch、并发独立状态均实测 |
| 4. 接入真实 Python | ROCm Torch tensor 通过明确的 C ABI 调用共享后端；补齐项目私有 Python 依赖 | 输入/输出 tensor、stream 和临时 buffers 生命周期正确；保留原处理顺序、PNG 和 CSV 流程 |
| 5. 跑完整原例 | 8 个原始分辨率，保留 5 次 warmup 和每分辨率 1000 次测量循环 | 逐尺寸完整输出检查、真实 GPU trace、文件复读；数值通过和可发布性能比较分别登记 |
| 6. 反向与独立复核 | 允许差异、超限差异、错通道/布局、空输出、丢结果、失败 rc、错误 stream/ABI 等检查 | 验收器既接受约定内差异，也拒绝超限或结构性错误；失败不能被跳过 |
| 7. 签发与发布 | 提交固定代码及复合证据，再发布对应样例、算子与支持日志 | 完整必需 cases 和审查均通过；原始 CUDA 脚本与修正绑定的 native API 基线分别记录；首页只更新当前支持 |

首批新增独立 corpus 必须包括弱边缘、边界直线/交叉、平台/斜线、稀疏边缘、常量/空结果、奇数尺寸、非连续/pitched 输入和修改输入后的复用。保留全部逐点差异、边缘数、内部/边界统计及结构检查。不能通过忽略整个边界或全图差异占比让错误实现过关。

C1 的步骤 1–7 已全部完成并发布：[完整验收](reports/canny-plus.md)、[固定资格](reports/canny-plus-qualification.json)、[三项独立复审](reports/canny-plus-review.json)。原始 8 分辨率、31 组完整 mask、49 项运行合同、28 项正反向检查及干净检出重放通过。该入口新增支持已发布；C3 两入口亦已完成以下验收。

## 3. 第二批：完成 NPP 的两个 C3 Canny 入口

目标为 `NPP/nppCanny::npp_canny_simple.cpp` 和 `NPP/nppCanny::npp_canny_simple.py`，通过后累计可达 **5/26**。

共享 Sobel/L2/NMS、C ABI、文件和 Python 基础设施，保留 C3 最大梯度通道选择及对应源例的预处理、默认阈值、文件/计时流程。**不直接把 NPP+ C1 局部模型套到 NPP C3**。

当前 NPP 对照中存在数千像素的差异，与已接受的 NPP+ 3 个边界点不是同一结论。先固定并分析连接算法；可选择合理、明确的 Canny 算法变体，但需给出独立 CPU 与构造几何图的效果证据，报告与原生 NPP 的实际差异，不声称 mask 精确兼容。若这一功能判断尚不成立，两项保持 PARTIAL；不阻塞已完成入口的发布。

C3 两入口现已完成并发布：[完整验收](reports/canny-color.md)、[固定资格](reports/canny-color-qualification.json)、[三项独立复核](reports/canny-color-review.json)。22 组完整 mask、两语言 10 个完整文件流程、55 项运行合同、12 项 C++ 类检查、10 项 CLI、39 项验收器检查及干净检出重放通过。项目采用经典八连接强种子滞后，原图比 native NPP 少 4328 个像素，完整差异及结构说明保留。I1 状态为 COMPLETED_SCOPED，不代表后续图像范围完成。

### I2 当前进展

两个 CCL 完整入口已发布：[支持方式和验收](reports/image-ccl.md)、[固定资格](reports/image-ccl-qualification.json)、[独立复核](reports/image-ccl-review.json)。覆盖原始五图、单图/异构batch、NPP+默认及条件编译、全部batch 1..5；27mask、44运行、3默认/外设备/销毁stream、15完整流程165文件、39CLI、31正反例、3原生预检反例及20子记录冷重放通过。当前NPP/NPP+分区缺陷独立保留，项目与CPU正确分区精确。两项轮廓现亦已完整验收发布：[支持方式](reports/image-contour.md)、[资格](reports/image-contour-qualification.json)、[独立复审](reports/image-contour-review.json)。22完整输入、15工作流/55RAW、61参数、26设备数据、11状态/stream、32CLI、58反例及22子记录冷重放通过。I2剩余一项signed/unsigned EDT与既有EDT/NCC回归，保持IN_PROGRESS。

## 4. JPEG 路线

1. **复用 baseline**：继续使用已实测的 rocJPEG/VCN + HIP 布局、ROI、缩放等后处理。将输出策略匹配的独立 CPU 参考正式接入验收，保留 Pillow 默认平滑结果作为另一份质量比较。不因之前最高 52 的跨策略差异先重写整个 baseline decoder。
2. **补 progressive GPU 解码**：CPU 只解析 marker/scan 描述；GPU 实现 Huffman、DC/AC 首次与 refinement、EOB run、restart、系数累积、IDCT 和像素重建。先覆盖现有两张 SOF2/10-scan 图片，再扩展独立多 scan/重启/损坏输入。
3. **完成四个解码入口**：统一接入 decoder、multiple instances、backend/ROI 与 Python decoder tests。验证 batch 尾部、多实例独立状态、实际 stream 依赖、布局/ROI/scale、所有实际 backend 参数。强制硬件模式按真实能力处理，不能伪造支持。
4. **补 GPU 编码链**：DCT/量化、DC 差分、RLE/Huffman、bit packing/stuffing、标准有效码流与 metadata；完整接入 encoder、多实例、resize 和 watermark 的重编码。源例要求保留的 progressive 输出、量化表/采样/metadata 分支仍需实现。

baseline 组件可提前完成并登记；四个解码整例的资格以各自完整必需模式为准，不能把两张有效 progressive 图片排除后宣称整例完成。CPU 整幅编解码回退不计作最终 GPU 支持。

当前 10 张 baseline 的 maxAbs1–3、PSNR>55.7dB、SSIM>0.9997 是已接受观测，**不直接当作所有 JPEG 的统一门槛**。正式 profile 按位深、输出格式、上采样/颜色规则固定误差预算，保存完整配置、全像素/分量误差、RMSE/分位数、PSNR/SSIM 以及局部结果，并在新增 corpus 上验证。

### 第一版验收配置

以下为项目提出的候选配置，须在新增独立测试集上确认后写入正式 profile；它们不是行业统一标准，也不是对其它类型/模式的默认批准。超限时保留失败并分析处理策略或实现原因，不随结果提高门槛。

| 对象 | 候选判据 | 适用范围 |
| --- | --- | --- |
| Canny GPU 与项目 CPU 主参考 | 最终 mask 每个像素精确；尺寸/pitch/ROI外区域精确 | 固定的 C1/C3 算法 profile；NPP+ 与 NPP 连接策略分别登记 |
| Canny 与 native | 完整记录内部/外圈差异、边缘数与结构；已确认的 3 个外圈点允许不同 | 不使用“忽略整个边界”的通用规则；新增内部差异须按算法定义和结构效果解释、复核 |
| 8-bit JPEG baseline RGB/灰度解码 | 相同输出策略下 maxAbs≤4；每通道 RMSE≤1；每通道 abs-error 第99百分位≤2；全图PSNR≥48dB；RGB平均SSIM≥0.995 | 先用于已明确配置的普通8-bit profile；原分辨率SSIM定义沿用复评实验。progressive、其它采样/格式需单独登记验证，不自动继承通过 |
| CCL/label compact | 固定映射后分区、背景、分量数精确 | 无语义编号可不同；seed/引用等有语义字段必须对应 |
| JPEG/JPEG2000 编码 | 独立跨解码成功、尺寸/采样/位深/模式正确、quality参数生效、相应重建指标满足profile | 合法码流字节和压缩文件大小可不同；报告长度必须与实际文件一致 |
| 无损/可逆 JPEG2000 | 规定转换后的整数/浮点表示逐值或bits精确 | 不使用上述JPEG有损解码阈值 |

原始尺寸、元数据语义、输出数据长度及 GPU 计算路径不采用视觉容差。此处“长度正确”指与实际数据/格式/接口声明一致，不要求两个合法编码器产生相同压缩文件大小。

## 5. 批次与目标

下表为条件目标，不是已通过数。每批独立验收并实时更新文档，不等整个项目结束才发布结果。

| 顺序 | 对应原阶段 | 内容 | 新增入口目标 | 累计目标 |
| --- | --- | --- | ---: | ---: |
| 1 | I1 第一部分 | NPP+ Python C1 Canny 完整 GPU/文件/benchmark 入口 | 1 | 3/26 |
| 2 | I1 第二部分 | NPP C++/Python C3 Canny 两入口 | 2 | 5/26 |
| 3 | I2 | CCL/label compact、两类 contour、NPP+ signed/unsigned EDT；旧 EDT/NCC 回归 | 5 | 10/26 |
| 4 | I3 | NPP/NPP+ watershed、完整 flood fill、Hough、OpenCV benchmark | 5 | 15/26 |
| 5 | I4 | JPEG 四个解码入口，补齐实际所需 progressive/ROI/多实例/Python | 4 | 19/26 |
| 6 | I5 | JPEG encoder、多实例及 resize/watermark 完整重编码 | 3 | 22/26 |
| 7 | I6–I8 | JPEG2000 Part1、MQ/HT、NLT3、类型/码块/quality、tile/partial/pipeline 全分支 | 4 | 26/26 |
| 回归 | I9 | 全 26、受影响的既有资格、冷构建、独立审查与发布 | 0 | 保持已通过范围 |

JPEG2000 先实现并核验码块与变换组件，再组成四个真实入口。OpenJPEG/OpenJPH 仅作固定版本参考或独立 CPU oracle；最终熵编解码与变换在 GPU。可逆重建保持规定表示精确；不可逆编码按 quality/量化/PSNR 参数及实际重建效果验收，不要求合法压缩码流逐字节相同。组件完成不提前签发含缺失模式的整例资格。

允许合理差异会减少厂商细节复刻的工作。progressive、GPU 编码、MQ/HT 和 NLT3 仍有实际研发量，不据此把原 32–61 工程人周的完整范围承诺为短期全部完成。近期交付以第一批完整入口为准。

## 6. 日志、主表和验收器

每个 profile 记录：`actual_backend`、`comparison_mode`、`algorithm/output_configuration`、`accepted_differences`、`measured_error`、完整/缺失 cases、原生/CPU/GPU 证据、源/二进制/SDK/输入哈希与失败恢复条件。原始严格失败不改写；新 profile 另签复合验收。

更新顺序为：实验封存 → 本方案与主计划逐步记录 → 独立复核 → 固定资格先提交 Git → 发布 `samples.yaml`、算子表及详细支持页。数值工具必须拒绝缺失/重复 case、非零 rc、精确文件长度/集合/身份错误和超出 profile 约定的结果。

容差内的扰动是正向检查，超预算数值偏差和错通道/ROI/模式/丢 batch 是反向检查；不要求所有 1 LSB 扰动都被判错。无损数据、位深/通道/尺寸、ROI/padding、错误行为和 GPU 实际执行仍有硬约束。水印、tile/ROI、连通结构等另作局部/语义检查，不能只用全图 SSIM 判断。

首页仍只展示当前支持情况；批次过程与完整日志保留在[逐步记录](reports/image-libraries-progress.md)和[支持日志总表](reports/support-log-index.md)。历史检查点曾发布项目 248/22/369、图像 9/7/10；当前数量见文末实时检查点，新增数只来自已经签发并先提交 Git 的完整入口资格。


<!-- IMAGE_EXECUTION:START -->

## 当前实施检查点

更新时间：2026-11-13T07:45:42.750764+00:00。26入口当前14通过/8部分/4失败。

I3：IMG-02：第一次冷检出在运行GPU前遇到记录器路径类型错误：__file__字符串被当Path读取suffix；失败已完整封存。已规范为Path，保持算法/输入/门槛不变，重新固定提交执行。

证据：`migration/reports/image-watershed-completion-cold.json`

完整逐步事件见主计划和 `migration/reports/image-libraries-progress.md`。

<!-- IMAGE_EXECUTION:END -->
