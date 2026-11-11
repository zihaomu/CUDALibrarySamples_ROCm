# cuDSS/nvfortran/dense_matrix_helpers::dense_matrix_helpers.cuf

**PARTIAL / L3**

R9候选实现已完成构建并进入独立CPU/native CUDA及原始合同验收；尚未签发复合资格，不计整例通过。历史原生API自动移植失败保留。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/nvfortran/dense_matrix_helpers/dense_matrix_helpers.cuf](../../../../../cuDSS/nvfortran/dense_matrix_helpers/dense_matrix_helpers.cuf) |
| 实际库 / 后端 | Project host matrix-descriptor C ABI + HIP device storage/pointer tables / Project HIP runtime adapter |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/nvfortran/dense_matrix_helpers/dense_matrix_helpers.cuf](../../../../../rocm/ported/cuDSS/nvfortran/dense_matrix_helpers/dense_matrix_helpers.cuf) |
| required cases | 1/5 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `0ad5c2bca1694aa127d1c26465bdd73030cab151ccf0e3d5c67cb825e267d0d3` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite-R9/current-build`, `rewrite-R9/frozen-inputs-and-original-contract`, `rewrite-R9/CPU-and-native-CUDA`, `rewrite-R9/negative-and-runtime`, `rewrite-R9/independent-review-and-qualification`。

实现方式：`UNIMPLEMENTED_BINDING`。

恢复/扩展条件：完成当前源码完整原始合同、实际语言/CLI、独立CPU/native CUDA、故障及边界检查和固定提交独立复审后再签发资格。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T084354.110802Z/languages/cuDSS_nvfortran_dense_matrix_helpers_dense_matrix_helpers.cuf](../../../../reports/evidence/20261109T084354.110802Z/languages/cuDSS_nvfortran_dense_matrix_helpers_dense_matrix_helpers.cuf)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_nvfortran_dense_matrix_helpers_dense_matrix_helpers.cuf](../../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/cuDSS_nvfortran_dense_matrix_helpers_dense_matrix_helpers.cuf)
- [migration/reports/rewrite-R9.md](../../../../reports/rewrite-R9.md)
