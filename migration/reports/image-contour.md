# NPP / NPP+ 轮廓与有序几何实现

状态：**两个原始入口完整验收通过并发布**。固定来源e4fad06b7经三个独立范围批准，复合资格先在666eb8480提交Git，然后发布主表。

[完整资格](image-contour-qualification.json) · [独立复审](image-contour-review.json) · [首次Git发布保护](image-contour-publication-tests.json)

两个原始入口为 `NPP/findContour::findContour.cpp`、`NPP+/findContour::findContourNPPPlus.cpp`。生产计算路线为项目 HIP 等值八连通分区、边界检测、有向像素单元边图、GPU 循环并查集、指针跳跃排序、GPU 前缀扫描和从几何顶点重建图像；CPU 只处理标量、分配、文件与诊断格式化。

## 固定语义与差异

[22 组固定输入与算法合同](../rewrite/image-contour-profile.json)包括两张原始 2048×1024 RAW，常量、单像素/行/列、孔洞/嵌套区域、斜点接触、贴边对象、细线、随机多值和实际大轮廓分支。

最终 mask 使用原生编码：**0 为边界，255 为非边界**。像素在 ROI 内存在不同组件的八邻居时属于边界，ROI 外部不单独产生像素边界。所有像素值包含零均按相同值八连通分区；标签无语义编号可不同，项目紧凑标签从零开始。

几何采用明确的项目表示：有向单位像素单元边，在 ROI 边缘闭合；组件在边的左侧，外轮廓逆时针、孔洞顺时针。点接触的多个闭环仍共享正确的八连通组件。每个闭环从最小 edge ID 开始，所有循环顺序在 GPU 产生。该表示保持完整拓扑和重建语义，**不声明 NPP 专有 packed geometry 结构的二进制兼容**。

重建实际消费 GPU geometry：内部异类组件边的端点映射到相邻同组件像素，完整恢复八邻域边界，包括凹角的斜邻域像素；ROI 外闭合边不单独绘制成像素边界。独立 CPU 用顺序图遍历验证 GPU 并查集/指针跳跃的所有边、顺序、闭环和重建。

原例 NPP 只写三个 RAW 文件；声明的 `OUTPUT_GEOMETRY` 未使用。NPP+ 写四个 RAW 文件，保留其范围选择、bbox/count、排序几何诊断及重建流程；方向图和备用 CPU 路径原本由 `#if 0` 禁用。默认范围为 `[1, component_count)`。多 ID 范围中唯一边界像素数达到 262144 的组件旁路重建/逐点诊断，单 ID 范围强制输出。后端可以提前构造全部几何，不作原厂相同开销或性能承诺。

## 当前证据

| 范围 | 观察 / 结果 |
| --- | --- |
| 两个未改 CUDA 原例 | 5090 build/run 均返回 0，原始输入及三/四文件完整保存。[执行](image-I2-contour-native-originals.json) |
| 原生数学检查 | CPU 正确分区 262 个组件；本次 NPP 273 个、72002 像素分区不同，NPP+ 266 个、13246 像素不同。原生 0 边界位置与其实际标签的 ROI 内八邻域边界对应；不能把原生错误分区当作 ROCm 正确答案。[原始观察](image-I2-contour-native-research.json) |
| CPU 算法定义 | 17 小图的闭环排列与从 geometry 精确重建八邻域 mask 通过。[检查](image-contour-model-check.json) |
| GPU 全部输入 | 22 组全部原标签/紧凑标签/mask、marker 信息、逐 edge/loop/order、输入/padding 和各 range 重建对独立 CPU 精确。[执行](image-contour-all.json)、[CPU](image-contour-all-validation.json) |
| 实际阈值 | 单 ID 输入边界计数262913/262912；多 ID 输入计数3080/262913/262912。确实覆盖262144阈值及单ID强制，初版加框后未超过阈值的构造已在执行前扩大，不更改原阈值。[合同检查](image-contour-large-threshold-contract.json) |
| C ABI | 共享 HIP 库已构建；规模为各维1..32768且像素≤2^26，info容量≥像素数，geometry容量≥4×像素数；仅写实际前缀。ABI2 renderer先独立验证边集合完整、唯一、闭环次序和全部marker统计，再写目标；61项参数/query和26项真实畸形设备数据验收通过。[构建](image-contour-build.json) |
| 两真实 C++ 入口 | 15个默认文件/范围/大轮廓/诊断完整流程、55个实际RAW文件和逐点stdout独立CPU验收通过。[构建](image-contour-frontends-build.json)、[逐次执行](image-contour-originals.json) |

初版小图及各构建证据继续保留；最终资格只使用当前固定 source/profile 及完整输入的最新证明。已完成32项真实CLI、11项默认流/输入变化复用/并发实例/外设备及销毁stream、61项参数/query、26项设备数据合同与17图真实trace（10类关键kernel），58项验收器正反例全部通过。早期ABI1接受缺边几何的真实失败保留，不计支持。干净检出164538d92重新生成全部22输入、新编译ABI2和两个入口，并完成15流程/26设备数据/61参数/11状态合同的独立CPU重验，22子记录全部封存通过。复合验收预检曾只剩最终复审；预审发现CLI绑定、冷流程去重、native完整文件和frontend依赖闭包缺口后均补齐，58项反例已通过。修复后的新冷检出83ea6539及32项CLI实际重跑全部通过；旧冷重放和所有失败保留。最终22项复合门槛均通过，两个完整入口已发布。

[干净检出复现](image-contour-cold.json)

[CLI](image-contour-cli-validation.json) · [状态/stream](image-contour-states-validation.json) · [参数](image-contour-arguments-validation.json) · [设备数据](image-contour-data-errors-validation.json) · [trace](image-contour-trace-validation.json) · [58项反例](image-contour-checks.json) · [ABI1失败](image-contour-legacy-data-error-validation.json)

## 复现

在工作区 ROCm10.1 launcher 和 device guard 内创建项目 SDK overlay，然后执行：

```bash
python3 tools/moat/image_contour_contracts.py
python3 tools/moat/image_contour_build.py
python3 tools/moat/image_contour_run.py
python3 tools/moat/image_contour_frontends_build.py
python3 tools/moat/image_contour_originals.py
```

独立 CPU 环境运行 `image_contour_reference.py`。完整实测 GPU 为 gfx1201 物理GPU1；没有 GPU3、性能、wave64 或 Windows 结论。两张原图、22组输入及全部输出身份、依赖、原始日志见对应封存记录。
