# NPP+/cannyEdgeDetectorPython::cannyEdgeDetector.py

**PASSED / L4**

完整C1原例8分辨率、5 warmup/1000测量及PNG/CSV通过；31组最终mask与独立CPU逐像素一致，native NPP+全部内部像素一致，仅两研究用例合计3外圈点不同。两stream/并发/类型转换/非法span与trace、验收器反向和独立复审通过。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py](../../../../NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py) |
| 实际库 / 后端 | Project HIP Canny + ROCm Torch (C1 Sobel3/L2/local threshold) / project HIP image C ABI |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py](../../../../rocm/ported/NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py) |
| required cases | 36/36 |
| CUDA baseline / comparison | BLOCKED / PASSED |
| 性能 | NOT_QUALIFIED |
| 原始源码 SHA256 | `74c58b322283e9979d26a793b915291db457f2a4c33515947e82608c4ee1fe16` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`image/original-320x180`, `image/original-640x360`, `image/original-800x600`, `image/original-1280x720`, `image/original-1920x1080`, `image/original-2560x1440`, `image/original-3840x2160`, `image/original-5120x2880`, `image/registered-teapot-c1`, `image/registered-noise-c1`, `image/registered-ties-c1`, `image/registered-step-c1`, `image/registered-tiny-c1`, `image/registered-holdout-weak-step-c1`, `image/registered-holdout-weak-cross-c1`, `image/registered-holdout-weak-diagonal-c1`, `image/registered-holdout-low-noise-c1`, `image/registered-holdout-mixed-noise-c1`, `image/registered-border-check91203-c1`, `image/registered-border-check40519-c1`, `image/registered-border-check83914-c1`, `image/new-one-pixel`, `image/new-single-row`, `image/new-single-column`, `image/new-flat`, `image/new-odd-noise`, `image/new-boundary-step`, `image/new-weak-cross`, `image/new-impulse`, `image/new-equal-threshold`, `image/new-high-threshold`, `image/full-original-8-sizes-1000-loops`, `image/runtime-and-ABI`, `image/GPU-trace`, `image/positive-negative-validator`, `image/independent-review`。

实现方式：`ALGORITHM_VARIANT`。

恢复/扩展条件：扩展kernel/算法/dtype/布局/平台或性能声明时重新冻结合同并实测。

CUDA 对照限制：同字节输入、同阈值、NPP+真实API及SDK/二进制回执；完整内部mask一致，3个外圈差异按项目明确边界规则接受。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python3 tools/moat/canny_plus_build.py
python3 tools/moat/canny_plus_run.py
python3 tools/moat/canny_plus_run.py --original
```

- [migration/reports/evidence/20261109T084354.110802Z/languages/NPP+_cannyEdgeDetectorPython_cannyEdgeDetector.py](../../../reports/evidence/20261109T084354.110802Z/languages/NPP+_cannyEdgeDetectorPython_cannyEdgeDetector.py)
- [migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/NPP+_cannyEdgeDetectorPython_cannyEdgeDetector.py](../../../reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/NPP+_cannyEdgeDetectorPython_cannyEdgeDetector.py)
- [migration/reports/canny-plus.md](../../../reports/canny-plus.md)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T123200.693229Z-I1-composite-qualification-51ce42c058](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T123200.693229Z-I1-composite-qualification-51ce42c058)
- [migration/reports/evidence/rewrite/I1/CannyPlus-acceptance-mutations/20261111T122016.417050Z-I1-CPU-validator-test-99c40e5688](../../../reports/evidence/rewrite/I1/CannyPlus-acceptance-mutations/20261111T122016.417050Z-I1-CPU-validator-test-99c40e5688)
- [migration/reports/evidence/rewrite/I1/CannyPlus-clean-checkout/20261111T122544.406349Z-I1-host-cold-replay-4540da489b](../../../reports/evidence/rewrite/I1/CannyPlus-clean-checkout/20261111T122544.406349Z-I1-host-cold-replay-4540da489b)
- [migration/reports/evidence/rewrite/I1/CannyPlus-contract-and-fixtures/20261111T115003.674180Z-I1-CPU-fixtures-41b974229d](../../../reports/evidence/rewrite/I1/CannyPlus-contract-and-fixtures/20261111T115003.674180Z-I1-CPU-fixtures-41b974229d)
- [migration/reports/evidence/rewrite/I1/CannyPlus-deterministic-fixture-replay/20261111T121328.945896Z-I1-CPU-fixtures-5afa78314d](../../../reports/evidence/rewrite/I1/CannyPlus-deterministic-fixture-replay/20261111T121328.945896Z-I1-CPU-fixtures-5afa78314d)
- [migration/reports/evidence/rewrite/I1/CannyPlus-full-library-build/20261111T115553.659333Z-I1-rocm-build-7d346fc325](../../../reports/evidence/rewrite/I1/CannyPlus-full-library-build/20261111T115553.659333Z-I1-rocm-build-7d346fc325)
- [migration/reports/evidence/rewrite/I1/CannyPlus-private-Python-dependencies/20261111T121742.460205Z-I1-rocm-setup-ff119bde51](../../../reports/evidence/rewrite/I1/CannyPlus-private-Python-dependencies/20261111T121742.460205Z-I1-rocm-setup-ff119bde51)
- [migration/reports/evidence/rewrite/I1/CannyPlus-runtime-independent-CPU/20261111T122015.228557Z-I1-CPU-reference-ef78184026](../../../reports/evidence/rewrite/I1/CannyPlus-runtime-independent-CPU/20261111T122015.228557Z-I1-CPU-reference-ef78184026)
- [migration/reports/evidence/rewrite/I1/CannyPlus-runtime/20261111T121908.423889Z-I1-rocm-runtime-0da5ed7409](../../../reports/evidence/rewrite/I1/CannyPlus-runtime/20261111T121908.423889Z-I1-rocm-runtime-0da5ed7409)
- [migration/reports/evidence/rewrite/I1/CannyPlus-runtime/20261111T121934.116530Z-I1-rocm-trace-fddd584fae](../../../reports/evidence/rewrite/I1/CannyPlus-runtime/20261111T121934.116530Z-I1-rocm-trace-fddd584fae)
- [migration/reports/evidence/rewrite/I1/CannyPlus-trace-independent-CPU/20261111T122015.237954Z-I1-CPU-reference-b2783c37e8](../../../reports/evidence/rewrite/I1/CannyPlus-trace-independent-CPU/20261111T122015.237954Z-I1-CPU-reference-b2783c37e8)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115300.937762Z-I1-cuda-build-f2915ac7e8](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115300.937762Z-I1-cuda-build-f2915ac7e8)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115306.980713Z-I1-cuda-run-f07192705e](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115306.980713Z-I1-cuda-run-f07192705e)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115309.154940Z-I1-cuda-run-7639356b14](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115309.154940Z-I1-cuda-run-7639356b14)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115311.319332Z-I1-cuda-run-78bb1c020a](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115311.319332Z-I1-cuda-run-78bb1c020a)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115313.472886Z-I1-cuda-run-5a848bf6d4](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115313.472886Z-I1-cuda-run-5a848bf6d4)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115315.627011Z-I1-cuda-run-7fbfce63a0](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115315.627011Z-I1-cuda-run-7fbfce63a0)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115317.804071Z-I1-cuda-run-a8c18b232e](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115317.804071Z-I1-cuda-run-a8c18b232e)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115320.180514Z-I1-cuda-run-47795c14f4](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115320.180514Z-I1-cuda-run-47795c14f4)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115322.459249Z-I1-cuda-run-0f42b755fe](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115322.459249Z-I1-cuda-run-0f42b755fe)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115324.882083Z-I1-cuda-run-43703888a9](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115324.882083Z-I1-cuda-run-43703888a9)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115327.058655Z-I1-cuda-run-13b3a2a0e3](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115327.058655Z-I1-cuda-run-13b3a2a0e3)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115329.169107Z-I1-cuda-run-d50910a0ca](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115329.169107Z-I1-cuda-run-d50910a0ca)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115331.322603Z-I1-cuda-run-7260a00436](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115331.322603Z-I1-cuda-run-7260a00436)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115333.470564Z-I1-cuda-run-1134fd7213](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115333.470564Z-I1-cuda-run-1134fd7213)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115335.583947Z-I1-cuda-run-60f4aad25d](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115335.583947Z-I1-cuda-run-60f4aad25d)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115337.737359Z-I1-cuda-run-a9b4d777e7](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115337.737359Z-I1-cuda-run-a9b4d777e7)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115339.893288Z-I1-cuda-run-9ba7b65182](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115339.893288Z-I1-cuda-run-9ba7b65182)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115342.055493Z-I1-cuda-run-9496894607](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115342.055493Z-I1-cuda-run-9496894607)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115344.162547Z-I1-cuda-run-6d33575ad3](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115344.162547Z-I1-cuda-run-6d33575ad3)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115346.277769Z-I1-cuda-run-04119c3a56](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115346.277769Z-I1-cuda-run-04119c3a56)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115348.416047Z-I1-cuda-run-d5a1b50e67](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115348.416047Z-I1-cuda-run-d5a1b50e67)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115350.583320Z-I1-cuda-run-3788c724fe](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115350.583320Z-I1-cuda-run-3788c724fe)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115352.861717Z-I1-cuda-run-4a0086837c](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115352.861717Z-I1-cuda-run-4a0086837c)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115355.028919Z-I1-cuda-run-ebe36769d8](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115355.028919Z-I1-cuda-run-ebe36769d8)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115357.101176Z-I1-cuda-run-556f196771](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115357.101176Z-I1-cuda-run-556f196771)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115359.367731Z-I1-cuda-run-f30552c5f5](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115359.367731Z-I1-cuda-run-f30552c5f5)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115401.468654Z-I1-cuda-run-24df5fd16f](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115401.468654Z-I1-cuda-run-24df5fd16f)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115403.666275Z-I1-cuda-run-ba4d0c12fb](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115403.666275Z-I1-cuda-run-ba4d0c12fb)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115405.820704Z-I1-cuda-run-ea7016c0c5](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115405.820704Z-I1-cuda-run-ea7016c0c5)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115408.200773Z-I1-cuda-run-86fee144a0](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115408.200773Z-I1-cuda-run-86fee144a0)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115410.422795Z-I1-cuda-run-53700c91dd](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115410.422795Z-I1-cuda-run-53700c91dd)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115412.564522Z-I1-cuda-run-d5e13d29f7](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115412.564522Z-I1-cuda-run-d5e13d29f7)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115739.481820Z-I1-rocm-run-575b7c18ef](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115739.481820Z-I1-rocm-run-575b7c18ef)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115904.142381Z-I1-rocm-original-b47a08dd56](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T115904.142381Z-I1-rocm-original-b47a08dd56)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T120725.476677Z-I1-cuda-original-d5f71ef0a7](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T120725.476677Z-I1-cuda-original-d5f71ef0a7)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T120835.898910Z-I1-CPU-original-fecc4d7fdd](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T120835.898910Z-I1-CPU-original-fecc4d7fdd)
- [migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T120835.899416Z-I1-CPU-reference-919c2d65a9](../../../reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T120835.899416Z-I1-CPU-reference-919c2d65a9)
