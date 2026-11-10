# nvJPEG/nvJPEG-Decoder/tests::test_decoder.py

**PARTIAL / L4**

使用 rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode；7 个预登记case通过独立CPU与同输入CUDA。锁定rocJPEG的HYBRID创建返回-12；原始12图中2张progressive由明确标注的libjpeg CPU fallback解码。GPU格式/ROI/缩放/Lanczos/水印和真实CLI已验证，CPU编码不声称AMDGPU JPEG encoder支持。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvJPEG/nvJPEG-Decoder/tests/test_decoder.py](../../../../../nvJPEG/nvJPEG-Decoder/tests/test_decoder.py) |
| 实际库 / 后端 | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode / rocJPEG/HIP runtime + libjpeg-turbo |
| 候选路线 | rocJPEG (decode only), RPP |
| 代码 | [rocm/ported/nvJPEG/nvJPEG-Decoder/tests/test_decoder.py](../../../../../rocm/ported/nvJPEG/nvJPEG-Decoder/tests/test_decoder.py) |
| required cases | 7/8 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `b430c3b46f5698b0e54aa4b23ed80c165371f4fdc02d132c6d75a7701264ca33` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches9_11/original-corpus`, `batches9_11/formats-scale`, `batches9_11/roi-boundary`, `batches9_11/batch-multi-instance`, `batches9_11/invalid-cli`, `batches9_11/postprocess`, `batches9_11/python-integration`, `batches9_11/native-progressive-GPU-backend`。

实现方式：`HYBRID_CPU_GPU`。

恢复/扩展条件：缺失范围：native-progressive-GPU-backend；需要真实后端/完整harness并重做验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches9_11_run.py b10
OPENBLAS_NUM_THREADS=1 python3 tools/migration/batches9_11_validate.py b10 --qualify
```

- [migration/reports/evidence/20261109T084354.110802Z/languages/nvJPEG_nvJPEG-Decoder_tests_test_decoder.py](../../../../reports/evidence/20261109T084354.110802Z/languages/nvJPEG_nvJPEG-Decoder_tests_test_decoder.py)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/nvJPEG_nvJPEG-Decoder_tests_test_decoder.py](../../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/nvJPEG_nvJPEG-Decoder_tests_test_decoder.py)
- [migration/reports/evidence/20261110T043132.627099Z/batches9_11-rocm/nvJPEG_nvJPEG-Decoder_tests_test_decoder.py](../../../../reports/evidence/20261110T043132.627099Z/batches9_11-rocm/nvJPEG_nvJPEG-Decoder_tests_test_decoder.py)
- [migration/reports/batches9_11-validation.json](../../../../reports/batches9_11-validation.json)
- [migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvJPEG_nvJPEG-Decoder_tests_test_decoder.py](../../../../reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvJPEG_nvJPEG-Decoder_tests_test_decoder.py)
