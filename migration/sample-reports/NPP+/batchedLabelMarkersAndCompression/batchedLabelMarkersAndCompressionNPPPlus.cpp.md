# NPP+/batchedLabelMarkersAndCompression::batchedLabelMarkersAndCompressionNPPPlus.cpp

**PASSED / L4**

原始五输入/单图与异构batch、NPP+默认及CUDA11U1压缩分支完整；27组全像素/padding、44运行合同及3项默认/外设备/销毁stream、1..5 batch共15个完整流程/165文件、39CLI、31正反例/BFS、trace/冷检出/三复审通过。包括零值所有区域，编号按最小像素确定；当前NPP/NPP+原生分区错误单列，不复制厂商错误。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP+/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp](../../../../NPP+/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp) |
| 实际库 / 后端 | Project HIP equal-value 8-connected union/find + hierarchical GPU prefix-scan compression / project HIP CCL |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP+/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp](../../../../rocm/ported/NPP+/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp) |
| required cases | 37/37 |
| CUDA baseline / comparison | PASSED / OBSERVED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `27072de0ee98a324dc66c0a3be357e68dc49a0125800abfe7bc5c6e7a086e0fe` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`image-CCL/npp-lena`, `image-CCL/npp-CT_skull`, `image-CCL/npp-PCB_METAL`, `image-CCL/npp-PCB2`, `image-CCL/npp-PCB`, `image-CCL/plus-lena`, `image-CCL/plus-CT_skull`, `image-CCL/plus-PCB_METAL`, `image-CCL/plus-PCB2`, `image-CCL/plus-PCB`, `image-CCL/three-by-three-stale-root`, `image-CCL/one-pixel`, `image-CCL/single-row`, `image-CCL/single-column`, `image-CCL/scan-255`, `image-CCL/scan-256`, `image-CCL/scan-257`, `image-CCL/scan-recursive`, `image-CCL/constant-0`, `image-CCL/constant-1`, `image-CCL/constant-255`, `image-CCL/noise-847`, `image-CCL/noise-83827`, `image-CCL/noise-654981`, `image-CCL/diagonal-touch`, `image-CCL/frame-hole-and-island`, `image-CCL/long-serpentine-component`, `image-CCL/full-original-individual-and-heterogeneous-batch`, `image-CCL/all-five-batch-counts`, `image-CCL/conditional-batch-compression`, `image-CCL/actual-runtime-ABI-streams-instances`, `image-CCL/default-foreign-destroyed-streams`, `image-CCL/complete-CLI-errors-and-no-device`, `image-CCL/raw-GPU-dispatch`, `image-CCL/independent-BFS-and-validator-mutations`, `image-CCL/cold-checkout`, `image-CCL/independent-review`。

实现方式：`EXACT_CPU_PARTITION_ARBITRARY_VENDOR_IDS`。

恢复/扩展条件：修改连接、编号、类型、布局、范围或平台须重新冻结并实测。

CUDA 对照限制：54次真实API及55原始输出对独立CPU完整比较。3x3两库返回5分量，CPU/HIP为4；其它分裂/合并均逐输入记录，native程序成功不等于数学正确。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP+/batchedLabelMarkersAndCompression/dirent.h:28:10: fatal error: 'windows.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_m

尝试库：—；实现 hash：`ec23745b19076cdc893dd799ab9873f5ae8ee6656777e737ef1d2e0b47188f48`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python3 tools/moat/image_ccl_contracts.py
python3 tools/moat/image_ccl_build.py
python3 tools/moat/image_ccl_run.py
python3 tools/moat/image_ccl_originals.py
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/NPP+_batchedLabelMarkersAndCompression_batchedLabelMarkersAndCompressionNPPPlus.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/NPP+_batchedLabelMarkersAndCompression_batchedLabelMarkersAndCompressionNPPPlus.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP+_batchedLabelMarkersAndCompression_batchedLabelMarkersAndCompressionNPPPlus.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/NPP+_batchedLabelMarkersAndCompression_batchedLabelMarkersAndCompressionNPPPlus.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP+_batchedLabelMarkersAndCompression_batchedLabelMarkersAndCompressionNPPPlus.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/NPP+_batchedLabelMarkersAndCompression_batchedLabelMarkersAndCompressionNPPPlus.cpp)
- [migration/reports/image-ccl.md](../../../reports/image-ccl.md)
- [migration/reports/evidence/rewrite/I2/_batchedLabelMarkersAndCompression__batchedLabelMarkersAndCompressionNPPPlus.cpp/20261111T144109.140340Z-I2-composite-qualification-65f5bd66c5](../../../reports/evidence/rewrite/I2/_batchedLabelMarkersAndCompression__batchedLabelMarkersAndCompressionNPPPlus.cpp/20261111T144109.140340Z-I2-composite-qualification-65f5bd66c5)
- [migration/reports/evidence/rewrite/I2/CCL-clean-checkout/20261111T143320.085723Z-I2-host-cold-replay-17225690ca](../../../reports/evidence/rewrite/I2/CCL-clean-checkout/20261111T143320.085723Z-I2-host-cold-replay-17225690ca)
- [migration/reports/evidence/rewrite/I2/CCL-default-foreign-destroyed-streams/20261111T142925.706311Z-I2-rocm-streams-b6f1e3feb3](../../../reports/evidence/rewrite/I2/CCL-default-foreign-destroyed-streams/20261111T142925.706311Z-I2-rocm-streams-b6f1e3feb3)
- [migration/reports/evidence/rewrite/I2/CCL-frozen-contracts-and-golden-audit/20261111T141936.193470Z-I2-CPU-contract-d4eba7f9c1](../../../reports/evidence/rewrite/I2/CCL-frozen-contracts-and-golden-audit/20261111T141936.193470Z-I2-CPU-contract-d4eba7f9c1)
- [migration/reports/evidence/rewrite/I2/CCL-identity-bound-original-NPP/20261111T142747.149195Z-I2-cuda-original-8e556f6c69](../../../reports/evidence/rewrite/I2/CCL-identity-bound-original-NPP/20261111T142747.149195Z-I2-cuda-original-8e556f6c69)
- [migration/reports/evidence/rewrite/I2/CCL-identity-bound-original-NPP_/20261111T142750.231812Z-I2-cuda-original-97fe44d989](../../../reports/evidence/rewrite/I2/CCL-identity-bound-original-NPP_/20261111T142750.231812Z-I2-cuda-original-97fe44d989)
- [migration/reports/evidence/rewrite/I2/CCL-identity-bound-original-NPP_/20261111T142752.912766Z-I2-cuda-original-94a3770d94](../../../reports/evidence/rewrite/I2/CCL-identity-bound-original-NPP_/20261111T142752.912766Z-I2-cuda-original-94a3770d94)
- [migration/reports/evidence/rewrite/I2/CCL-independent-validator-mutations/20261111T143131.646449Z-I2-CPU-validator-test-6da204dc5c](../../../reports/evidence/rewrite/I2/CCL-independent-validator-mutations/20261111T143131.646449Z-I2-CPU-validator-test-6da204dc5c)
- [migration/reports/evidence/rewrite/I2/CCL-masks-independent-CPU/20261111T142924.645016Z-I2-CPU-reference-848b5dce94](../../../reports/evidence/rewrite/I2/CCL-masks-independent-CPU/20261111T142924.645016Z-I2-CPU-reference-848b5dce94)
- [migration/reports/evidence/rewrite/I2/CCL-masks/20261111T142757.225415Z-I2-rocm-masks-d7df156af8](../../../reports/evidence/rewrite/I2/CCL-masks/20261111T142757.225415Z-I2-rocm-masks-d7df156af8)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142341.948137Z-I2-cuda-run-532a275ec5](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142341.948137Z-I2-cuda-run-532a275ec5)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142344.726247Z-I2-cuda-run-d4a12c6d06](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142344.726247Z-I2-cuda-run-d4a12c6d06)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142347.533204Z-I2-cuda-run-04c78168af](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142347.533204Z-I2-cuda-run-04c78168af)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142350.288135Z-I2-cuda-run-45b455b011](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142350.288135Z-I2-cuda-run-45b455b011)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142353.095738Z-I2-cuda-run-bda0a70957](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142353.095738Z-I2-cuda-run-bda0a70957)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142355.860964Z-I2-cuda-run-085d4243ba](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142355.860964Z-I2-cuda-run-085d4243ba)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142358.627368Z-I2-cuda-run-39efc3576b](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142358.627368Z-I2-cuda-run-39efc3576b)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142401.398800Z-I2-cuda-run-8db828daf2](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142401.398800Z-I2-cuda-run-8db828daf2)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142404.177246Z-I2-cuda-run-105347d6ea](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142404.177246Z-I2-cuda-run-105347d6ea)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142407.020078Z-I2-cuda-run-2292947a1a](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142407.020078Z-I2-cuda-run-2292947a1a)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142409.835279Z-I2-cuda-run-576306475b](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142409.835279Z-I2-cuda-run-576306475b)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142412.585446Z-I2-cuda-run-1310a60649](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142412.585446Z-I2-cuda-run-1310a60649)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142415.367027Z-I2-cuda-run-02205eaa1a](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142415.367027Z-I2-cuda-run-02205eaa1a)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142418.114425Z-I2-cuda-run-7708f6ade5](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142418.114425Z-I2-cuda-run-7708f6ade5)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142420.888592Z-I2-cuda-run-ffb6df6c99](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142420.888592Z-I2-cuda-run-ffb6df6c99)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142423.710225Z-I2-cuda-run-9f01f20a22](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142423.710225Z-I2-cuda-run-9f01f20a22)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142426.476558Z-I2-cuda-run-9d5d680632](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142426.476558Z-I2-cuda-run-9d5d680632)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142429.137565Z-I2-cuda-run-30ae4bb0d2](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142429.137565Z-I2-cuda-run-30ae4bb0d2)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142431.980862Z-I2-cuda-run-9524fe32eb](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142431.980862Z-I2-cuda-run-9524fe32eb)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142434.694280Z-I2-cuda-run-6e2e1a5d63](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142434.694280Z-I2-cuda-run-6e2e1a5d63)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142437.404995Z-I2-cuda-run-ebcedce717](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142437.404995Z-I2-cuda-run-ebcedce717)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142440.135331Z-I2-cuda-run-7f2bcaacb7](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142440.135331Z-I2-cuda-run-7f2bcaacb7)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142442.896201Z-I2-cuda-run-992e1d56f4](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142442.896201Z-I2-cuda-run-992e1d56f4)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142445.602875Z-I2-cuda-run-ccdd283707](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142445.602875Z-I2-cuda-run-ccdd283707)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142448.363170Z-I2-cuda-run-955da45df2](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142448.363170Z-I2-cuda-run-955da45df2)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142451.105173Z-I2-cuda-run-5ad27a615e](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142451.105173Z-I2-cuda-run-5ad27a615e)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142453.857987Z-I2-cuda-run-9f69a2ebfb](../../../reports/evidence/rewrite/I2/CCL-native-NPP/20261111T142453.857987Z-I2-cuda-run-9f69a2ebfb)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142456.623855Z-I2-cuda-run-de481309be](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142456.623855Z-I2-cuda-run-de481309be)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142459.225810Z-I2-cuda-run-8497559817](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142459.225810Z-I2-cuda-run-8497559817)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142501.853073Z-I2-cuda-run-09d2fad74c](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142501.853073Z-I2-cuda-run-09d2fad74c)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142504.416503Z-I2-cuda-run-b2c479129f](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142504.416503Z-I2-cuda-run-b2c479129f)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142507.030321Z-I2-cuda-run-c001187302](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142507.030321Z-I2-cuda-run-c001187302)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142509.623337Z-I2-cuda-run-7f0947a357](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142509.623337Z-I2-cuda-run-7f0947a357)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142512.181529Z-I2-cuda-run-ad5f4e5058](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142512.181529Z-I2-cuda-run-ad5f4e5058)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142514.678887Z-I2-cuda-run-abf500614a](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142514.678887Z-I2-cuda-run-abf500614a)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142517.232663Z-I2-cuda-run-c483709242](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142517.232663Z-I2-cuda-run-c483709242)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142519.887938Z-I2-cuda-run-0ff351c34b](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142519.887938Z-I2-cuda-run-0ff351c34b)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142522.509125Z-I2-cuda-run-cec9666c79](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142522.509125Z-I2-cuda-run-cec9666c79)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142525.005744Z-I2-cuda-run-90a1e0a7d8](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142525.005744Z-I2-cuda-run-90a1e0a7d8)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142527.546321Z-I2-cuda-run-d895470098](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142527.546321Z-I2-cuda-run-d895470098)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142530.088572Z-I2-cuda-run-11bc89725c](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142530.088572Z-I2-cuda-run-11bc89725c)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142532.631371Z-I2-cuda-run-ef391b6c6d](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142532.631371Z-I2-cuda-run-ef391b6c6d)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142535.143787Z-I2-cuda-run-d91412047e](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142535.143787Z-I2-cuda-run-d91412047e)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142537.667369Z-I2-cuda-run-cedcb2fd56](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142537.667369Z-I2-cuda-run-cedcb2fd56)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142540.168938Z-I2-cuda-run-7c78d06596](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142540.168938Z-I2-cuda-run-7c78d06596)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142542.720298Z-I2-cuda-run-56bcce5503](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142542.720298Z-I2-cuda-run-56bcce5503)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142545.216835Z-I2-cuda-run-ca79a0975e](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142545.216835Z-I2-cuda-run-ca79a0975e)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142547.728192Z-I2-cuda-run-488802affb](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142547.728192Z-I2-cuda-run-488802affb)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142550.280207Z-I2-cuda-run-4875ad1a81](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142550.280207Z-I2-cuda-run-4875ad1a81)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142552.786051Z-I2-cuda-run-5840d35b2c](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142552.786051Z-I2-cuda-run-5840d35b2c)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142555.278939Z-I2-cuda-run-e3330d72f3](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142555.278939Z-I2-cuda-run-e3330d72f3)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142557.826211Z-I2-cuda-run-0b0e965a73](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142557.826211Z-I2-cuda-run-0b0e965a73)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142600.392914Z-I2-cuda-run-33daea2ec7](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142600.392914Z-I2-cuda-run-33daea2ec7)
- [migration/reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142602.895225Z-I2-cuda-run-ada95cfa55](../../../reports/evidence/rewrite/I2/CCL-native-NPP_/20261111T142602.895225Z-I2-cuda-run-ada95cfa55)
- [migration/reports/evidence/rewrite/I2/CCL-native-build/20261111T142330.558737Z-I2-cuda-build-75c96264fd](../../../reports/evidence/rewrite/I2/CCL-native-build/20261111T142330.558737Z-I2-cuda-build-75c96264fd)
- [migration/reports/evidence/rewrite/I2/CCL-native-independent-CPU/20261111T142929.425787Z-I2-CPU-reference-cbd9f79b7e](../../../reports/evidence/rewrite/I2/CCL-native-independent-CPU/20261111T142929.425787Z-I2-CPU-reference-cbd9f79b7e)
- [migration/reports/evidence/rewrite/I2/CCL-native-original-preflight-negative-tests/20261111T143230.137474Z-I2-CPU-selftest-f7d40c8c1f](../../../reports/evidence/rewrite/I2/CCL-native-original-preflight-negative-tests/20261111T143230.137474Z-I2-CPU-selftest-f7d40c8c1f)
- [migration/reports/evidence/rewrite/I2/CCL-native-original-preflight/20261111T142745.975342Z-I2-host-preflight-12a95b8d32](../../../reports/evidence/rewrite/I2/CCL-native-original-preflight/20261111T142745.975342Z-I2-host-preflight-12a95b8d32)
- [migration/reports/evidence/rewrite/I2/CCL-native-original-preflight/20261111T143230.757595Z-I2-host-preflight-afd2728f4a](../../../reports/evidence/rewrite/I2/CCL-native-original-preflight/20261111T143230.757595Z-I2-host-preflight-afd2728f4a)
- [migration/reports/evidence/rewrite/I2/CCL-native-original-preflight/20261111T143231.630112Z-I2-host-preflight-3b8ff57a83](../../../reports/evidence/rewrite/I2/CCL-native-original-preflight/20261111T143231.630112Z-I2-host-preflight-3b8ff57a83)
- [migration/reports/evidence/rewrite/I2/CCL-native-original-preflight/20261111T143232.493210Z-I2-host-preflight-5c7873f0d5](../../../reports/evidence/rewrite/I2/CCL-native-original-preflight/20261111T143232.493210Z-I2-host-preflight-5c7873f0d5)
- [migration/reports/evidence/rewrite/I2/CCL-native-originals-independent-CPU/20261111T142934.314604Z-I2-CPU-reference-54911f7bcf](../../../reports/evidence/rewrite/I2/CCL-native-originals-independent-CPU/20261111T142934.314604Z-I2-CPU-reference-54911f7bcf)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142817.632650Z-I2-rocm-original-3b4d8d29c5](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142817.632650Z-I2-rocm-original-3b4d8d29c5)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142819.976555Z-I2-rocm-original-4995193f51](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142819.976555Z-I2-rocm-original-4995193f51)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142822.017599Z-I2-rocm-original-4aa51ea63e](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142822.017599Z-I2-rocm-original-4aa51ea63e)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142824.035564Z-I2-rocm-original-b6f1e62833](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142824.035564Z-I2-rocm-original-b6f1e62833)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142826.060615Z-I2-rocm-original-c620b9dd85](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142826.060615Z-I2-rocm-original-c620b9dd85)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142851.375598Z-I2-rocm-CLI-b531d8ab34](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142851.375598Z-I2-rocm-CLI-b531d8ab34)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142853.803792Z-I2-rocm-CLI-c4821a7b52](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142853.803792Z-I2-rocm-CLI-c4821a7b52)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142855.628816Z-I2-rocm-CLI-5837422f74](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142855.628816Z-I2-rocm-CLI-5837422f74)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142857.412546Z-I2-rocm-CLI-68e4bc1cb1](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142857.412546Z-I2-rocm-CLI-68e4bc1cb1)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142859.162855Z-I2-rocm-CLI-c181414744](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142859.162855Z-I2-rocm-CLI-c181414744)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142900.957506Z-I2-rocm-CLI-9d9e3b8c92](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142900.957506Z-I2-rocm-CLI-9d9e3b8c92)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142902.768689Z-I2-rocm-CLI-2ebd4a0f6f](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142902.768689Z-I2-rocm-CLI-2ebd4a0f6f)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142904.585486Z-I2-rocm-CLI-10aa6c395f](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142904.585486Z-I2-rocm-CLI-10aa6c395f)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142906.356334Z-I2-rocm-CLI-5f8b614233](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142906.356334Z-I2-rocm-CLI-5f8b614233)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142908.145160Z-I2-rocm-CLI-6519f2fd81](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142908.145160Z-I2-rocm-CLI-6519f2fd81)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142910.059847Z-I2-rocm-CLI-a2e9c7fb0c](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142910.059847Z-I2-rocm-CLI-a2e9c7fb0c)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142912.009771Z-I2-rocm-CLI-c001c270b1](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142912.009771Z-I2-rocm-CLI-c001c270b1)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142914.013437Z-I2-rocm-CLI-c92888756e](../../../reports/evidence/rewrite/I2/CCL-original-NPP/20261111T142914.013437Z-I2-rocm-CLI-c92888756e)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142828.158506Z-I2-rocm-original-937aeb96aa](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142828.158506Z-I2-rocm-original-937aeb96aa)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142830.105677Z-I2-rocm-original-befa1d596d](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142830.105677Z-I2-rocm-original-befa1d596d)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142832.070579Z-I2-rocm-original-f29ebced2b](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142832.070579Z-I2-rocm-original-f29ebced2b)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142834.170743Z-I2-rocm-original-d9e9d4d5f4](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142834.170743Z-I2-rocm-original-d9e9d4d5f4)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142836.154059Z-I2-rocm-original-34cd822a47](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142836.154059Z-I2-rocm-original-34cd822a47)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142838.209205Z-I2-rocm-original-f3a9787f1d](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142838.209205Z-I2-rocm-original-f3a9787f1d)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142840.282910Z-I2-rocm-original-46d206152f](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142840.282910Z-I2-rocm-original-46d206152f)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142842.300285Z-I2-rocm-original-5536030b2f](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142842.300285Z-I2-rocm-original-5536030b2f)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142844.346915Z-I2-rocm-original-1db7ed034d](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142844.346915Z-I2-rocm-original-1db7ed034d)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142846.381011Z-I2-rocm-original-6f5b2a9af4](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142846.381011Z-I2-rocm-original-6f5b2a9af4)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142915.973473Z-I2-rocm-CLI-f044fc2702](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142915.973473Z-I2-rocm-CLI-f044fc2702)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142918.058809Z-I2-rocm-CLI-f315ee3390](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142918.058809Z-I2-rocm-CLI-f315ee3390)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142919.841582Z-I2-rocm-CLI-aedc9b272d](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142919.841582Z-I2-rocm-CLI-aedc9b272d)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142921.603382Z-I2-rocm-CLI-43504397f0](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142921.603382Z-I2-rocm-CLI-43504397f0)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142923.394829Z-I2-rocm-CLI-b908987622](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142923.394829Z-I2-rocm-CLI-b908987622)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142925.208676Z-I2-rocm-CLI-9ae7f360cc](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142925.208676Z-I2-rocm-CLI-9ae7f360cc)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142927.012323Z-I2-rocm-CLI-4acb3ee186](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142927.012323Z-I2-rocm-CLI-4acb3ee186)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142928.970801Z-I2-rocm-CLI-7afc198dcb](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142928.970801Z-I2-rocm-CLI-7afc198dcb)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142930.756075Z-I2-rocm-CLI-967f01c1e5](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142930.756075Z-I2-rocm-CLI-967f01c1e5)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142932.617349Z-I2-rocm-CLI-05a033b47b](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142932.617349Z-I2-rocm-CLI-05a033b47b)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142934.564002Z-I2-rocm-CLI-74ddd78373](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142934.564002Z-I2-rocm-CLI-74ddd78373)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142936.495002Z-I2-rocm-CLI-ec2212c397](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142936.495002Z-I2-rocm-CLI-ec2212c397)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142938.518054Z-I2-rocm-CLI-b791870aca](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142938.518054Z-I2-rocm-CLI-b791870aca)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142940.500905Z-I2-rocm-CLI-903c12a94b](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142940.500905Z-I2-rocm-CLI-903c12a94b)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142942.599782Z-I2-rocm-CLI-188927d42e](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142942.599782Z-I2-rocm-CLI-188927d42e)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142944.391430Z-I2-rocm-CLI-f6db5c70fd](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142944.391430Z-I2-rocm-CLI-f6db5c70fd)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142946.222802Z-I2-rocm-CLI-aff7c400a1](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142946.222802Z-I2-rocm-CLI-aff7c400a1)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142948.012479Z-I2-rocm-CLI-a4e7380524](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142948.012479Z-I2-rocm-CLI-a4e7380524)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142949.783999Z-I2-rocm-CLI-558b1cbcdd](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142949.783999Z-I2-rocm-CLI-558b1cbcdd)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142951.582752Z-I2-rocm-CLI-b8033b7610](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142951.582752Z-I2-rocm-CLI-b8033b7610)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142953.364118Z-I2-rocm-CLI-5aa5893fa5](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142953.364118Z-I2-rocm-CLI-5aa5893fa5)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142955.115710Z-I2-rocm-CLI-3a991c9aa5](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142955.115710Z-I2-rocm-CLI-3a991c9aa5)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142956.928499Z-I2-rocm-CLI-8533269ca5](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142956.928499Z-I2-rocm-CLI-8533269ca5)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142958.857544Z-I2-rocm-CLI-90251b12bc](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T142958.857544Z-I2-rocm-CLI-90251b12bc)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T143000.845312Z-I2-rocm-CLI-ce2c76cfa8](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T143000.845312Z-I2-rocm-CLI-ce2c76cfa8)
- [migration/reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T143002.826782Z-I2-rocm-CLI-ef061c6be1](../../../reports/evidence/rewrite/I2/CCL-original-NPP_/20261111T143002.826782Z-I2-rocm-CLI-ef061c6be1)
- [migration/reports/evidence/rewrite/I2/CCL-original-cli-independent-CPU/20261111T143129.958025Z-I2-CPU-reference-b6320a61ca](../../../reports/evidence/rewrite/I2/CCL-original-cli-independent-CPU/20261111T143129.958025Z-I2-CPU-reference-b6320a61ca)
- [migration/reports/evidence/rewrite/I2/CCL-original-originals-independent-CPU/20261111T143127.840539Z-I2-CPU-reference-989c5e8f37](../../../reports/evidence/rewrite/I2/CCL-original-originals-independent-CPU/20261111T143127.840539Z-I2-CPU-reference-989c5e8f37)
- [migration/reports/evidence/rewrite/I2/CCL-runtime-independent-CPU/20261111T142926.308940Z-I2-CPU-reference-609a5c7ad9](../../../reports/evidence/rewrite/I2/CCL-runtime-independent-CPU/20261111T142926.308940Z-I2-CPU-reference-609a5c7ad9)
- [migration/reports/evidence/rewrite/I2/CCL-runtime/20261111T142804.124793Z-I2-rocm-runtime-e4dcd28269](../../../reports/evidence/rewrite/I2/CCL-runtime/20261111T142804.124793Z-I2-rocm-runtime-e4dcd28269)
- [migration/reports/evidence/rewrite/I2/CCL-shared-GPU-and-original-build/20261111T142747.097863Z-I2-rocm-build-d0924b4190](../../../reports/evidence/rewrite/I2/CCL-shared-GPU-and-original-build/20261111T142747.097863Z-I2-rocm-build-d0924b4190)
- [migration/reports/evidence/rewrite/I2/CCL-streams-independent-CPU/20261111T143126.531018Z-I2-CPU-reference-4f3627f437](../../../reports/evidence/rewrite/I2/CCL-streams-independent-CPU/20261111T143126.531018Z-I2-CPU-reference-4f3627f437)
- [migration/reports/evidence/rewrite/I2/CCL-trace-independent-CPU/20261111T142927.675646Z-I2-CPU-reference-2f1a8506ff](../../../reports/evidence/rewrite/I2/CCL-trace-independent-CPU/20261111T142927.675646Z-I2-CPU-reference-2f1a8506ff)
- [migration/reports/evidence/rewrite/I2/CCL-trace/20261111T142810.540767Z-I2-rocm-trace-5998506c21](../../../reports/evidence/rewrite/I2/CCL-trace/20261111T142810.540767Z-I2-rocm-trace-5998506c21)
