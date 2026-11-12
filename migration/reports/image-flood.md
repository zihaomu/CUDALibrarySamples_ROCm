# 完整 RGB flood fill 实现与实验记录

状态：**实施中，尚未签发整例资格**。项目保持249通过、图像10/26通过。

入口：`NPP+/floodFill::floodFillVariousRegionTypesNPPPlus.cpp`。实际计算为项目 HIP；复用未修改的八连通 GPU union-find 核心。生产 CPU 只负责文件、参数和调度，连接、区域填色、边界、count/bbox/seed 信息全部在 GPU 生成。

## 定义和原例范围

[冻结29输入](../rewrite/image-flood-profile.json)覆盖两张完整原图和全部五分支：精确 seed 颜色、固定原始 seed 的逐通道梯度范围、梯度范围与边界、绝对范围、绝对范围与边界。C3 uint8，所有通道同时满足含端点区间；梯度上下限饱和至0..255。连接为经典八连通，边界为选中区域的内八邻域边界，包含图像外框；填色前判断所有像素。seed不满足绝对范围时返回空区域。

独立返回完整区域mask；metadata为inclusive xmin/ymin/xmax/ymax、区域像素count和原始RGB seed。保留原例把width/height表示为右/下坐标的含义。边界像素计入原区域count。颜色已经等于填充值或边界色也不能省略mask和metadata验证。

C ABI1，descriptor160字节，支持byte pitch、相同pitch的精确原地alias、禁用可选mask，以及独立workspace。拒绝部分重叠、错设备/stream、溢出、错误实际分配范围。无wave64/Windows或性能资格。

## 当前证据

| 项目 | 结果和日志 |
| --- | --- |
| 原始源码面 | [五入口调查](image-I3-contract-surface.json)；本入口两图、五完整RGB产品和region信息 |
| 29完整输入 | [GPU](image-flood-all.json) · [独立CPU](image-flood-all-validation.json)：完整RGB/mask/metadata/padding全部精确一致 |
| 完整文件入口 | [合同](image-flood-original-contracts.json) · [构建](image-flood-frontend-build.json) · [四流程](image-flood-originals.json) · [CPU](image-flood-originals-validation.json)：默认/显式/完整规模变化/完整规模常量，共20RGB产品及全部实际GPU审计通过 |
| 运行语义 | [72项冻结合同](../rewrite/image-flood-runtime-contract.json) · [实际执行](image-flood-runtime.json) · [独立CPU](image-flood-runtime-validation.json)：全存储before/after、32字节guard、真实hipMalloc16字节、query、alias、复用变化/还原、禁mask、并发与外设备/销毁流通过；新增末行padding交叠与短物理分配9项 |
| 末行padding反例 | [旧库实际错误](image-flood-legacy-padding-failure.json) · [新库同一反例](image-flood-padding-fix-validation.json)：旧库在1×1、pitch4、mask=input+3时改写输入末行padding197→255；新库rc1且全部缓冲保持。旧失败证据独立归档，不用作新库通过证明 |
| CLI/追踪 | [18项CLI与畸形文件独立检查](image-flood-cli-validation.json) · [真实GPU trace](image-flood-trace-validation.json)：五种GPU阶段均有实际dispatch，全部RGB/mask/metadata仍由CPU核对 |
| 验收器反例 | [30项核心读取器检查](image-flood-checks.json) · [30项运行时/CLI/原例读取器检查](image-flood-runtime-checks.json)：均含完整归档重定位正例；拒绝伪造输出、配对hash、buffer/stream/命令及原例产品 |
| 干净检出 | [固定提交重放](image-flood-cold.json)：无预建库的新克隆重建四合同、HIP和C++，29全图、4原例、72运行、18CLI、trace及五独立CPU检查全部通过，36份完整子实验封存；第一次外层容器重入失败另存原始日志 |
| 当前原生NPP+ | [未改五原例执行](image-I3-native-originals.json) · [flood完整比较](image-flood-native-validation.json)：源码/输入/binary/实际SDK/GPU receipt及两输入五完整产品验证；数值差异单列 |
| 历史捆绑文件 | [CPU研究](image-I3-flood-bundled-research.json)，仅为旧vendor文件观察，和新的实际native记录分开 |

## 与原生结果的差异

项目使用首次GPU实现前冻结的经典固定seed八连通定义，对独立CPU的29输入和四完整原例流程精确一致。新5090原生结果和项目在五个原分支分别有380、14、2948、2990、4959个RGB像素不同；包含连接、边界及区域信息差异，不能以平均像素误差代替拓扑验收。

例如精确颜色原图项目/CPU区域267578像素，当前native267198；绝对范围项目/CPU区域321429，native318439。绝对范围实际seed(20,24)的RGB为169/211/232，native region字段记录149/205/229，bbox也不同。上述是当前SDK/实际输入的完整观察，不据此概括所有NPP版本的行为，也不把这些差异拟合成像素容差。所有vendor产品、原始stdout和库身份保留。

GPU图像计算均在物理GPU1；物理GPU0只创建/查询空的外设备stream，未存储图像或运行图像kernel。两实例并发验证使用实际不同流、独立全部地址范围和重叠的API+自身流同步区间。

尚需固定源码独立复审和固定资格发布。完成全部门槛后才把该入口从PARTIAL升级。

## 复现

GPU构建/执行通过项目ROCm10.1 launcher/device guard；CPU生成与参考使用项目隔离CPU环境。

```bash
python3 tools/moat/image_flood_contracts.py
python3 tools/moat/image_flood_build.py
python3 tools/moat/image_flood_run.py
python3 tools/moat/image_flood_original_contracts.py
python3 tools/moat/image_flood_frontend_build.py
python3 tools/moat/image_flood_originals.py
python3 tools/moat/image_flood_runtime_contracts.py
python3 tools/moat/image_flood_runtime.py
python3 tools/moat/image_flood_cli.py
python3 tools/moat/image_flood_trace.py
build/image-cpu-venv/bin/python tools/moat/image_flood_checks.py
build/image-cpu-venv/bin/python tools/moat/image_flood_runtime_checks.py
```

详细命令、环境和原始输出在每项独立experiment目录，实时步骤见[实施记录](image-libraries-progress.md)。CPU参考运行 `image_flood_reference.py`、`image_flood_original_reference.py`、`image_flood_runtime_reference.py`、`image_flood_native_reference.py`。
