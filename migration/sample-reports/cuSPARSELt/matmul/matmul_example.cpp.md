# cuSPARSELt/matmul::matmul_example.cpp

**UNSUPPORTED / L2**

锁定 ROCm 10.1.0 hipSPARSELt 已编译，但 gfx1201 缺少 kernel bundle；实机返回 NOT_IMPLEMENTED/无法加载 TensileLibrary_lazy_gfx1201，固定源码架构检查也拒绝 gfx1201。仅限此版本/硬件/后端；保留 structured prune/compress/matmul 契约，未改成 dense。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSPARSELt/matmul/matmul_example.cpp](../../../../cuSPARSELt/matmul/matmul_example.cpp) |
| 实际库 / 后端 | hipsparselt+hipsparse / hipSPARSELt |
| 候选路线 | hipSPARSELt |
| 代码 | [rocm/ported/cuSPARSELt/matmul/matmul_example.cpp](../../../../rocm/ported/cuSPARSELt/matmul/matmul_example.cpp) |
| required cases | 0/2 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `19b6c11093e7160dd031648d316e2bc6df8324988adeedd5b9499ca1b623bb95` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：使用有匹配 kernel bundle 的受支持 GPU，或新的 gfx1201 hipSPARSELt 实现/包；重新跑 prune/compress/matmul 与 CPU 参考。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

run 失败：hipsparselt_error: Cannot read /opt/venv/lib/python3.13/site-packages/_rocm_sdk_libraries/lib/hipsparselt/library/TensileLibrary_lazy_gfx1201.dat (or .zlib variant): Illegal seek；hipsparselt_error: Could not load /opt/venv/lib/python3.13/site-packages/_rocm_sdk_libraries/lib/hipsparselt/library/TensileLibrary_lazy_gfx1201.dat

尝试库：hipsparselt, hipsparse；实现 hash：`ce7d529bea4268fc1ebccadbc21d9b23bbc7ee2f9b3d6e3e51698e77e78115d9`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuSPARSELt_matmul_matmul_example.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/cuSPARSELt_matmul_matmul_example.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSPARSELt_matmul_matmul_example.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/cuSPARSELt_matmul_matmul_example.cpp)
- [migration/reports/evidence/20261109T091606.225939Z/original-rocm/cuSPARSELt_matmul_matmul_example.cpp](../../../reports/evidence/20261109T091606.225939Z/original-rocm/cuSPARSELt_matmul_matmul_example.cpp)
- [migration/reports/evidence/20261109T091904.671567Z/original-rocm/cuSPARSELt_matmul_matmul_example.cpp](../../../reports/evidence/20261109T091904.671567Z/original-rocm/cuSPARSELt_matmul_matmul_example.cpp)
- [migration/reports/evidence/20261109T092720.531889Z/original-rocm/cuSPARSELt_matmul_matmul_example.cpp](../../../reports/evidence/20261109T092720.531889Z/original-rocm/cuSPARSELt_matmul_matmul_example.cpp)
- [migration/reports/upstream-support/hipsparselt-gfx1201-configure.log](../../../reports/upstream-support/hipsparselt-gfx1201-configure.log)
- [migration/reports/upstream-support/sources.json](../../../reports/upstream-support/sources.json)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSPARSELt_matmul_matmul_example.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/cuSPARSELt_matmul_matmul_example.cpp)
