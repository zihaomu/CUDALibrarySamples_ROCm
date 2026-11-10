# MOAT 重写实时进展

更新时间：2026-11-10T10:05:43.447562+00:00。样例支持结论仍以 samples.yaml 为准。

| 批次 / 样例 | AMD 已运行 / CPU通过 | CUDA 已运行 / CPU通过 | 当前验收结论 |
| --- | ---: | ---: | --- |
| R1 / `gemm3m` | 6/6 / 6/6 | 6/6 / 6/6 | [整例已签发资格：PASSED](evidence/rewrite/R1/gemm3m_boundary/20261110T082833.002605Z-R1-cpu-validation-8f51bc20ae/summary.md) |
| R1 / `herk3m` | 6/6 / 6/6 | 6/6 / 6/6 | [整例已签发资格：PASSED](evidence/rewrite/R1/herk3m_boundary/20261110T082837.619360Z-R1-cpu-validation-3b64fb7e55/summary.md) |
| R1 / `syrk3m` | 6/6 / 6/6 | 6/6 / 6/6 | [整例已签发资格：PASSED](evidence/rewrite/R1/syrk3m_boundary/20261110T082842.183745Z-R1-cpu-validation-7fe31256f6/summary.md) |
| R1 / `planar` | 7/7 / 7/7 | 7/7 / 7/7 | [整例已签发资格：PASSED](evidence/rewrite/R1/planar_half-max/20261110T082905.721073Z-R1-cpu-validation-fa9ac77c24/summary.md) |
| R1 / `igemm` | 6/6 / 6/6 | 6/6 / 6/6 | [整例已签发资格：PASSED](evidence/rewrite/R1/igemm_boundary/20261110T082851.364518Z-R1-cpu-validation-8e0db494fe/summary.md) |
| R2 / `lu` | 7/7 / 7/7 | 7/7 / 7/7 | [整例已签发资格：PASSED](evidence/rewrite/R2/lu_wave-stress/20261110T082906.495078Z-R2-cpu-validation-e0fa6a85e6/summary.md) |
| R2 / `posv` | 7/7 / 7/7 | 7/7 / 7/7 | [整例已签发资格：PASSED](evidence/rewrite/R2/posv_nonspd-second-minor/20261110T082907.270760Z-R2-cpu-validation-94350d48bc/summary.md) |
| R2 / `trsm` | 6/6 / 6/6 | 6/6 / 6/6 | [整例已签发资格：PASSED](evidence/rewrite/R2/trsm_boundary/20261110T082904.941302Z-R2-cpu-validation-b83ccffba2/summary.md) |

反向检查：27/27；原生与兼容 CUDA 数学对照分别登记。

当前全项目状态：221 PASSED、393 FAILED、23 PARTIAL、2 UNSUPPORTED。

日志：[实验事件索引](rewrite-experiments.jsonl)；[AMD运行](rewrite-first-rocm.json)；[独立CPU验收](rewrite-first-rocm-validation.json)；[CUDA运行](rewrite-first-cuda.json)。

R1–R2完整记录：[批次验收](rewrite-R1-R2.md)。后续R3–R8尚未完成，全项目MOAT surface与其它平台仍有owed项。
