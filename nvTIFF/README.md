# nvTIFF Library API examples

## Description

Samples demonstrating GPU-accelerated TIFF decoding and encoding with the
[nvTIFF library](https://docs.nvidia.com/cuda/nvtiff/index.html) (0.9 API).

## Examples

| Sample | Workload | Key APIs |
|---|---|---|
| [nvTIFF-Decode](nvTIFF-Decode/) | Minimal first-image decode and PNM preview | `nvtiffStreamOpenFromFile`, `nvtiffStreamGetImageInfo`, `nvtiffDecode` |
| [nvTIFF-Decode-Encode](nvTIFF-Decode-Encode/) | Minimal decode → encode roundtrip | `nvtiffStreamOpenFromFile`, `nvtiffDecode`, `nvtiffEncode`, `nvtiffWriteTiffFile` |
| [nvTIFF-Image-Info-Multi-Image](nvTIFF-Image-Info-Multi-Image/) | Multi-page / pyramid navigation, metadata, SubIFDs | `nvtiffStreamGetHeader`, `nvtiffStreamGetNextIFDOffset`, tag APIs |
| [nvTIFF-Batched-Region-Decode](nvTIFF-Batched-Region-Decode/) | Many ROIs in one decode call (patch extraction, tile serving) | `nvtiffDecodeRegion_t`, `nvtiffDecodeParamsSetRegions`, `NVTIFF_STATUS_BATCH_INCOMPATIBLE` |
| [nvTIFF-Encode-Options](nvTIFF-Encode-Options/) | Strip/tile geometry, JPEG options, BigTIFF, custom tags, encode-to-memory | `nvtiffEncodeParamsSetImageGeometry`, `SetJpegOptions`, `SetTiffVariant`, `SetTag`, `nvtiffWriteTiffBuffer` |
| [nvTIFF-GeoTIFF-Decode-Encode](nvTIFF-GeoTIFF-Decode-Encode/) | Georeferencing roundtrip | geo key getters and setters, `NVTIFF_TAG_MODEL_*` |

## Test data

`images/bali_notiles.tif` ships with the samples and works with every decode
sample. `nvTIFF-Encode-Options` generates tiled,
multi-page, JPEG, BigTIFF and custom-tag files that the other samples accept
as input. For real-world large tiled / pyramidal images see the
[OpenSlide test data](https://openslide.cs.cmu.edu/download/openslide-testdata/)
(note the per-file licenses); GeoTIFF inputs can be created with GDAL (see
the GeoTIFF sample README).

## Supported SM Architectures

[SM 7.0 +](https://developer.nvidia.com/cuda-gpus)

## Supported OSes

Linux, Windows

## Supported CPU Architecture

x86_64, arm64-sbsa, aarch64-jetson

## Prerequisites

- A Linux or Windows system with recent NVIDIA drivers.
- The [CUDA toolkit](https://developer.nvidia.com/cuda-downloads).
- [nvTIFF](https://developer.nvidia.com/nvtiff-downloads) 0.9 or later.
- Optional runtime dependencies, loaded on demand:
  [nvCOMP](https://developer.nvidia.com/nvcomp-download) 6.0 or later for
  Deflate and Zstandard,
  nvJPEG (part of the CUDA toolkit) for JPEG, and
  [nvJPEG2000](https://developer.nvidia.com/nvjpeg2000-downloads) for
  JPEG2000/Aperio streams.

Each sample builds standalone:

```
cd <sample>
cmake -B build -DNVTIFF_PATH=/path/to/nvtiff/cuda13   # archive dir or install prefix
cmake --build build
```

<!-- ROCM-MIGRATION:START -->
## ROCm 支持情况

6 个独立源入口；PASSED 0，PARTIAL 0，FAILED 6，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：unresolved。候选不等于已使用；基础探针成功也不等于整库迁移成功。

原始 TIFF GPU codec 与多页/GeoTIFF/options 等接口未改写；CPU TIFF 容器处理不能冒充 GPU codec。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [nvTIFF-Batched-Region-Decode/nvtiff_batched_region_decode.cpp](nvTIFF-Batched-Region-Decode/nvtiff_batched_region_decode.cpp) · [详情](../migration/sample-reports/nvTIFF/nvTIFF-Batched-Region-Decode/nvtiff_batched_region_decode.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvTIFF/nvTIFF-Batched-Region-Decode/nvtiff_batched_region_decode.cpp:23:10: fatal error: 'nvtiff_samples_common.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvTIFF_nvTIFF-Batched-Region-Decode_nvtiff_batched_region_decode.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvTIFF_nvTIFF-Batched-Region-Decode_nvtiff_batched_region_decode.cpp) |
| [nvTIFF-Decode-Encode/nvtiff_decode_encode.cpp](nvTIFF-Decode-Encode/nvtiff_decode_encode.cpp) · [详情](../migration/sample-reports/nvTIFF/nvTIFF-Decode-Encode/nvtiff_decode_encode.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvTIFF/nvTIFF-Decode-Encode/nvtiff_decode_encode.cpp:23:10: fatal error: 'nvtiff_samples_common.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvTIFF_nvTIFF-Decode-Encode_nvtiff_decode_encode.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvTIFF_nvTIFF-Decode-Encode_nvtiff_decode_encode.cpp) |
| [nvTIFF-Decode/nvtiff_decode.cpp](nvTIFF-Decode/nvtiff_decode.cpp) · [详情](../migration/sample-reports/nvTIFF/nvTIFF-Decode/nvtiff_decode.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvTIFF/nvTIFF-Decode/nvtiff_decode.cpp:23:10: fatal error: 'nvtiff_samples_common.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvTIFF_nvTIFF-Decode_nvtiff_decode.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvTIFF_nvTIFF-Decode_nvtiff_decode.cpp) |
| [nvTIFF-Encode-Options/nvtiff_encode_options.cpp](nvTIFF-Encode-Options/nvtiff_encode_options.cpp) · [详情](../migration/sample-reports/nvTIFF/nvTIFF-Encode-Options/nvtiff_encode_options.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvTIFF/nvTIFF-Encode-Options/nvtiff_encode_options.cpp:23:10: fatal error: 'nvtiff_samples_common.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvTIFF_nvTIFF-Encode-Options_nvtiff_encode_options.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvTIFF_nvTIFF-Encode-Options_nvtiff_encode_options.cpp) |
| [nvTIFF-GeoTIFF-Decode-Encode/nvtiff_geotiff_decode_encode.cpp](nvTIFF-GeoTIFF-Decode-Encode/nvtiff_geotiff_decode_encode.cpp) · [详情](../migration/sample-reports/nvTIFF/nvTIFF-GeoTIFF-Decode-Encode/nvtiff_geotiff_decode_encode.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvTIFF/nvTIFF-GeoTIFF-Decode-Encode/nvtiff_geotiff_decode_encode.cpp:23:10: fatal error: 'nvtiff_samples_common.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvTIFF_nvTIFF-GeoTIFF-Decode-Encode_nvtiff_geotiff_decode_encode.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvTIFF_nvTIFF-GeoTIFF-Decode-Encode_nvtiff_geotiff_decode_encode.cpp) |
| [nvTIFF-Image-Info-Multi-Image/nvtiff_image_info.cpp](nvTIFF-Image-Info-Multi-Image/nvtiff_image_info.cpp) · [详情](../migration/sample-reports/nvTIFF/nvTIFF-Image-Info-Multi-Image/nvtiff_image_info.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvTIFF/nvTIFF-Image-Info-Multi-Image/nvtiff_image_info.cpp:22:10: fatal error: 'nvtiff_samples_common.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvTIFF_nvTIFF-Image-Info-Multi-Image_nvtiff_image_info.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvTIFF_nvTIFF-Image-Info-Multi-Image_nvtiff_image_info.cpp) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
