# M0–M5 执行交付

**已完成全量执行与结果归档；功能迁移仍有失败、部分完成和前置条件缺口。** 共 639 个入口，464 FAILED / 158 PASSED / 14 PARTIAL / 2 UNSUPPORTED / 1 BLOCKED。没有 NOT_STARTED/IN_PROGRESS。成功率按逐例登记范围计为 24.73%，困难样例全部保留在分母。

| 阶段 | 入口 | 结果 |
| --- | ---: | --- |
| M0 | 866 源文件 / 477 构建定义 | 静态审计、环境锁、runner、fixture、证据结构已完成；53 个未展开表达式已分类 |
| M1 | 16 | 16 PASSED |
| M2 | 205 | 64 FAILED, 129 PASSED, 12 PARTIAL |
| M3 | 79 | 69 FAILED, 2 UNSUPPORTED, 5 PASSED, 2 PARTIAL, 1 BLOCKED |
| M4 | 58 | 55 FAILED, 3 PASSED |
| M5 | 281 | 276 FAILED, 5 PASSED |

M1 16/16、95 required cases、CTest 16/16 通过；另外 54 组 CUDA 专项对照全部通过，不能与入口成功数相加。[数值与证据一致性验收](final-validation.json)。

6 个 GEMM 性能实验已运行，但 AMD 空闲资格失败；[性能报告](performance-comparison.md) 仅保留竞争条件下原始数据，不计算合格速度比。

原始 CUDA 源码与构建文件未改动；自动移植稿的失败与最终选定实现分开保存。所有逐例功能、实际库、缺失点、恢复条件与日志在 [清单](../samples.yaml) 和 30 个库级 README；[选型与失败边界](ecosystem-decisions.md)。

- 464 entries remain FAILED drafts or frontend/binding attempts; AMD algorithms/API rewrites are not implemented for all families.
- 14 PARTIAL entries have unvalidated original features or missing independent oracles.
- 2 UNSUPPORTED results apply only to locked hipSPARSELt/gfx1201; 1 BLOCKED Python test lacks GPU executable prerequisites.
- CUDA baseline builds/inputs/SDKs have individual failures or prerequisite blocks; a GPU execution return code alone is not a numerical comparison.
- No multi-node MPI environment was established; basic RCCL probes do not qualify original distributed Mp examples.
- All PASSED labels apply only to explicitly registered original profiles/required cases, not whole-library compatibility.
