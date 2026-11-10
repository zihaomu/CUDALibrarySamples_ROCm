# MOAT 重写实时进展

更新时间：2026-11-10T07:59:05.553837+00:00。样例支持结论仍以 samples.yaml 为准。

| 批次 / 样例 | AMD 已运行 / CPU通过 | CUDA 已运行 / CPU通过 | 当前验收结论 |
| --- | ---: | ---: | --- |
| R1 / `gemm3m` | 6/6 / 6/6 | 6/6 / 6/6 | [数值复核中；尚未签发整例资格](evidence/rewrite/R1/gemm3m_boundary/20261110T074959.241325Z-R1-cpu-validation-d2451bef2d/summary.md) |
| R1 / `herk3m` | 6/6 / 6/6 | 6/6 / 6/6 | [数值复核中；尚未签发整例资格](evidence/rewrite/R1/herk3m_boundary/20261110T075003.647972Z-R1-cpu-validation-89cb13b049/summary.md) |
| R1 / `syrk3m` | 6/6 / 6/6 | 6/6 / 6/6 | [数值复核中；尚未签发整例资格](evidence/rewrite/R1/syrk3m_boundary/20261110T075008.021313Z-R1-cpu-validation-09883eece8/summary.md) |
| R1 / `planar` | 6/6 / 6/6 | 6/6 / 6/6 | [数值复核中；尚未签发整例资格](evidence/rewrite/R1/planar_boundary/20261110T075012.292163Z-R1-cpu-validation-f09ecb94c9/summary.md) |
| R1 / `igemm` | 6/6 / 6/6 | 6/6 / 6/6 | [数值复核中；尚未签发整例资格](evidence/rewrite/R1/igemm_boundary/20261110T075016.579686Z-R1-cpu-validation-5928d75a5b/summary.md) |
| R2 / `lu` | 6/6 / 6/6 | 6/6 / 6/6 | [数值复核中；尚未签发整例资格](evidence/rewrite/R2/lu_boundary/20261110T075020.894988Z-R2-cpu-validation-315ecf016c/summary.md) |
| R2 / `posv` | 6/6 / 6/6 | 6/6 / 6/6 | [数值复核中；尚未签发整例资格](evidence/rewrite/R2/posv_boundary/20261110T075025.216319Z-R2-cpu-validation-f28f5bbcec/summary.md) |
| R2 / `trsm` | 6/6 / 6/6 | 6/6 / 6/6 | [数值复核中；尚未签发整例资格](evidence/rewrite/R2/trsm_boundary/20261110T075029.604587Z-R2-cpu-validation-3def04376f/summary.md) |

反向检查：16/16；原生与兼容 CUDA 数学对照分别登记。

当前全项目状态：211 PASSED、402 FAILED、24 PARTIAL、2 UNSUPPORTED。

日志：[实验事件索引](rewrite-experiments.jsonl)；[AMD运行](rewrite-first-rocm.json)；[独立CPU验收](rewrite-first-rocm-validation.json)；[CUDA运行](rewrite-first-cuda.json)。

待完成：提交固定源码后的独立审查、必要原生 SDK 合同复核、反向检查与支持资格签发。
