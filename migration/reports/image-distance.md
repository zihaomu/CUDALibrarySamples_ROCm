# NPP+ signed / unsigned EDT 实现与实验记录

状态：**已签发完整 NPP+ 原例资格**。当前项目249通过，图像10/26通过；四模块其它缺口继续按计划实施。

原始入口：`NPP+/distanceTransform::unsignedAndSignedDistanceTransformNPPPlus.cpp`。实际后端为项目 HIP；CPU 负责文件、标量和调度，不承担生产距离/Voronoi/可视化计算。

## 定义与兼容范围

[30组完整输入和固定合同](../rewrite/image-distance-profile.json)覆盖原始五张图、uint8 unsigned、float32/float64 signed、圆图原例预处理、子像素阈值、同距、反相、常量、单像素/行/列、独立噪声、完整padding。数学定义详见[合同说明](../image-signed-edt-contract.md)。

Unsigned 为零像素中心的精确欧氏最近距离；signed 为水平/垂直线性阈值交点与恰零像素中心构成的点集距离，符号来自有效输入场。signed 使用GPU紧凑site集和完整二维平方距离搜索后按最小site ID破同距，避免分离搜索中间舍入提前丢弃全局同距候选。恰零像素的唯一零距离site直接输出，避免常量图的二次搜索。原始输入转换、site生成、距离、Voronoi和16u可视化均在GPU。

项目采用 `ALGORITHM_VARIANT`，不声明复制NPP+ PBA反走样算法或Voronoi编号。输出绝对short2为所选子像素site向下取整的anchor，相对short2为像素减anchor，实际距离仍使用子像素坐标。距离对独立CPU预算固定为 `atol=2e-11, rtol=1e-12`，零/符号/无穷位置严格；site ID、坐标、索引、相对值、可视化和padding检查精确。

无site返回相应符号无穷和-32768坐标sentinel。可视化保持原例unsigned截断、signed加32700后截断，并明确定义端点饱和；不继承越界浮点转无符号整数的未定义行为。

## 当前证据

| 范围 | 当前结果与证据 |
| --- | --- |
| 原生CUDA完整样例 | 5090未改源码实际build/run，五原图与12输出保存。[执行](image-I2-distance-native-original.json) |
| 原生符号/类型/Voronoi研究 | 全文件读取，记录cutoff、符号、值域和绝对/相对坐标。[研究](image-I2-distance-native-research.json) |
| 数学变体与native | 圆图maxAbs约29.9444，Lith约0.86533；这是不同算法的完整观测，不作为拟合容差。[独立点集研究](image-I2-distance-definition-research.json) |
| 固定输入 | 30组、五原图12原始产品文件；首次GPU数值执行前把workspace与实现调整为完整site搜索，原数学定义和数值预算不变。[合同](image-distance-contracts.json) |
| HIP共享库 | ABI1，160字节descriptor，独立输出和workspace；实际ROCm10.1/gfx1201构建。[构建](image-distance-build.json) |
| GPU全量结果 | 30组完整实际执行；独立cKDTree参考核对所有距离/sites/索引/可视化、符号与Lipschitz、padding。[GPU](image-distance-all.json)、[CPU](image-distance-all-validation.json) |
| 独立CPU解析检查 | 子像素直线、同距编号、无site/无穷、零、circle remap、有限端点差值溢出、nonfinite拒绝。[检查](image-distance-model-checks.json) |
| 完整C++入口 | 五图12文件；固定默认/显式/完整规模变化/零level常量四流程，共48产品文件；GPU site审计单独保存。[合同](image-distance-original-contracts.json)、[构建](image-distance-frontend-build.json)、[执行](image-distance-originals.json)、[48文件独立CPU](image-distance-originals-validation.json) |

最初device math普通符号无法链接的构建失败保留，改用HIP编译器内建数学操作后构建成功。CPU解析测试曾误将恰零site ID写成n+pixel而非合同的2n+pixel，修正测试期望后通过，生产模型未修改；全部失败和后续运行见[逐步记录](image-libraries-progress.md)及[实验索引](rewrite-experiments.jsonl)。

四完整C++流程/48文件及全部site审计已独立CPU通过。已完成19CLI、69参数/query、27默认/复用/并发/可选输出/外设备与销毁流/极值/次正规/32768行列、31项全trace检查及34反例；原生当前五图12输出及实际SDK/GPU receipt绑定和全量差异重算通过。旧NPP EDT6组/NCC8组回归与12子记录冷检出已通过；尚需最终固定提交复审和先Git后发布。

[CLI](image-distance-cli-validation.json) · [参数](image-distance-arguments-validation.json) · [状态](image-distance-states-validation.json) · [trace](image-distance-trace-validation.json) · [34反例](image-distance-checks.json) · [当前原生绑定与全量比较](image-distance-native-validation.json)

预审发现NaN可冒充无穷、fixture未核冻结manifest两项缺口，现均修复并由原reviewer复核闭合；34项反例含语义不变的1→2输入及配套回读/receipt伪造，预算内扰动仍接受。销毁流的观察器查询会把709留在HIP线程错误缓存，已记录并用hipGetLastError清除后继续Torch操作；未改变API原始709返回值，后续全部正向状态通过。旧NCC常量图/模板预期返回1表示歧义拒绝，原输出/数值/PGM仍须完整通过，不能把该历史合同误报成算法失败。

I9特别跟踪：旧NPP unsigned EDT的既有PASSED资格覆盖原尺寸数值/Voronoi/截断；其legacy入口输出观察器bin，而原CUDA入口写六RAW（并有原例Voronoi文件长度错误）。新26入口完整文件目标结束前须补原始文件适配并独立验收，不能仅凭数学回归宣布I9完成。组件结果不提前增加整例支持。

## 复现

先在私有CPU环境生成固定输入，再在工作区ROCm10.1 launcher/device guard内构建与执行：

```bash
python3 tools/moat/image_distance_contracts.py
python3 tools/moat/image_distance_original_contracts.py
python3 tools/moat/image_distance_build.py
python3 tools/moat/image_distance_run.py
python3 tools/moat/image_distance_frontend_build.py
python3 tools/moat/image_distance_originals.py
```

独立CPU环境含NumPy2.2.6、SciPy1.18.1，运行 `image_distance_reference.py`、`image_distance_original_reference.py` 和 `image_distance_model_checks.py`。所有GPU像素计算在物理GPU1；未验证性能、wave64和Windows。

原计划2/4ULP是I0前的候选；当前signed定义带子像素插值，首次GPU执行前另行固定绝对/相对数值预算，并严格保留零/符号/无穷及离散字段。该预算不由native差异拟合。当前30组实际GPU/CPU最大绝对误差见 `image-distance-all-validation.json`，与跨算法native差异分开报告。

当前补充验收：100项CPU解析/穷举参考检查、69参数、27状态、19CLI、34核心与23运行/文件验收器正反例全部通过；旧EDT6组及完整NCC8组也通过。30组实际GPU/项目CPU距离最大绝对误差为0；与native不同signed定义的差异仍单列。

冷启动复现通过：[12个封存子记录](image-distance-cold.json)，从提交7a4972d28干净检出、三类输入重建、新编译库/完整C++入口，30输入/4流程48RAW/69参数/27状态独立CPU重新核对。资格器和发布器重新计算全部必需证据、完整frontend编译闭包，发布前要求资格先进入Git。当前仍不提前增加支持数。

最终资格24项复合门槛全部通过，三scope批准提交`76afb83f64178d974cedd7b62260b2d27dcaa728`；资格与全部引用seal首次发布于`67a4bba604b96aa09d28e9349a42b7d0005256d9`，随后真实publisher才修改支持主表。[资格](image-distance-qualification.json) · [复审](image-distance-review.json) · [数据CAS门禁](image-distance-review-gate-checks.json) · [实际发布拒绝/主表不变检查](image-distance-publication-guards.json)。这完成I2新增5原入口的范围；I3与codec/I9仍未完成，旧NPP六RAW文件入口仍须补齐。
