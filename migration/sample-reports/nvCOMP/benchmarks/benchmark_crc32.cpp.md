# nvCOMP/benchmarks::benchmark_crc32.cpp

**PASSED / L4**

保留原始CRC32 benchmark的CLI、默认storage、完整CSV网格及真实GPU配置搜索/最终重算；默认16GiB原规模、4个小场景、独立zlib、真实nvCOMP对照、故障/CLI/64位长度/trace/replay及独立复审通过。默认RNG序列不跨库逐位比较；性能与完整32GiB complete扫描未验收。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvCOMP/benchmarks/benchmark_crc32.cpp](../../../../nvCOMP/benchmarks/benchmark_crc32.cpp) |
| 实际库 / 后端 | HIP + hipRAND + project segmented IEEE CRC32/GPU GF2 search / project HIP segmented CRC/GF2 backend |
| 候选路线 | hipCOMP |
| 代码 | [rocm/ported/nvCOMP/benchmarks/benchmark_crc32.cpp](../../../../rocm/ported/nvCOMP/benchmarks/benchmark_crc32.cpp) |
| required cases | 8/8 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `e343816ec5a4af1af1b907da5534aa010f2c579658883559b913465463a69f7e` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite/original-auto`, `rewrite/storage-small`, `rewrite/complete-small`, `rewrite/changed-input`, `rewrite/repeat`, `rewrite/negative-and-runtime`, `rewrite/sealed-build-and-native-identities`, `rewrite/independent-source-review`。

实现方式：`PROJECT_HIP_CRC_WITH_ORIGINAL_BENCHMARK_HARNESS`。

恢复/扩展条件：扩展API/精度/布局/设备或性能声明时重新冻结合同并完成实际GPU与独立参考验收。

CUDA 对照限制：四个冻结小输入同字节三方；默认各自实际RNG输入在各GPU运行后独立CPU校验。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvCOMP/benchmarks/benchmark_crc32.cpp:321:3: error: unknown type name 'nvcompCRC32KernelConf_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvCOMP/benchmarks/benchmark_crc32.cpp:327:5: error: use of undeclared identifier 'nvcompCRC32'

尝试库：—；实现 hash：`a7d9f686fabe127764435e609da33cb658a5435d54d9201ed622bd59dc9c0bc3`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python3 tools/moat/build_crc_benchmark.py
python3 tools/moat/run_crc_benchmark.py
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/nvCOMP_benchmarks_benchmark_crc32.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/nvCOMP_benchmarks_benchmark_crc32.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvCOMP_benchmarks_benchmark_crc32.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/nvCOMP_benchmarks_benchmark_crc32.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvCOMP_benchmarks_benchmark_crc32.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/nvCOMP_benchmarks_benchmark_crc32.cpp)
- [migration/reports/rewrite-R9.md](../../../reports/rewrite-R9.md)
- [migration/reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T071936.358750Z-R9-composite-qualification-b099b3980b](../../../reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T071936.358750Z-R9-composite-qualification-b099b3980b)
- [migration/reports/evidence/rewrite/R9/CRC32-64bit-combine-boundary/20261111T070943.761040Z-R9-rocm-probe-12e61eb3b1](../../../reports/evidence/rewrite/R9/CRC32-64bit-combine-boundary/20261111T070943.761040Z-R9-rocm-probe-12e61eb3b1)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-GPU-trace-and-repeat/20261111T065742.236597Z-R9-rocm-profile-3dc3e055a1](../../../reports/evidence/rewrite/R9/CRC32-benchmark-GPU-trace-and-repeat/20261111T065742.236597Z-R9-rocm-profile-3dc3e055a1)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-native-build/20261111T065629.694235Z-R9-cuda-build-a85c454dc1](../../../reports/evidence/rewrite/R9/CRC32-benchmark-native-build/20261111T065629.694235Z-R9-cuda-build-a85c454dc1)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-output-negative/20261111T070926.146462Z-R9-CPU-negative-d0a5b515f9](../../../reports/evidence/rewrite/R9/CRC32-benchmark-output-negative/20261111T070926.146462Z-R9-CPU-negative-d0a5b515f9)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-output-negative/20261111T070927.287125Z-R9-CPU-negative-6014296f38](../../../reports/evidence/rewrite/R9/CRC32-benchmark-output-negative/20261111T070927.287125Z-R9-CPU-negative-6014296f38)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-output-negative/20261111T070928.474656Z-R9-CPU-negative-f798073a63](../../../reports/evidence/rewrite/R9/CRC32-benchmark-output-negative/20261111T070928.474656Z-R9-CPU-negative-f798073a63)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-output-negative/20261111T070929.618197Z-R9-CPU-negative-23890312d1](../../../reports/evidence/rewrite/R9/CRC32-benchmark-output-negative/20261111T070929.618197Z-R9-CPU-negative-23890312d1)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-output-negative/20261111T070930.792169Z-R9-CPU-negative-ffacc564ce](../../../reports/evidence/rewrite/R9/CRC32-benchmark-output-negative/20261111T070930.792169Z-R9-CPU-negative-ffacc564ce)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-output-negative/20261111T070931.959242Z-R9-CPU-negative-7296d47f7f](../../../reports/evidence/rewrite/R9/CRC32-benchmark-output-negative/20261111T070931.959242Z-R9-CPU-negative-7296d47f7f)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-output-negative/20261111T070933.111247Z-R9-CPU-negative-e58f341393](../../../reports/evidence/rewrite/R9/CRC32-benchmark-output-negative/20261111T070933.111247Z-R9-CPU-negative-e58f341393)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070934.261519Z-R9-rocm-runtime-26bb109aac](../../../reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070934.261519Z-R9-rocm-runtime-26bb109aac)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070935.347922Z-R9-rocm-runtime-9328e8a2b7](../../../reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070935.347922Z-R9-rocm-runtime-9328e8a2b7)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070936.480847Z-R9-rocm-runtime-958d03b1fe](../../../reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070936.480847Z-R9-rocm-runtime-958d03b1fe)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070937.566688Z-R9-rocm-runtime-2603def36b](../../../reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070937.566688Z-R9-rocm-runtime-2603def36b)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070938.659953Z-R9-rocm-runtime-19b1512c08](../../../reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070938.659953Z-R9-rocm-runtime-19b1512c08)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070939.740739Z-R9-rocm-runtime-e844e5a1cb](../../../reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070939.740739Z-R9-rocm-runtime-e844e5a1cb)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070940.964594Z-R9-rocm-runtime-53df25981b](../../../reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070940.964594Z-R9-rocm-runtime-53df25981b)
- [migration/reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070942.184916Z-R9-rocm-runtime-ee6b94f64d](../../../reports/evidence/rewrite/R9/CRC32-benchmark-runtime/20261111T070942.184916Z-R9-rocm-runtime-ee6b94f64d)
- [migration/reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T061849.276951Z-R9-rocm-build-0828d8560b](../../../reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T061849.276951Z-R9-rocm-build-0828d8560b)
- [migration/reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T065638.527435Z-R9-cuda-benchmark-8d861fa0e0](../../../reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T065638.527435Z-R9-cuda-benchmark-8d861fa0e0)
- [migration/reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070133.852466Z-R9-cuda-benchmark-932a95199b](../../../reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070133.852466Z-R9-cuda-benchmark-932a95199b)
- [migration/reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070136.681562Z-R9-cuda-benchmark-4aeaeaa744](../../../reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070136.681562Z-R9-cuda-benchmark-4aeaeaa744)
- [migration/reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070140.614659Z-R9-cuda-benchmark-396c176878](../../../reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070140.614659Z-R9-cuda-benchmark-396c176878)
- [migration/reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070144.020519Z-R9-cuda-benchmark-cefcf4bbcf](../../../reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070144.020519Z-R9-cuda-benchmark-cefcf4bbcf)
- [migration/reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070737.904731Z-R9-rocm-benchmark-86995e360d](../../../reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070737.904731Z-R9-rocm-benchmark-86995e360d)
- [migration/reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070816.332336Z-R9-rocm-benchmark-5b1029083a](../../../reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070816.332336Z-R9-rocm-benchmark-5b1029083a)
- [migration/reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070817.734649Z-R9-rocm-benchmark-000b3952a4](../../../reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070817.734649Z-R9-rocm-benchmark-000b3952a4)
- [migration/reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070819.483558Z-R9-rocm-benchmark-2ed9a65263](../../../reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070819.483558Z-R9-rocm-benchmark-2ed9a65263)
- [migration/reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070820.850656Z-R9-rocm-benchmark-aed39723b4](../../../reports/evidence/rewrite/R9/nvCOMP_benchmarks__benchmark_crc32.cpp/20261111T070820.850656Z-R9-rocm-benchmark-aed39723b4)
