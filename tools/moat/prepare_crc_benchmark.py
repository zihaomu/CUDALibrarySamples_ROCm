#!/usr/bin/env python3
"""Keep the upstream benchmark harness, with explicit backend and observation hooks."""
from experiment import ROOT

def prepare(native=False):
 source=ROOT/'nvCOMP/benchmarks/benchmark_crc32.cpp';text=source.read_text()
 if native:text='#define RW_BENCH_NATIVE\n#include "crc_benchmark_observe.hpp"\n'+text
 else:
  text=text.replace('#include <cuda_runtime.h>','#include "crc_benchmark_compat.hpp"').replace('#include "benchmark_common.h"','').replace('#include "nvcomp.h"','').replace('#include <curand.h>','')
 replacements={
  'CUDA_CHECK(cudaMemGetInfo(&free_mem, &total_mem));':'CUDA_CHECK(cudaMemGetInfo(&free_mem, &total_mem));\n  cb_memory(total_mem, free_mem);',
  'CURAND_CHECK(curandDestroyGenerator(gen));':'CURAND_CHECK(curandDestroyGenerator(gen));\n  cb_input(storage_buf, storage_size);',
  'CUDA_CHECK(cudaEventElapsedTime(&elapsed_ms, start_, stop_));':'CUDA_CHECK(cudaEventElapsedTime(&elapsed_ms, start_, stop_));\n  cb_cell(buf_size, buf_count, crc_results_d_, elapsed_ms, kernel_conf);',
  'ThroughputTable table = make_throughput_table(args);':'ThroughputTable table = make_throughput_table(args);\n    cb_config(args, table);\n    if(table.buf_sizes.empty() || table.buf_counts.empty()) throw std::runtime_error("storage cannot contain a minimum-sized buffer");'}
 for a,b in replacements.items():
  if text.count(a)!=1:raise ValueError('Original benchmark marker changed: '+a)
  text=text.replace(a,b)
 return text
if __name__=='__main__':
 p=ROOT/'rocm/ported/nvCOMP/benchmarks/benchmark_crc32.cpp';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(prepare());print('Original CRC benchmark harness preserved with explicit HIP backend')
