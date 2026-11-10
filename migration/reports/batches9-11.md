# B9–B11 实施、支持方式与逐例日志

更新时间：2026-11-10T04:50:52.366619+00:00。19 个计划目标。只按完整登记范围及实测证据更新支持状态；缺口保留 PARTIAL/FAILED/BLOCKED。

**本轮 146 个case通过AMD／独立CPU／同输入CUDA；10个整例支持、9个部分支持。** 全项目202 PASSED、13 PARTIAL、422 FAILED、2 UNSUPPORTED。

| 批次 | 原始样例 / 详细状态 | 实际路线 | 当前结果 | 验收 / 日志 |
| --- | --- | --- | --- | --- |
| B9 | [nvCOMP/examples/low_level_quickstart_example.cpp](../sample-reports/nvCOMP/examples/low_level_quickstart_example.cpp.md) | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter | PASSED | [验收](batches9_11-validation.json) |
| B9 | [nvCOMP/examples/high_level_quickstart_example.cpp](../sample-reports/nvCOMP/examples/high_level_quickstart_example.cpp.md) | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter | PASSED | [验收](batches9_11-validation.json) |
| B9 | [nvCOMP/examples/lz4_cpu_compression.cu](../sample-reports/nvCOMP/examples/lz4_cpu_compression.cu.md) | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter | PASSED | [验收](batches9_11-validation.json) |
| B9 | [nvCOMP/examples/lz4_cpu_decompression.cu](../sample-reports/nvCOMP/examples/lz4_cpu_decompression.cu.md) | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter | PASSED | [验收](batches9_11-validation.json) |
| B9 | [nvCOMP/examples/snappy_cpu_compression.cu](../sample-reports/nvCOMP/examples/snappy_cpu_compression.cu.md) | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter | PASSED | [验收](batches9_11-validation.json) |
| B9 | [nvCOMP/examples/snappy_cpu_decompression.cu](../sample-reports/nvCOMP/examples/snappy_cpu_decompression.cu.md) | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter | PASSED | [验收](batches9_11-validation.json) |
| B9 | [nvCOMP/benchmarks/benchmark_lz4_chunked.cu](../sample-reports/nvCOMP/benchmarks/benchmark_lz4_chunked.cu.md) | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter | PARTIAL | [验收](batches9_11-validation.json) |
| B9 | [nvCOMP/benchmarks/benchmark_snappy_chunked.cu](../sample-reports/nvCOMP/benchmarks/benchmark_snappy_chunked.cu.md) | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter | PARTIAL | [验收](batches9_11-validation.json) |
| B10 | [nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp](../sample-reports/nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp.md) | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode | PARTIAL | [验收](batches9_11-validation.json) |
| B10 | [nvJPEG/nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp](../sample-reports/nvJPEG/nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp.md) | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode | PARTIAL | [验收](batches9_11-validation.json) |
| B10 | [nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp](../sample-reports/nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp.md) | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode | PARTIAL | [验收](batches9_11-validation.json) |
| B10 | [nvJPEG/Image-Resize/imageResize.cpp](../sample-reports/nvJPEG/Image-Resize/imageResize.cpp.md) | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode | PARTIAL | [验收](batches9_11-validation.json) |
| B10 | [nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp](../sample-reports/nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp.md) | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode | PARTIAL | [验收](batches9_11-validation.json) |
| B10 | [nvJPEG/nvJPEG-Decoder/tests/test_decoder.py](../sample-reports/nvJPEG/nvJPEG-Decoder/tests/test_decoder.py.md) | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode | PARTIAL | [验收](batches9_11-validation.json) |
| B11 | [cuDSS/simple_batch/simple_batch.cpp](../sample-reports/cuDSS/simple_batch/simple_batch.cpp.md) | CPU sparse symbolic/matching + rocSOLVER CSRRF LU / HIP CSR pivot LU and GPU query adapter | PASSED | [验收](batches9_11-validation.json) |
| B11 | [cuDSS/simple_uniform_batch/simple_uniform_batch.cpp](../sample-reports/cuDSS/simple_uniform_batch/simple_uniform_batch.cpp.md) | CPU sparse symbolic/matching + rocSOLVER CSRRF LU / HIP CSR pivot LU and GPU query adapter | PASSED | [验收](batches9_11-validation.json) |
| B11 | [cuDSS/simple_reordering_phase/simple_reordering_phase.cpp](../sample-reports/cuDSS/simple_reordering_phase/simple_reordering_phase.cpp.md) | CPU sparse symbolic/matching + rocSOLVER CSRRF LU / HIP CSR pivot LU and GPU query adapter | PASSED | [验收](batches9_11-validation.json) |
| B11 | [cuDSS/simple_residual/simple_residual.cpp](../sample-reports/cuDSS/simple_residual/simple_residual.cpp.md) | CPU sparse symbolic/matching + rocSOLVER CSRRF LU / HIP CSR pivot LU and GPU query adapter | PASSED | [验收](batches9_11-validation.json) |
| B11 | [cuDSS/simple_get_set/simple_get_set.cpp](../sample-reports/cuDSS/simple_get_set/simple_get_set.cpp.md) | CPU sparse symbolic/matching + rocSOLVER CSRRF LU / HIP CSR pivot LU and GPU query adapter | PARTIAL | [验收](batches9_11-validation.json) |

B9：LZ4/Snappy原生batch，CPU↔GPU与hipCOMP↔nvCOMP双向GPU互解；每chunk大小/status、34个manager场景、100个RAW buffer、GPU CRC32C/独立CPU检查。2个benchmark只验证codec核心和基础文件/iteration CLI，完整NVBENCH框架仍PARTIAL。native manager容器各后端自用，不宣称HLIF二进制头跨厂商兼容；跨库使用标准RAW block。

B10：12张原始图全遍历，10张使用rocJPEG硬件，2张progressive明确走libjpeg CPU fallback；9种布局、1/2/4/8缩放、RGB ROI、native batch、多实例、Lanczos-3/alpha-plus水印、文件/退出码及原始10项Python集成测试。奇数尺寸在保持MCU网格的SOF padding视图上硬件解码后GPU裁回原尺寸，避免未定义chroma边界；对齐pitch并在GPU压紧。硬件RGB按CPU FASTUPSAMPLE参考逐像素验收，不与fancy上采样混淆。GPU progressive、原例多实例自动调度/decoupled pipeline/部分backend控制未等价，保持PARTIAL；CPU编码不声称AMDGPU encoder支持。

B11：原始batch5×5+6×6、uniform5×5、analysis-only、GENERAL1000×1000/2RHS与SYMMETRIC类型保留。CPU稀疏符号/最大乘积matching，GPU CSR LU/原始大例rocSOLVER CSRRF LU；原始1000例采用实际稀疏填充，未转dense。小例按分量为潜在pivot预留CSR fill，性能未资格化；原始大例固定pivot，不外推任意大规模动态pivot矩阵。singular案例AMD报告拒绝，CUDA默认可能扰动1×1 pivot：通过真实NPIVOTS查询记录，绝不将其当成原始奇异方程有效解。get_set仅验收项目真实配置与查询子集：完整vendor超级面板/16项内存估计/原始顺序DIAG等仍PARTIAL。

原生能力门槛日志、固定环境与CPU依赖版本见 [CPU codecs](../environments/batches9_11-cpu-codecs.json)、[CUDA SDK](../environments/batches9_11-cuda-sdk.json)。数值/逐字节/逐像素及CLI记录见 [验收JSON](batches9_11-validation.json)；所有原始日志在逐例详情与支持日志索引中。

验证加固：19个入口各2次输出错误，共38次；另9次status/CRC/跨库输入/ROI/配置/GPU执行/奇异扰动语义错误均被拒绝。23项真实文件CLI/不支持功能返回码检查通过。见 [故障注入](batches9_11-negative.json)、[CLI检查](batches9_11-runtime-checks.json)、[跨库RAW流来源与SHA256](b9-cross-interop-inputs.json)。逐case outputs-manifest.json记录全部bin/raw/BMP/JPEG输出SHA256；大文件留本地并按命令重建。

复现（仓库根目录；先按环境锁构建项目依赖）：

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches9_11_run.py b9 b10 b11 --timeout 600
python3 tools/migration/package_batches9_11_cuda.py
# 将build/batches9_11-cuda.tar解到CUDA对照机的项目根目录
# CUDA_VISIBLE_DEVICES=0 python3 tools/migration/batches9_11_run.py b9 b10 b11 --backend cuda --timeout 600
python3 tools/migration/collect_batches9_11_cuda.py b9 b10 b11
OPENBLAS_NUM_THREADS=1 python3 tools/migration/batches9_11_validate.py b9 b10 b11 --qualify
OPENBLAS_NUM_THREADS=1 python3 tools/migration/batches9_11_negative.py
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches9_11_runtime_checks.py
```

跨库RAW fixture来自两端先行original运行，固定来源在JSON中；首次缺fixture时先双端运行：original仍产出，cross案例应报告失败；收集两端original流后固定来源与SHA256，再重跑完整登记case。新fixture必须更新来源JSON并重新验收，不能沿用旧资格。

[主清单](../samples.yaml) · [完整支持与日志索引](support-log-index.md)。原始输入/输出、CPU codec/像素/稀疏参考与 CUDA 结果分开记录；兼容适配、CPU fallback 与原生 API 分开标注。
