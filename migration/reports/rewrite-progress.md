# MOAT 重写实时进展

更新时间：2026-11-10T08:25:07.390949+00:00。样例支持结论仍以 samples.yaml 为准。

| 批次 / 样例 | AMD 已运行 / CPU通过 | CUDA 已运行 / CPU通过 | 当前验收结论 |
| --- | ---: | ---: | --- |
| R1 / `gemm3m` | 6/6 / 6/6 | 6/6 / 6/6 | [数值复核中；尚未签发整例资格](evidence/rewrite/R1/gemm3m_boundary/20261110T082058.884767Z-R1-cpu-validation-39ae63f6d9/summary.md) |
| R1 / `herk3m` | 6/6 / 6/6 | 6/6 / 6/6 | [数值复核中；尚未签发整例资格](evidence/rewrite/R1/herk3m_boundary/20261110T082103.350579Z-R1-cpu-validation-33817661a4/summary.md) |
| R1 / `syrk3m` | 6/6 / 6/6 | 6/6 / 6/6 | [数值复核中；尚未签发整例资格](evidence/rewrite/R1/syrk3m_boundary/20261110T082107.870628Z-R1-cpu-validation-265f0efbf1/summary.md) |
| R1 / `planar` | 7/7 / 7/7 | 7/7 / 7/7 | [数值复核中；尚未签发整例资格](evidence/rewrite/R1/planar_half-max/20261110T082130.737246Z-R1-cpu-validation-53e6ba5242/summary.md) |
| R1 / `igemm` | 6/6 / 6/6 | 6/6 / 6/6 | [数值复核中；尚未签发整例资格](evidence/rewrite/R1/igemm_boundary/20261110T082116.664321Z-R1-cpu-validation-e5642c7274/summary.md) |
| R2 / `lu` | 7/7 / 7/7 | 7/7 / 7/7 | [数值复核中；尚未签发整例资格](evidence/rewrite/R2/lu_wave-stress/20261110T082131.467484Z-R2-cpu-validation-cb72c0f2b4/summary.md) |
| R2 / `posv` | 7/7 / 7/7 | 7/7 / 7/7 | [数值复核中；尚未签发整例资格](evidence/rewrite/R2/posv_nonspd-second-minor/20261110T082132.194334Z-R2-cpu-validation-4d4d268174/summary.md) |
| R2 / `trsm` | 6/6 / 6/6 | 6/6 / 6/6 | [数值复核中；尚未签发整例资格](evidence/rewrite/R2/trsm_boundary/20261110T082130.009713Z-R2-cpu-validation-fb8c7b961b/summary.md) |

反向检查：27/27；原生与兼容 CUDA 数学对照分别登记。

当前全项目状态：211 PASSED、402 FAILED、24 PARTIAL、2 UNSUPPORTED。

日志：[实验事件索引](rewrite-experiments.jsonl)；[AMD运行](rewrite-first-rocm.json)；[独立CPU验收](rewrite-first-rocm-validation.json)；[CUDA运行](rewrite-first-cuda.json)。

待完成：提交固定源码后的独立审查、必要原生 SDK 合同复核、反向检查与支持资格签发。
