# rotmg 重复缩放：原生失败与项目 GPU 修正

锁定 ROCm 10.1.0 / gfx1201 的原生 hipBLAS→rocBLAS 在 d1=1e-20、d2=2e-20、x=2、y=1 下返回错误的 H 参数。独立 CPU OpenBLAS 与 CUDA cuBLAS 一致；原始普通输入通过，并不表示该极端 case 正确。

| H 元素 | 原生 AMD 输出 | CPU / CUDA 参考 |
| --- | ---: | ---: |
| h11 | 5.960464477539063e-8 | 5.960464477539063e-8 |
| h21 | -2.44140625e-4 | -2.9802322387695312e-8 |
| h12 | 1 | 5.960464477539063e-8 |
| h22 | 5.960464477539063e-8 | 5.960464477539063e-8 |

[原生失败、参考与精确源码身份](rotmg-native-rescale-failure.json)；[锁定上游源码](upstream-support/rocblas-rotmg-kernels.cpp) 与 [来源/hash](upstream-support/rocblas-rotmg-source.json)。两个缩放循环在 flag 已为 -1 时仍走普通 else，将已有 h21/h12 重置，破坏重复缩放的 H。

项目保留正常 hipBLAS 调用；遇到一般形式 H（flag=-1），用独立 HIP GPU kernel 正确保留并缩放 H，修正 d1/d2/x/param。共享 foundation 与 AMD 库没有修改，没有使用 CPU 数值回退。原始、零、非法负权重、极小/极大/非对称权重均纳入验收。该样例明确标为 hipBLAS + HIP scale fix / HYBRID_HIP，范围以所列 cases 为准。

[GPU 修正源码](../../rocm/common/rotmg_scale_fix.hip) · [最终第二批验收](batch2-validation.json)
