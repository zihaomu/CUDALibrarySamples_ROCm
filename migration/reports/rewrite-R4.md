# R4 CRC32 验收

IEEE/PKZIP CRC32采用项目HIP GPU kernel。hipCOMP锁定公开头文件无对应CRC32 API，选择依据见[路线探针](rewrite-crc32-route.json)。不是CRC32C。

6个数值场景逐chunk通过独立zlib和真实native nvCOMP；另1个零chunk场景按原生语义拒绝，native退出-6、项目退出1。保持每文件65536字节分块、-f多文件、2次warmup/5次总迭代及GPU event计时。

[复合资格](rewrite-R4-qualification.json)、[独立复审](rewrite-R4-review.json)、[AMD/CPU](rewrite-crc32-rocm-validation.json)、[CUDA/CPU](rewrite-crc32-cuda-validation.json)、[8项故障注入](rewrite-crc32-negative.json)、[5项CLI](rewrite-crc32-runtime.json)、[实际5次GPU核](rewrite-crc32-trace.json)。

其它R4方向仍在逐项任务队列，未用本例结果外推codec或低精度功能。性能没有跨设备速度结论。
