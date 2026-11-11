# 等值连通域与 GPU 标签压缩

状态：实现、完整数值/运行验收及干净检出重放通过；复审要求的 stream/验收器修复已实施并重验，更新后的干净检出和最终复核进行中。尚未据此增加首页通过数。

两个原始入口分别为 NPP 与 NPP+ 的 `batchedLabelMarkersAndCompression`。AMD 实现采用项目 HIP 八连接并查集与分层 GPU 前缀扫描，覆盖输入的所有字节值，包含零值区域。CPU 只读取收敛标量和最终分量数，以及文件 IO；标签生成和压缩都在 GPU。

## 功能与约定

- 原始五张图片完整处理：512×512 两张、509×335、1024×683、1280×720。PCB_METAL 有 11 种值，按相同值分区，不先转成二值图。
- 每张图片分别生成原标签和紧凑标签，然后按异构尺寸 batch 重算。NPP 默认输出 20 文件；NPP+ 默认输出 15 文件，`CUDA11U1` 编译分支输出 20 文件。
- 保留 `../images/` 默认目录、`-b` 和帮助。项目另提供 `--input-dir`、`--output-dir`；`-b 1..5` 在全部阶段一致生效。原始 CUDA 后半部分硬编码 5 的不完整 batch 问题记录在 profile；非法值明确拒绝。
- 原标签使用分量最小行优先像素位置加一，压缩编号为根位置顺序的 1..K。厂商无语义编号允许双射重映射；真正的分裂或合并不是编号差异。
- C ABI 支持 pitched 输入和输出、显式 stream、独立状态并发及异构 batch。先校验整个 batch，拒绝空指针、大小/步长、分配长度、对齐、设备身份和读写重叠，再启动计算。内部同步一个收敛标量；最终输出仍在调用方 stream 排队，调用方同步后读取或释放。

同值区域与八连接规则依据 [NPP+ 官方过滤函数文档](https://docs.nvidia.com/cuda/nppplus/image_filtering_functions.html)。本项目额外明确编号和错误行为，以便复现。

## 已完成验收

| 范围 | 结果与日志 |
| --- | --- |
| 固定合同/输入 | 27 组：10 个原始入口资产、3×3 回归、单像素/单行/单列、扫描块边界/递归、常量含零、随机多值、斜连、孔洞/边界、长蛇形。[profile](../rewrite/image-ccl-profile.json)、[封存](image-ccl-contracts.json) |
| 完整 GPU 分区 | 27 组的全部原标签、压缩标签、分量数、输入/padding 对独立 OpenCV 精确；小图另以 BFS 交叉核对。[GPU](image-ccl-masks.json)、[CPU](image-ccl-masks-validation.json) |
| 运行语义 | 44 项：由独立冻结的角色/输入/几何/query映射约束实际 ABI/查询返回码、非法缓冲区不修改存储、先校验全部 batch、重复/变化输入、非默认 stream、5 图异构 batch、两个独立并发实例。[GPU](image-ccl-runtime.json)、[CPU](image-ccl-runtime-validation.json) |
| 两真实 C++ 原例 | 三个编译配置各跑 batch 1..5，15 个完整流程共 165 个 raw 输出逐值检查；不使用缩小图片代替原图。[执行](image-ccl-originals.json)、[验收](image-ccl-originals-validation.json) |
| CLI | 三个配置共 39 项：默认目录、帮助、参数/输入/输出错误和合法空设备 mask；检查实际返回码、具体诊断、成功输出全集。[执行](image-ccl-cli.json)、[验收](image-ccl-cli-validation.json) |
| 默认/外设备/销毁 stream | 默认 nullptr 正向完整像素通过；GPU0仅创建外设备流，GPU1拒绝返回101并保留存储；销毁流查询/调用均返回709。全部像素仅GPU1执行。[GPU](image-ccl-streams.json)、[CPU](image-ccl-streams-validation.json) |
| 原生执行预检反例 | 实际runner对失败build、缺binary身份、缺分支三项均先封存拒绝，无远端命令和逐例孤立记录。[检查](image-ccl-native-guard-tests.json) |
| 真实 GPU trace | 27 次 initialize/root_flags/output；53 次 hook/compress、61 次 block_scan、34 次 scan_offsets。时间、grid、PCI 检查均通过，执行物理 GPU1 `0000:23:00.0`。[执行](image-ccl-trace.json)、[验收](image-ccl-trace-validation.json) |
| 干净检出 | 无预先 build，固定提交重新生成27输入并校验profile一致，创建SDK overlay、重编译库/三个原入口；27mask、44运行及15完整流程全部再次CPU通过。[冷重放](image-ccl-cold.json)；此前19子raw与源对象封存；stream与独立角色约束更新后重做冷检出，目标20子记录。 |
| 验收器正反例 | 31 项，增加像素→错误、查询valid/几何重定义、错误→查询、丢源身份四类绕过反例；接受任意 native 标签重编号，拒绝错误分区、压缩、padding、计数、输入、缺例/重复、实际失败码和结构错误。[检查](image-ccl-checks.json) |

## NVIDIA 原生对照与真实差异

[54 次 API 对照](image-ccl-native.json)与[独立分区比较](image-ccl-native-validation.json)已完成。当前 NPP 13.4 工具链及 NPP+ 0.10 私有 SDK 的两个 API 全部运行成功，但部分分区不符合同值八连接定义。例如：

```text
0 2 0
0 2 0
1 0 1
```

正确分区为 4 个：五个零在八邻域连通，两个 2 连通，两个 1 分离。当前两套 NVIDIA API 实测返回 5 个分量；HIP、OpenCV 与 BFS 均为 4 个。逐像素结果保留，不把这个问题视为允许的编号重映射。

原图也存在缺陷：Lena 的独立 CPU 为 552 分量，当前一次 NPP 实测 564、NPP+ 570；全部实际分裂/合并、像素差异及编号记录见比较 JSON。GPU 与 CPU 主验收精确；不声称与错误 native 分区精确兼容。

[三种未改 CUDA 原例](image-ccl-native-originals.json)另以 binary SHA、五张输入 SHA 和独立新工作目录运行；原始文件及数学比较见[完整输出验收](image-ccl-native-originals-validation.json)。“原程序运行成功”和“输出分区正确”分别报告。

## 复现与限制

在项目锁定的 ROCm 10.1 foundation 中使用工作区 launcher/device guard；当前实测为 gfx1201、物理 GPU1。先执行 `python3 tools/migration/bootstrap_sdk.py` 创建项目 SDK overlay，再运行：

```bash
python3 tools/moat/image_ccl_contracts.py
python3 tools/moat/image_ccl_build.py
python3 tools/moat/image_ccl_run.py
python3 tools/moat/image_ccl_run.py --runtime
python3 tools/moat/image_ccl_run.py --trace
python3 tools/moat/image_ccl_originals.py
python3 tools/moat/image_ccl_originals.py --cli
```

独立 CPU 环境为 OpenCV 4.12.0、NumPy 2.2.6；执行 `image_ccl_reference.py` 的 masks/runtime/trace/native/native-originals 分支，以及 `image_ccl_original_reference.py`、`--cli` 与 `image_ccl_checks.py`。CPU 库只作参考，不参与生产分区计算。

尺寸边界为单维 1..32768、像素数不超过 2^28；原始所有尺寸均在范围内。当前没有跨设备性能、wave64 或 Windows 结论。NPP+ 和 NVIDIA SDK 仅保留私有安装及哈希，仓库不分发 vendor payload。

首轮 NPP+ 编译宏、库名/探针 include 顺序错误、额外身份工具的路径初始化错误，复用 native 输出目录导致的严格文件集合失败、并行 git status 与提交锁争用，以及冷 fixture 父目录缺失和收集旧报告错误均已封存。最终使用正确 SDK 配置和独立新目录重试，不删除历史失败。

独立复审发现的缺口均保留修复记录：原生编译返回码汇总/预检初始化、默认流与设备身份、运行验收器角色自定义。当前 `hipStreamGetDevice` 负责默认/外设备/销毁流预检；所有角色与源输入由独立合同约束，错误分支还对已知初始化缓冲区SHA逐项核对。修复后重编译及所有受影响生产/CPU流程重跑；不对旧oracle闭包作豁免。
