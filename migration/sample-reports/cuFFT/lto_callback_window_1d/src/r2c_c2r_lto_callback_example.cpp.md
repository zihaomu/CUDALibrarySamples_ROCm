# cuFFT/lto_callback_window_1d/src::r2c_c2r_lto_callback_example.cpp

**PASSED / L4**

HIP 编译器预生成 SPIR-V，经 hipfftXtSetJITCallback 与 FFT 内核 JIT 集成，保留 device callback 融合；原始 830×328、window32 全量输出通过独立 CPU FFT/filter/inverse 检查，L2=2.746302811829082e-07。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuFFT/lto_callback_window_1d/src/r2c_c2r_lto_callback_example.cpp](../../../../../cuFFT/lto_callback_window_1d/src/r2c_c2r_lto_callback_example.cpp) |
| 实际库 / 后端 | hipFFT/rocFFT JIT callbacks + HIP compiler SPIR-V / rocFFT SPIR-V JIT integration |
| 候选路线 | hipFFT, rocFFT, RCCL + HIP (distributed alternative) |
| 代码 | [rocm/cuFFT/lto_callback_window_1d/sample_jit.cpp](../../../../../rocm/cuFFT/lto_callback_window_1d/sample_jit.cpp) |
| required cases | 2/2 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `dbfcba4a01351756d763bd0801b911821bd73c25884bbf961cfb4d074d4ea8ec` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-window32-batch830-size328-independent-cpu`, `compiled-SPIRV-JIT`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuFFT/lto_callback_window_1d/src/r2c_c2r_lto_callback_example.cpp:34:10: fatal error: 'r2c_c2r_lto_callback_device_fatbin.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihao

尝试库：hipfft；实现 hash：`a1e02533ed04f74f682b5dd19159d8e47abb2793a6340d66645c079b7769aa1f`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_lto_callback_example.cpp](../../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_lto_callback_example.cpp)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_lto_callback_example.cpp](../../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_lto_callback_example.cpp)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_lto_callback_example.cpp](../../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_lto_callback_example.cpp)
- [migration/reports/evidence/20261109T085509.301265Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_lto_callback_example.cpp](../../../../reports/evidence/20261109T085509.301265Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_lto_callback_example.cpp)
- [migration/reports/evidence/20261109T090451.232153Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_lto_callback_example.cpp](../../../../reports/evidence/20261109T090451.232153Z/original-rocm/cuFFT_lto_callback_window_1d_src_r2c_c2r_lto_callback_example.cpp)
- [migration/reports/evidence/20261109T092810.856178Z/jit-fft/bitcode](../../../../reports/evidence/20261109T092810.856178Z/jit-fft/bitcode)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_lto_callback_window_1d_src_r2c_c2r_lto_callback_example.cpp](../../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuFFT_lto_callback_window_1d_src_r2c_c2r_lto_callback_example.cpp)
- [migration/reports/additional-comparison.json](../../../../reports/additional-comparison.json)
