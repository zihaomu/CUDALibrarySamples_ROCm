# nvJPEG/nvJPEG-Decoder/tests::test_decoder.py

**BLOCKED / L0**

Python imports 已通过，但 AMD decoder executable 与完整原始 CLI/GPU 测试前置条件尚未实现；只做 import 资格检查不能推断 GPU 成功。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvJPEG/nvJPEG-Decoder/tests/test_decoder.py](../../../../../nvJPEG/nvJPEG-Decoder/tests/test_decoder.py) |
| 实际库 / 后端 | — / — |
| 候选路线 | rocJPEG (decode only), RPP |
| 代码 | 无实现 |
| required cases | 0/2 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `b430c3b46f5698b0e54aa4b23ed80c165371f4fdc02d132c6d75a7701264ca33` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`UNIMPLEMENTED_BINDING`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T084354.110802Z/languages/nvJPEG_nvJPEG-Decoder_tests_test_decoder.py](../../../../reports/evidence/20261109T084354.110802Z/languages/nvJPEG_nvJPEG-Decoder_tests_test_decoder.py)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/nvJPEG_nvJPEG-Decoder_tests_test_decoder.py](../../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/nvJPEG_nvJPEG-Decoder_tests_test_decoder.py)
