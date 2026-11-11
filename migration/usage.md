# 构建与复现

以下命令从仓库根目录执行。每个入口的输入、构建方式、运行参数和正确性检查见[支持方式与验证记录](reports/support-log-index.md)。


先核对物理 GPU 占用及共享预约；**HIP ordinal 2 对应物理 GPU0**，ordinal 3 对应物理 GPU1。项目 `device_guard.py` 按 PCI 地址校验；物理 GPU3 排除计算，预约卡也会拒绝。历史使用错误 ordinal 的结果已标记，不能用于验收。

```bash
HIP_VISIBLE_DEVICES=2 tools/migration/run_rocm.sh
python3 tools/migration/compare.py
python3 tools/migration/render.py
```

M1 的独立 CMake/CTest（在锁定 ROCm 10.1.0 容器中，并先运行 guard）：

```bash
python tools/migration/device_guard.py
cmake -S rocm -B build/rocm -DCMAKE_BUILD_TYPE=Release
cmake --build build/rocm -j2
ctest --test-dir build/rocm --output-on-failure
```

原始 profile 批量构建：`bulk_run.py --families cuBLAS cuSPARSE ...`；先在锁定容器中运行 `bootstrap_sdk.py` 建项目 overlay。hipCOMP/hipTensor 的锁定源码重建使用 `bash tools/migration/build_optional.sh`。`python3 tools/migration/restore_observations.py` 从归档恢复 CUDA 输出观测/fixture 适配副本，原始 CUDA 树保持不变。每例复现链接在库级表中的“详情”；命令、原始日志、source/fixture hash 和环境随证据保存。[最终源码与 fixture 身份](source-tree.json) 包含可恢复的内容寻址源码；大输出保留于 artifacts，输入生成方法/hash 在报告中。


[返回项目首页](../README.md) · [环境锁](environments/project.lock.json) · [最终源码与 fixture 身份](source-tree.json)
