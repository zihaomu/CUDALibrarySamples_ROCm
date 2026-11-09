# cuEST/python_examples/4_exchange_correlation/nonlocal_xc_gradient::run.py

**FAILED / L0**

Python 原始入口依赖 cuest.bindings, numpy, argparse, pathlib, sys, helpers.cuda_utils, helpers.utilities, helpers.parsers, helpers.grid_utils；锁定 AMD 环境中的 import 资格检查未通过，尚无保留该例 API/算法的 AMD Python 改写。安装 CPU 包不能充作 GPU 迁移。 日志： in _gcd_import   File "<frozen importlib._bootstrap>", line 1360, in _find_and_load   File "<frozen importlib._bootstrap>", line 1310, in _find_and_load_unlocked   File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed   File "<frozen importlib._bootstrap>", line 1395, in _gcd_import   File "<frozen importlib._bootstrap>", line 1360, in _find_and_load   File "<frozen importlib._bootstrap>", line 1324, in _find_and_load_unlocked ModuleNotFoundError: No module named 'cuest'

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuEST/python_examples/4_exchange_correlation/nonlocal_xc_gradient/run.py](../../../../../../cuEST/python_examples/4_exchange_correlation/nonlocal_xc_gradient/run.py) |
| 实际库 / 后端 | — / — |
| 候选路线 | unresolved |
| 代码 | 无实现 |
| required cases | 0/2 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `9e26538bb631681bb330088683282e71d3b16ade8bbf1ff6c00f6ffdde68885a` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`UNIMPLEMENTED_BINDING`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T084354.110802Z/languages/cuEST_python_examples_4_exchange_correlation_nonlocal_xc_gradient_run.py](../../../../../reports/evidence/20261109T084354.110802Z/languages/cuEST_python_examples_4_exchange_correlation_nonlocal_xc_gradient_run.py)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuEST_python_examples_4_exchange_correlation_nonlocal_xc_gradient_run.py](../../../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuEST_python_examples_4_exchange_correlation_nonlocal_xc_gradient_run.py)
