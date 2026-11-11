# C1 Canny：实现方式与完整验收

实现使用项目 HIP Sobel3、整数 L2、NMS 和局部阈值 kernel，ROCm Torch 通过项目 C ABI 调用。生产像素计算全部在 GPU；CPU NumPy 仅用于独立验收。

算法定义见 [profile](../rewrite/canny-plus-profile.json)。它是明确登记的算法变体，不承诺 NPP+ 的二进制 ABI。原始 NVIDIA 源文件保持原样，移植入口位于 `rocm/ported/NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py`。

完整原例保留 BGR resize → Torch CHW → torchvision RGB 灰度权重的原顺序、8 个 320×180 至 5120×2880 分辨率、5 次预热和每组 1000 次测量；输出 8 张 PNG 和性能 CSV。CSV 明确标注实际 HIP 后端，计时记录不能作为 AMD/NVIDIA 性能结论。

| 项目 | 实测结果与证据 |
| --- | --- |
| 完整 mask | [31组 CPU验收](canny-plus-validation.json)：GPU输出和独立CPU所有像素、pitch padding 精确一致 |
| 原始文件流程 | [8分辨率验收](canny-plus-original-validation.json)：预处理字节、PNG、CSV、5/1000循环与全部测量记录 |
| NVIDIA 对照 | [31组 native NPP+](canny-plus-native.json)：全部内部mask一致；两个研究用例合计3个外圈像素差异，完整差异计数保留 |
| 原始CUDA Python | [原始脚本环境](canny-plus-original-cuda.json)：5090系统Python无Torch，BLOCKED；真实native API对照单列 |
| 运行语义 | [运行检查](canny-plus-runtime-validation.json)：CPU uint8/float16/32/64、GPU float16/32、非连续、两stream、并发实例、重复和修改输入、非法参数及调用后存储保持 |
| GPU执行 | [原始trace](canny-plus-trace-validation.json)：两次输入变化调用各有Sobel/NMS/阈值三阶段dispatch |
| 验收器 | [24项正反向](canny-plus-checks.json)：接受约定内native差异，拒绝超预算、错像素/padding、错误hash、尾字节、失败rc、丢结果、错误CSV/循环与空trace |

构建和运行使用项目已固定的 ROCm 10.1 foundation。先按工作区设备政策启动该环境，在其中执行：

```bash
python3 tools/moat/canny_plus_environment.py
python3 tools/moat/canny_plus_replay_fixtures.py
python3 tools/moat/canny_plus_build.py
PYTHONPATH=build/image-gpu-site:rocm/python \
  python3 rocm/ported/NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py \
  --input NPP+/cannyEdgeDetectorPython/Teapot.jpg --output build/canny-output
```

共享库默认 `build/image/libimage_canny.so`，可用 `MIGRATION_IMAGE_LIBRARY` 指定。C ABI workspace 由调用方持有，stream 属于调用方；输入/输出/workspace必须是当前设备的不同有效分配。Python 模块自动保留异步 tensor/临时 buffer 的 stream 生命周期。只声明实际验收的 gfx1201/Linux 范围，wave64/Windows 仍待验证。

每份证据目录提供 commands、stdout/stderr、源和输入哈希、observed environment、完整原始输出清单及 seal；大体积原始 `.bin` 留在 artifacts 并由 seal 记录 SHA256/字节数。资格与支持发布见 [qualification](canny-plus-qualification.json)。
