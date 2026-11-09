# nvTIFF/nvTIFF-GeoTIFF-Decode-Encode::nvtiff_geotiff_decode_encode.cpp

**FAILED / L1**

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvTIFF/nvTIFF-GeoTIFF-Decode-Encode/nvtiff_geotiff_decode_encode.cpp:23:10: fatal error: 'nvtiff_samples_common.h' file not found

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvTIFF/nvTIFF-GeoTIFF-Decode-Encode/nvtiff_geotiff_decode_encode.cpp](../../../../nvTIFF/nvTIFF-GeoTIFF-Decode-Encode/nvtiff_geotiff_decode_encode.cpp) |
| 实际库 / 后端 | — / — |
| 候选路线 | unresolved |
| 代码 | [rocm/ported/nvTIFF/nvTIFF-GeoTIFF-Decode-Encode/nvtiff_geotiff_decode_encode.cpp](../../../../rocm/ported/nvTIFF/nvTIFF-GeoTIFF-Decode-Encode/nvtiff_geotiff_decode_encode.cpp) |
| required cases | 0/2 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `21c20a8fa1cbc298ec1eb5badfeb79d71f3d9d7154ee5f7deb8d1fe22db8df0f` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：补 GPU TIFF codec 及容器/元数据桥接；分别验收 encode/decode/multi-image/GeoTIFF/options。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvTIFF/nvTIFF-GeoTIFF-Decode-Encode/nvtiff_geotiff_decode_encode.cpp:23:10: fatal error: 'nvtiff_samples_common.h' file not found

尝试库：—；实现 hash：`dbddbdbfa1791d21d7ac13f1cdb3776e18d97a8f224c48ea91031750cc077d94`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/nvTIFF_nvTIFF-GeoTIFF-Decode-Encode_nvtiff_geotiff_decode_encode.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/nvTIFF_nvTIFF-GeoTIFF-Decode-Encode_nvtiff_geotiff_decode_encode.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvTIFF_nvTIFF-GeoTIFF-Decode-Encode_nvtiff_geotiff_decode_encode.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/nvTIFF_nvTIFF-GeoTIFF-Decode-Encode_nvtiff_geotiff_decode_encode.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvTIFF_nvTIFF-GeoTIFF-Decode-Encode_nvtiff_geotiff_decode_encode.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/nvTIFF_nvTIFF-GeoTIFF-Decode-Encode_nvtiff_geotiff_decode_encode.cpp)
