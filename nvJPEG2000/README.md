# nvJPEG2000 library examples

These examples show how to decode and encode JPEG 2000 images on the GPU with the
[nvJPEG2000](https://docs.nvidia.com/cuda/nvjpeg2000/index.html) library.

## Examples

| Example | What it shows |
|---|---|
| [nvJPEG2000-Decoder](nvJPEG2000-Decoder/) | Decoding whole images, one at a time, with `nvjpeg2kDecodeImage` |
| [nvJPEG2000-Decoder-Pipelined](nvJPEG2000-Decoder-Pipelined/) | Overlapping the decodes of a batch of images, each on its own decode state and CUDA stream |
| [nvJPEG2000-Decoder-Tile-Partial](nvJPEG2000-Decoder-Tile-Partial/) | Decoding an image tile by tile with `nvjpeg2kDecodeTile`, or only an area of it |
| [nvJPEG2000-Encoder](nvJPEG2000-Encoder/) | Encoding BMP, PGM/PPM, PFM and raw YUV images to JPEG 2000 or HTJ2K |

## What nvJPEG2000 supports

This is what nvJPEG2000 0.12 supports. Each example's README lists what that example handles, which can be less.

Decoding:
- JPEG 2000 Part 1 and High-Throughput JPEG 2000 (HTJ2K, Part 15), as .jp2 files or raw codestreams
- Up to 16384 components
- Integer output up to 16 bits per component: unsigned 8-bit, unsigned 16-bit and signed 16-bit
- 16- and 32-bit floating-point output for images with NLT type 3 on every component (HTJ2K, reversible wavelet)
- 4:4:4, 4:2:2 and 4:2:0 chroma subsampling, with optional conversion to RGB
- Reversible (5-3) and irreversible (9-7) wavelets, multiple tiles, up to 32 quality layers, and all progression orders
- Decoding a single tile (also at a lower resolution), an area of the image, or a subset of its components

Encoding:
- JPEG 2000 Part 1 and HTJ2K, as .jp2 files or raw codestreams
- 1 to 16384 components, with integer input up to 16 bits: unsigned 8-bit, unsigned 16-bit and signed 16-bit
- 16- and 32-bit floating-point input, encoded as HTJ2K with NLT type 3 and the reversible wavelet
- Lossless (reversible wavelet) or lossy (irreversible wavelet) encoding; lossy quality is set by Q-factor, quantization
  step or target PSNR, and target PSNR is not available with HTJ2K
- Code blocks of 32x32, 32x64, 64x32 and 64x64, and 128x32 for HTJ2K with NLT type 3
- All progression orders, multiple tiles, and 4:2:2 or 4:2:0 input in the YCbCr (sYCC) color space

The [nvJPEG2000 documentation](https://docs.nvidia.com/cuda/nvjpeg2000/index.html) has the complete list and its limits.

## Supported platforms

| Platform | CUDA 12 | CUDA 13 |
|---|---|---|
| Linux x86_64 | GPUs of compute capability 5.2 and higher | GPUs of compute capability 7.5 and higher |
| Linux arm64 server (sbsa) | GPUs of compute capability 5.2 and higher | GPUs of compute capability 7.5 and higher; Jetson Thor, and Jetson Orin from CUDA 13.2 |
| Linux aarch64 for Jetson (L4T) | Jetson Orin | Not available; use the arm64 server package |
| Windows x86_64 | GPUs of compute capability 5.2 and higher | GPUs of compute capability 7.5 and higher |

The supported Linux distributions and Windows versions are listed in the
[nvJPEG2000 documentation](https://docs.nvidia.com/cuda/nvjpeg2000/index.html).

## Prerequisites

- An NVIDIA GPU from the table above, and a driver that supports the CUDA version of the nvJPEG2000 package
- CUDA Toolkit 12 or 13, the same CUDA major version as the nvJPEG2000 package
- CMake 3.18 or later
- A C++17 compiler: GCC on Linux, Visual Studio on Windows
- [nvJPEG2000](https://developer.nvidia.com/nvjpeg2000/downloads)

## Building all examples

The CMakeLists.txt in this directory builds all four examples against an nvJPEG2000 package, and installs them with
their images and a script that runs them. `NVJPEG2K_PATH` is the root of the package, the directory holding `include`
and `lib`.

Linux:
```
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DNVJPEG2K_PATH=/opt/libnvjpeg_2k
cmake --build build
cmake --install build --prefix examples
```

Windows:
```
cmake -S . -B build -G "Visual Studio 17 2022" -A x64 -DNVJPEG2K_PATH=C:\libnvjpeg_2k
cmake --build build --config Release
cmake --install build --config Release --prefix examples
```

If CMake cannot find nvcc, add the CUDA Toolkit's `bin` directory to `PATH`, or set `CUDACXX` to the nvcc path. Each
example can also be built on its own; see its README.

## Checking the build

The install directory holds the examples in `bin`, their images in `images`, and `run_examples.sh` (Linux) or
`run_examples.cmd` (Windows). The script runs every example on the images and checks what they write: the Decoder and
Decoder-Pipelined outputs must be identical, and a lossless encode and decode, with and without HTJ2K, must reproduce
the source image. It checks that the build and the setup work; it is not a test of nvJPEG2000.

Linux:
```
examples/run_examples.sh /opt/libnvjpeg_2k 12
```

Windows:
```
examples\run_examples.cmd C:\libnvjpeg_2k 12
```

The second argument is the CUDA major version of the package. The script adds the package's `lib/<CUDA major>`
directory to the library search path. The CUDA runtime (`libcudart.so.<CUDA major>` on Linux, `cudart64_<CUDA major>.dll`
on Windows) must already be found, for example by adding the CUDA Toolkit's `lib64` directory to `LD_LIBRARY_PATH` on
Linux, or its `bin` directory (`bin\x64` with CUDA 13) to `PATH` on Windows.

## Exit codes

All examples use these exit codes:

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Any error not listed below, such as a CUDA failure |
| 2 | Invalid command line |
| 3 | The input path does not exist, or none of its files can be read |
| 4 | The input directory holds no files |
| 5 | A valid image that the example cannot handle; see the example's README |
| 6 | Decoding or encoding failed, or the output could not be written |

## API documentation

[nvJPEG2000](https://docs.nvidia.com/cuda/nvjpeg2000/index.html)

<!-- ROCM-MIGRATION:START -->
## ROCm 支持情况

4 个独立源入口；PASSED 0，PARTIAL 0，FAILED 4，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：unresolved。候选不等于已使用；基础探针成功也不等于整库迁移成功。

rocJPEG 的 JPEG decode 不能替代 JPEG2000；原始 GPU codec/多阶段/metadata 接口没有 AMD 实现，CPU OpenJPEG 不计成功。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [nvJPEG2000-Decoder-Pipelined/nvjpeg2k_dec_pipelined.cpp](nvJPEG2000-Decoder-Pipelined/nvjpeg2k_dec_pipelined.cpp) · [详情](../migration/sample-reports/nvJPEG2000/nvJPEG2000-Decoder-Pipelined/nvjpeg2k_dec_pipelined.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvJPEG2000/nvJPEG2000-Decoder-Pipelined/nvjpeg2k_dec_pipelined.h:53:10: fatal error: 'nvjpeg2k.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG2000_nvJPEG2000-Decoder-Pipelined_nvjpeg2k_dec_pipelined.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG2000_nvJPEG2000-Decoder-Pipelined_nvjpeg2k_dec_pipelined.cpp) |
| [nvJPEG2000-Decoder-Tile-Partial/nvjpeg2k_decode_tile_partial.cpp](nvJPEG2000-Decoder-Tile-Partial/nvjpeg2k_decode_tile_partial.cpp) · [详情](../migration/sample-reports/nvJPEG2000/nvJPEG2000-Decoder-Tile-Partial/nvjpeg2k_decode_tile_partial.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvJPEG2000/nvJPEG2000-Decoder-Tile-Partial/nvjpeg2k_decode_tile_partial.h:52:10: fatal error: 'nvjpeg2k.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG2000_nvJPEG2000-Decoder-Tile-Partial_nvjpeg2k_decode_tile_partial.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG2000_nvJPEG2000-Decoder-Tile-Partial_nvjpeg2k_decode_tile_partial.cpp) |
| [nvJPEG2000-Decoder/nvjpeg2k_decode.cpp](nvJPEG2000-Decoder/nvjpeg2k_decode.cpp) · [详情](../migration/sample-reports/nvJPEG2000/nvJPEG2000-Decoder/nvjpeg2k_decode.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvJPEG2000/nvJPEG2000-Decoder/nvjpeg2k_decode.h:52:10: fatal error: 'nvjpeg2k.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG2000_nvJPEG2000-Decoder_nvjpeg2k_decode.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG2000_nvJPEG2000-Decoder_nvjpeg2k_decode.cpp) |
| [nvJPEG2000-Encoder/nvjpeg2k_encode.cpp](nvJPEG2000-Encoder/nvjpeg2k_encode.cpp) · [详情](../migration/sample-reports/nvJPEG2000/nvJPEG2000-Encoder/nvjpeg2k_encode.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvJPEG2000/nvJPEG2000-Encoder/nvjpeg2k_encode.h:49:10: fatal error: 'nvjpeg2k.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG2000_nvJPEG2000-Encoder_nvjpeg2k_encode.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG2000_nvJPEG2000-Encoder_nvjpeg2k_encode.cpp) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
