# 第二批：稀疏 3 + BLAS 8 + tensor 4 + solver 2

**17/17 个样例、45 个输入 case 全部通过 ROCm / 独立 CPU / CUDA 三方验收。** 全仓库当前 158 PASSED、14 PARTIAL、464 FAILED、2 UNSUPPORTED、1 BLOCKED；按模块去重的已验收算子/功能族由 75 增至 87。17 是样例增量，其中 batch/索引宽度扩展不重复计为新算子。

AMD 固定 ROCm 10.1.0 foundation / gfx1201，物理 GPU0（HIP ordinal2）经 PCI/预约 guard 校验；CUDA 用双 RTX5090 主机的 device0，CUDA13.4.92。cuTENSOR2.8.1 安装在项目 build overlay，wheel 与库身份 [单独锁定](../environments/cuda-cutensor.lock.json)，未更改全局 Toolkit。

| 原始样例 | 输入 cases | AMD/CPU | CUDA/CPU及同输入对照 |
| --- | --- | --- | --- |
| [cuSPARSE/spvv/spvv_example.c](../../migration/sample-reports/cuSPARSE/spvv/spvv_example.c.md) | original, changed-values | PASSED | PASSED |
| [cuSPARSE/spgemm/spgemm_example.c](../../migration/sample-reports/cuSPARSE/spgemm/spgemm_example.c.md) | original, changed-values | PASSED | PASSED |
| [cuSPARSE/spgemm_reuse/spgemm_reuse_example.c](../../migration/sample-reports/cuSPARSE/spgemm_reuse/spgemm_reuse_example.c.md) | original, changed-values | PASSED | PASSED |
| [cuBLAS/Level-1/amax/cublas_amax_example.cu](../../migration/sample-reports/cuBLAS/Level-1/amax/cublas_amax_example.cu.md) | original, ties, empty | PASSED | PASSED |
| [cuBLAS/Level-1/amin/cublas_amin_example.cu](../../migration/sample-reports/cuBLAS/Level-1/amin/cublas_amin_example.cu.md) | original, ties, empty | PASSED | PASSED |
| [cuBLAS/Level-1/rotg/cublas_rotg_example.cu](../../migration/sample-reports/cuBLAS/Level-1/rotg/cublas_rotg_example.cu.md) | original, zero, negative | PASSED | PASSED |
| [cuBLAS/Level-1/rotm/cublas_rotm_example.cu](../../migration/sample-reports/cuBLAS/Level-1/rotm/cublas_rotm_example.cu.md) | original, flag-minus2, flag-minus1, flag-zero | PASSED | PASSED |
| [cuBLAS/Level-1/rotmg/cublas_rotmg_example.cu](../../migration/sample-reports/cuBLAS/Level-1/rotmg/cublas_rotmg_example.cu.md) | original, zero, negative, rescale, rescale-large, rescale-asymmetric | PASSED | PASSED |
| [cuBLAS/Level-3/gemmBatched/cublas_gemmBatched_example.cu](../../migration/sample-reports/cuBLAS/Level-3/gemmBatched/cublas_gemmBatched_example.cu.md) | original, negative-alpha | PASSED | PASSED |
| [cuBLAS/Level-3/gemmGroupedBatched/cublas_gemmGroupedBatched_example.cu](../../migration/sample-reports/cuBLAS/Level-3/gemmGroupedBatched/cublas_gemmGroupedBatched_example.cu.md) | original, negative-alpha | PASSED | PASSED |
| [cuBLAS/Level-3/trsmBatched/cublas_trsmBatched_example.cu](../../migration/sample-reports/cuBLAS/Level-3/trsmBatched/cublas_trsmBatched_example.cu.md) | original, negative-alpha | PASSED | PASSED |
| [cuTENSOR/elementwise_binary.cu](../../migration/sample-reports/cuTENSOR/elementwise_binary.cu.md) | original, small-nonzero, small-zero | PASSED | PASSED |
| [cuTENSOR/elementwise_permute.cu](../../migration/sample-reports/cuTENSOR/elementwise_permute.cu.md) | original, small-nonzero, small-zero | PASSED | PASSED |
| [cuTENSOR/elementwise_trinary.cu](../../migration/sample-reports/cuTENSOR/elementwise_trinary.cu.md) | original, small-nonzero, small-zero | PASSED | PASSED |
| [cuTENSOR/reduction.cu](../../migration/sample-reports/cuTENSOR/reduction.cu.md) | original, small-nonzero, small-zero | PASSED | PASSED |
| [cuSOLVER/Xgeqrf/cusolver_Xgeqrf_example.cu](../../migration/sample-reports/cuSOLVER/Xgeqrf/cusolver_Xgeqrf_example.cu.md) | original | PASSED | PASSED |
| [cuSOLVER/Xpotrf/cusolver_Xpotrf_example.cu](../../migration/sample-reports/cuSOLVER/Xpotrf/cusolver_Xpotrf_example.cu.md) | original | PASSED | PASSED |

验收内容：

- SpVV 独立 CPU 点积；SpGEMM 检查 CSR bounds/列唯一性/nnz 与完整 CPU 矩阵乘积；reuse 在不改变 pattern 时将 A 数值翻倍并再次 compute，分别检查两次结果。
- amax/amin 检查 BLAS one-based、并列值与 n=0；rotg/rotm/rotmg 以独立 CPU OpenBLAS 与数学不变量检查 active 参数、零/负权重、flags、极小/极大/非对称缩放；batch/grouped 按不同尺寸逐矩阵检查，trsm 另验残差。
- tensor 保留原始 modes/extents/FP32 与原数学 API，使用共享 seed fixture；检查原始规模的全部 115121408 个语义输出，另加非整齐小尺寸、非零系数和 alpha=0。CPU 以显式 column-major modes 和 FP64 运算独立计算。记录全量有限值、relative L2 和最大绝对误差；CUDA 使用 AMD 保存的相同输入，SHA256 对齐后全量对照。
- Xgeqrf 从 Householder/tau 独立构造 Q，检查 QR 重构与正交性；Xpotrf 检查 LL^T 重构、AX=B 残差与 info=0。两端输入身份为不可变上游原始字面量矩阵，不要求因合法符号变化产生的 factor 逐位一致。

[原始数值/参数/误差及阈值](batch2-validation.json) · [21 个故意损坏输出/NaN 的拒绝检查](batch2-negative-checks.json) · [27 个 tensor 输入 buffer 的生成规则/hash](batch2-fixtures.json) · [重新生成验证日志](batch2-fixture-replay.log)

`rotmg` 的原生极端缩放有真实数值错误，所选实现为 **hipBLAS + 项目 HIP GPU 修正**，不是原生 hipBLAS 全部通过。普通路径保留库调用，一般形式 H 用 GPU 保留正确缩放状态；共享 AMD SDK 未修改，未使用 CPU 结果回填。见 [原生失败与修正说明](rotmg-scale-fix.md)。

在仓库根目录复现 AMD（先检查占用及预约）：

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batch2_run.py sparse blas
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batch2_run.py tensor solver
```

CUDA 主机的项目 checkout（从源码对象恢复已观测的 CUDA 副本；只安装项目 SDK）：

```bash
python3 tools/migration/restore_observations.py
python3 tools/migration/bootstrap_cuda_tensor.py
python3 -m pip install --target build/python-reference numpy==2.3.4
python3 tools/migration/regenerate_batch2_fixtures.py
CUDA_VISIBLE_DEVICES=0 python3 tools/migration/batch2_run.py sparse blas tensor solver --backend cuda --fixture-root build/batch2-tensor-fixtures
```

把 CUDA 的 batch2-cuda.json 和其中记录的证据目录同步回 CPU 参考主机。CPU 参考使用宿主 Python3.12 的 build/python-reference（版本见环境锁），不在 foundation Python3.13 中复用这些二进制包：

```bash
python3 tools/migration/batch2_validate.py sparse blas tensor solver --qualify
python3 tools/migration/batch2_negative_checks.py
python3 tools/migration/render.py
```

大输入/输出仅在本地 artifacts；seed=20261109 的 uint32 mixing / high24-bit FP32 规则可在 CPU 精确重建全部 27 个输入 buffer，已逐文件验证 SHA256；小尺寸输入随 Git 提交。性能打印不作为本批性能结论，既有 GEMM 的竞争条件结果保持历史 BLOCKED。
