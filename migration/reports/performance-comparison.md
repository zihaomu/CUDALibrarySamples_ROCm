# GEMM 性能实验结果

**BLOCKED：AMD GPU 有其它任务，未满足合格性能对比条件。** 下列仅为竞争条件下的原始观察值，不计算速度比或移植加速收益。正确性与性能资格分别记录。

6 GEMM profiles only, FP32/FP64 n256/1024/2048. GPU event timing around GEMM, allocation/transfer/init excluded, >=1s warmup then 3x100 iterations. Independent sampled long-double CPU reference.

| 精度 | n | AMD 原始 median ms（受竞争） | CUDA 原始 median ms | 合格速度比 |
| --- | ---: | ---: | ---: | --- |
| fp32 | 256 | 0.061800 | 0.010336 | 不报告 |
| fp64 | 256 | 0.196598 | 0.059328 | 不报告 |
| fp32 | 1024 | 0.199238 | 0.056032 | 不报告 |
| fp64 | 1024 | 3.176252 | 1.483008 | 不报告 |
| fp32 | 2048 | 1.359228 | 0.349856 | 不报告 |
| fp64 | 2048 | 21.580250 | 11.760032 | 不报告 |

空闲资格失败日志：[performance-idle-gate.log](performance-idle-gate.log)。完整三组 median、参考误差、运行目录和恢复条件：[performance-comparison.json](performance-comparison.json)。
