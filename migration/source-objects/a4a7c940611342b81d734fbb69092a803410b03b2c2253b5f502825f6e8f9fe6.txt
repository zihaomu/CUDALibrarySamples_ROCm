/*
 * SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#pragma once

#include <iostream>
#include <iomanip>
#include <fstream>
#include <functional>
#include <stdexcept>
#include <string>
#include <vector>
#include <functional>

#include <hip/hip_runtime.h>

#ifndef CUDA_CHECK
#define CUDA_CHECK(func)                                                                                               \
  do {                                                                                                                 \
    hipError_t rt = (func);                                                                                           \
    if (rt != hipSuccess) {                                                                                           \
      const char* str = hipGetErrorString(rt);                                                                        \
      std::cerr << "CUDA Runtime failure \"" #func "\" with " << rt << " at " << __FILE__ << ":" << __LINE__           \
                << std::endl;                                                                                          \
      std::cerr << str << std::endl;                                                                                   \
      std::exit(1);                                                                                                    \
    }                                                                                                                  \
  } while (0)
#endif // CUDA_CHECK

#ifndef CU_CHECK
#define CU_CHECK(func)                                                                                                 \
  do {                                                                                                                 \
    hipError_t rt = (func);                                                                                              \
    if (rt != hipSuccess) {                                                                                          \
      const char* str;                                                                                                 \
      hipDrvGetErrorString(rt, &str);                                                                                      \
      std::cerr << "CUDA Driver failure \"" #func "\" with " << rt << " at " << __FILE__ << ":" << __LINE__            \
                << std::endl;                                                                                          \
      std::cerr << str << std::endl;                                                                                   \
      std::exit(1);                                                                                                    \
    }                                                                                                                  \
  } while (0)
#endif // CU_CHECK

size_t compute_batch_size(const std::vector<std::vector<char>>& data, const size_t chunk_size) {
  size_t batch_size = 0;
  for (size_t i = 0; i < data.size(); ++i) {
    const size_t num_chunks = nvcompdx::detail::roundUpDiv(data[i].size(), chunk_size);
    batch_size += num_chunks;
  }
  return batch_size;
}

std::vector<size_t>
compute_chunk_sizes(const std::vector<std::vector<char>>& data, const size_t batch_size, const size_t chunk_size) {
  std::vector<size_t> sizes(batch_size, chunk_size);

  size_t offset = 0;
  for (size_t i = 0; i < data.size(); ++i) {
    const size_t num_chunks = nvcompdx::detail::roundUpDiv(data[i].size(), chunk_size);
    offset += num_chunks;
    if (data[i].size() % chunk_size != 0) {
      sizes[offset - 1] = data[i].size() % chunk_size;
    }
  }
  return sizes;
}

std::vector<const void*>
compute_input_ptrs(const std::vector<std::vector<char>>& data, const size_t batch_size, const size_t chunk_size) {
  std::vector<const void*> input_ptrs(batch_size);
  size_t chunk = 0;
  for (size_t i = 0; i < data.size(); ++i) {
    const size_t num_chunks = nvcompdx::detail::roundUpDiv(data[i].size(), chunk_size);
    for (size_t j = 0; j < num_chunks; ++j) {
      input_ptrs[chunk++] = static_cast<const void*>(data[i].data() + j * chunk_size);
    }
  }
  return input_ptrs;
}

std::vector<char> read_file(const std::string& filename) {
  std::ifstream fin(filename, std::ifstream::in | std::ifstream::binary | std::ifstream::ate);
  if (!fin) {
    throw std::runtime_error("Unable to open file: " + filename);
  }
  fin.exceptions(std::ifstream::failbit | std::ifstream::badbit);

  // Query size
  size_t size = fin.tellg();
  fin.seekg(0, std::ifstream::beg);

  // Read the file
  std::vector<char> host_data(size);
  fin.read(host_data.data(), size);

  return host_data;
}

void write_file(const std::string& filename, std::vector<char>& data) {
  std::ofstream fout(filename, std::ofstream::out | std::ofstream::binary);
  fout.exceptions(std::ofstream::failbit | std::ofstream::badbit);
  fout.write(data.data(), data.size());
  fout.close();
}

std::vector<std::vector<char>> multi_file(const std::vector<std::string>& filenames) {
  std::vector<std::vector<char>> split_data;

  for (const auto& filename : filenames) {
    split_data.emplace_back(read_file(filename));
  }

  return split_data;
}

float measure_ms(
  const size_t warmup_iteration_count,
  const size_t total_iteration_count,
  hipStream_t stream,
  const std::function<void()>& fn) {
  hipEvent_t start, end;
  CUDA_CHECK(hipEventCreate(&start));
  CUDA_CHECK(hipEventCreate(&end));

  // Run warm-ups
  for (size_t iter = 0; iter < warmup_iteration_count; ++iter) {
    fn();
  }

  // Re-run for timing
  CUDA_CHECK(hipEventRecord(start, stream));
  for (size_t iter = warmup_iteration_count; iter < total_iteration_count; ++iter) {
    fn();
  }
  CUDA_CHECK(hipEventRecord(end, stream));
  CUDA_CHECK(hipStreamSynchronize(stream));

  float ms;
  CUDA_CHECK(hipEventElapsedTime(&ms, start, end));
  ms /= total_iteration_count - warmup_iteration_count;

  CUDA_CHECK(hipEventDestroy(start));
  CUDA_CHECK(hipEventDestroy(end));
  return ms;
}

unsigned int get_current_device_architecture() {
  int device;
  CUDA_CHECK(hipGetDevice(&device));
  int major = 0;
  int minor = 0;
  CUDA_CHECK(hipDeviceGetAttribute(&major, hipDeviceAttributeComputeCapabilityMajor, device));
  CUDA_CHECK(hipDeviceGetAttribute(&minor, hipDeviceAttributeComputeCapabilityMinor, device));
  return static_cast<unsigned int>(major * 10 + minor);
}

template <template <unsigned int> class Runner, typename... Args>
int run_with_current_arch(Args&&... args) {
  unsigned int current_device_arch = 10 * get_current_device_architecture();
  switch (current_device_arch) {
// Archs supported by nvCOMPDx
#ifdef NVCOMPDX_EXAMPLE_ENABLE_SM_75
    case 750:
      return Runner<750>::run(std::forward<Args>(args)...);
#endif
#ifdef NVCOMPDX_EXAMPLE_ENABLE_SM_80
    case 800:
      return Runner<800>::run(std::forward<Args>(args)...);
#endif
#ifdef NVCOMPDX_EXAMPLE_ENABLE_SM_86
    case 860:
      return Runner<860>::run(std::forward<Args>(args)...);
#endif
#ifdef NVCOMPDX_EXAMPLE_ENABLE_SM_87
    case 870:
      return Runner<870>::run(std::forward<Args>(args)...);
#endif
#ifdef NVCOMPDX_EXAMPLE_ENABLE_SM_89
    case 890:
      return Runner<890>::run(std::forward<Args>(args)...);
#endif
#ifdef NVCOMPDX_EXAMPLE_ENABLE_SM_90
    case 900:
      return Runner<900>::run(std::forward<Args>(args)...);
#endif
#ifdef NVCOMPDX_EXAMPLE_ENABLE_SM_100
    case 1000:
      return Runner<1000>::run(std::forward<Args>(args)...);
#endif
#ifdef NVCOMPDX_EXAMPLE_ENABLE_SM_103
    case 1030:
      return Runner<1030>::run(std::forward<Args>(args)...);
#endif
#ifdef NVCOMPDX_EXAMPLE_ENABLE_SM_110
    case 1100:
      return Runner<1100>::run(std::forward<Args>(args)...);
#endif
#ifdef NVCOMPDX_EXAMPLE_ENABLE_SM_120
    case 1200:
      return Runner<1200>::run(std::forward<Args>(args)...);
#endif
#ifdef NVCOMPDX_EXAMPLE_ENABLE_SM_121
    case 1210:
      return Runner<1210>::run(std::forward<Args>(args)...);
#endif
    default: {
      // Fail
      std::cerr << "Error:" << std::endl;
      std::cerr << "The current device architecture was not enabled during compilation." << std::endl;
      std::cerr << "Ensure that the 'NVCOMPDX_CUDA_ARCHITECTURES' CMake variable contains" << std::endl;
      std::cerr << "your current architecture (" << current_device_arch / 10 << ")." << std::endl;
      return 1;
    }
  }
}
