# MOAT 重写实时进展

更新时间：2026-11-11T06:50:56.068661+00:00。样例支持结论仍以 samples.yaml 为准。

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

当前全项目状态：231 PASSED、375 FAILED、33 PARTIAL。

日志：[实验事件索引](rewrite-experiments.jsonl)；[AMD运行](rewrite-first-rocm.json)；[独立CPU验收](rewrite-first-rocm-validation.json)；[CUDA运行](rewrite-first-cuda.json)。

R1–R2完整记录：[批次验收](rewrite-R1-R2.md)。其它批次见下表；全项目MOAT surface与其它平台仍有owed项。

## 全阶段与未完成范围

| 阶段 | 本轮新整例资格 | 仍未通过 | 当前结果与范围 |
| --- | ---: | ---: | --- |
| R1 | 5 | 0 | COMPLETED_SCOPED；5个 BLAS/Lt 整例 |
| R2 | 3 | 0 | COMPLETED_SCOPED；3个 device solver 整例 |
| R3 | 2 | 22 | ASSESSMENT_COMPLETE_22_GAPS；原24项复审，NCC/SVD两例收口 |
| R4 | 1 | 96 | SCOPED_BATCHES_96_PENDING；按资格签发的小批推进；R9含C++ helper及CRC benchmark |
| R5 | 8 | 66 | PARTIALLY_IMPLEMENTED_65_FRONTENDS_PENDING；真实 Fortran 入口；65前端与额外CPP项仍待支持 |
| R6 | 0 | 224 | ASSESSMENT_COMPLETE_PORTS_PENDING；224项专题研究与最小基础探针；未签发整例 |
| R7 | 2 | 0 | COMPLETED_SCOPED；2个真实GPU packed sparse2:4 整例 |
| R8 | 0 | 0 | COMPLETED_SCOPED；总回归、依赖封存、干净检出与交付 |

累计新增资格21项，另撤销旧C++排序样例资格1项，支持211→231，净增20。当前231/639通过、408待支持；117功能族、18模块。

[R3](rewrite-R3.md) · [R4](rewrite-R4.md) · [R5](rewrite-R5.md) · [R6](rewrite-R6.md) · [R7](rewrite-R7.md) · [408项逐例原因与后续实验](rewrite-remaining-assessment.md)。

计划第1.2节区分阶段执行和整例支持；R5剩余65个前端及其它待实现项没有被登记为完成。wave64、Windows、多节点与全项目MOAT surface仍未验证。

[R9：九个helper与CRC32 benchmark实时记录](rewrite-R9.md)。候选实现不预记整例资格。
