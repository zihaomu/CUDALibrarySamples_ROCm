# cuBLAS/Level-1/amin::cublas_amin_example.cu

**PARTIAL / L3**

原始教学输入构建运行通过；独立正确性验证待完成

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLAS/Level-1/amin/cublas_amin_example.cu](../../../../../cuBLAS/Level-1/amin/cublas_amin_example.cu) |
| 实际库 / 后端 | hipblas / rocBLAS |
| 候选路线 | hipBLAS, rocBLAS |
| 代码 | [rocm/ported/cuBLAS/Level-1/amin/cublas_amin_example.cu](../../../../../rocm/ported/cuBLAS/Level-1/amin/cublas_amin_example.cu) |
| required cases | 1/3 |
| CUDA baseline / comparison | PASSED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `d91d29c75d7ff20a453bf8e60d0118f0fb5914671ad86a20492e249837db23b9` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`build-and-original-profile-execution`, `original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：—；实现 hash：`c471121cd359521f181287df2cd5542fc8907a8bbf3effa2efc5efb9414c0ea9`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Level-1_amin_cublas_amin_example.cu](../../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuBLAS_Level-1_amin_cublas_amin_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Level-1_amin_cublas_amin_example.cu](../../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuBLAS_Level-1_amin_cublas_amin_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Level-1_amin_cublas_amin_example.cu](../../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuBLAS_Level-1_amin_cublas_amin_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Level-1_amin_cublas_amin_example.cu](../../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuBLAS_Level-1_amin_cublas_amin_example.cu)
- [migration/reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Level-1_amin_cublas_amin_example.cu](../../../../reports/evidence/20261109T082832.792069Z/original-rocm/cuBLAS_Level-1_amin_cublas_amin_example.cu)
- [migration/reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-1_amin_cublas_amin_example.cu](../../../../reports/evidence/20261109T082621.001055Z/original-cuda/cuBLAS_Level-1_amin_cublas_amin_example.cu)
