# C3 Canny：两种语言的完整实现与差异

实际后端为项目 HIP Sobel3、每点最大梯度通道选择、整数 L2、NMS 和 GPU 并查集滞后连接。C++ 使用 OpenCV 读取/写入图片和执行原例两组 CPU 比较；Python 使用 ROCm Torch/C ABI 调用相同 GPU 实现。CPU 不计算生产 Canny mask。

本实现采用明确的**经典 8 连接强种子滞后**：弱边缘为 `NMS > low`，强边缘为 `NMS > high`；只保留包含强种子的完整弱边缘连通分量。[冻结合同](../rewrite/canny-color-profile.json)在实现和新增输入执行前确定。它是 `ALGORITHM_VARIANT`，不承诺 NPP 内部 mask 逐点兼容。

| 验收项 | 实测与日志 |
| --- | --- |
| 22组完整 mask | [独立CPU/native](canny-color-validation.json)：C ABI pitched、GPU tensor 与 NumPy API 全像素、padding 精确；包括等亮度彩色边缘、强弱连接、边界、噪声、阈值和小尺寸 |
| C++/Python完整原例 | [10次完整文件流程](canny-color-originals-validation.json)：各5图，保留1次预热/10次测量、灰度 Canny 和三通道分开 Canny/OR 比较、原始3 PNG文件名 |
| 原始CUDA C++ | [原例三PNG验收](canny-color-original-cuda-validation.json)：未修改源码在5090成功，NPP mask与独立native API对照精确一致；CUDA Python依赖缺Torch保持[BLOCKED](canny-color-original-cuda-python.json) |
| stream/类型/错误 | [55项](canny-color-runtime-validation.json)：独立CPU复核完整输入输出、实际ABI码与异常类型、两stream、并发实例、转换及调用后存储 |
| 真实C++类 | [12项](canny-color-cpp-runtime-validation.json)：非连续host ROI、8项构造/尺寸/type/阈值错误、恢复调用及独立实例并发；4个完整mask独立检查 |
| CLI与无设备 | [10项](canny-color-cli-validation.json)：默认image.jpg、缺失/损坏图片、输出路径冲突和无GPU；检查具体诊断，不能把loader错误当预期失败 |
| GPU执行 | [trace](canny-color-trace-validation.json)：两个修改输入的完整Sobel/NMS/初始化/并查集/强种子/输出流水线，重复hook/compress及实际收敛 |
| 验收器 | [39项正反向](canny-color-checks.json)：允许明确native算法差异，严格拒绝错误像素/布局/padding、尾字节、丢结果、失败rc、错误ABI/异常和错误PNG/循环 |
| 复现与资格 | [冷重放](canny-color-cold.json)、[三项独立复审](canny-color-review.json)、[完整资格](canny-color-qualification.json) |

22组中有18组最终 mask与NPP精确一致。原始800×600 Teapot上，项目保留7443个边缘像素，NPP为11771个，IoU为0.6323167；4328个差异全部为NPP额外保留的像素，其中3905个在项目弱边缘集合内、但不属于含强种子的分量，423个在弱阈值或以下；没有丢失项目定义的强种子，也没有新增NPP以外的边缘。孤立弱阶跃、高强阈值和零阈值也有明确区别，完整内部/边界计数保留，不能仅用全图差异百分比掩盖。

另一次[独立局部模型调查](canny-color-local-research.json)发现，直接使用C1局部阈值假设在C3原图上有6704个差异，且高/零阈值存在差异。因此此处保留经过几何效果验证的经典规则，不复用C1三个外圈像素的结论。高阈值超过所有梯度时，本实现正确返回空强种子结果；灰度近似不变的纯颜色边缘仍能保留。

从仓库根目录，先在宿主安装已有OpenCV开发包所对应的私有prefix：

```bash
python3 tools/moat/image_opencv_setup.py
```

再进入项目固定的ROCm 10.1 foundation和允许的GPU，在其中运行：

```bash
python3 tools/moat/canny_plus_environment.py
export PYTHONPATH="$PWD/build/image-gpu-site:$PWD/rocm/python"
python3 tools/moat/canny_color_replay_fixtures.py
python3 tools/moat/canny_color_build.py
python3 tools/moat/canny_color_run.py
python3 tools/moat/canny_color_run.py --originals
```

单例C++入口的路径见[build.json](canny-color-build.json)的 `binary` 字段；Python入口为 `rocm/ported/NPP/nppCanny/npp_canny_simple.py image.jpg`。库默认 `build/image/libimage_canny_color.so`，可用 `MIGRATION_IMAGE_COLOR_LIBRARY` 指定。C++对象拥有缓存buffer，单个实例按顺序调用；并发使用独立实例。Python调用方workspace由每次调用持有。接口限制尺寸至32768、阈值0–32767，按实际冻结cases和gfx1201/Linux范围声明支持。

PNG和计时均来自真实原例流程；计时用于完整性检查，未签发跨设备或CPU/GPU速度比较。所有旧失败和严格vendor比较记录保留，原始CUDA源文件未修改。
