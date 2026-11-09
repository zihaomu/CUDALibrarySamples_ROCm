# cuDSS/simple::simple.cpp 的 ROCm 实现

使用 CPU 稀疏图消去构造符号 L pattern，rocSOLVER CSRRF 在 GPU 上完成稀疏 Cholesky 数值分解和求解；保留原始 FP64 upper-CSR 5×5 SPD 与 RHS，解/残差及缩放矩阵检查通过。未转 dense；高级 cuDSS 接口未覆盖。

[逐例状态、命令与证据](../../../migration/sample-reports/cuDSS/simple/simple.cpp.md)
