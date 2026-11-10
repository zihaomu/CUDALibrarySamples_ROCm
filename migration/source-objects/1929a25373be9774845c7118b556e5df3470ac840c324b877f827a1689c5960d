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

#include "hip/hip_runtime.h"
#pragma once

#include <iostream>
#include <memory>
#include <cstdlib>

#include <hip/hiprtc.h>
#include <nvJitLink.h>

#ifndef NVRTC_CHECK
#define NVRTC_CHECK(func)                                                                                              \
  do {                                                                                                                 \
    hiprtcResult rt = (func);                                                                                           \
    if (rt != HIPRTC_SUCCESS) {                                                                                         \
      const char* str = hiprtcGetErrorString(rt);                                                                       \
      std::cerr << "NVRTC call failure \"" #func "\" with " << rt << " at " << __FILE__ << ":" << __LINE__             \
                << std::endl;                                                                                          \
      std::cerr << str << std::endl;                                                                                   \
      std::exit(1);                                                                                                    \
    }                                                                                                                  \
  } while (0)
#endif // NVRTC_CHECK

#ifndef NVJITLINK_CHECK
#define NVJITLINK_CHECK(handle, func)                                                                                  \
  do {                                                                                                                 \
    nvJitLinkResult rt = (func);                                                                                       \
    if (rt != NVJITLINK_SUCCESS) {                                                                                     \
      std::cerr << "NVJITLINK call failure \"" #func "\" with " << rt << " at " << __FILE__ << ":" << __LINE__         \
                << std::endl;                                                                                          \
      size_t log_size;                                                                                                 \
      rt = nvJitLinkGetErrorLogSize(handle, &log_size);                                                                \
      if (rt == NVJITLINK_SUCCESS && log_size > 0) {                                                                   \
        auto log = std::make_unique<char[]>(log_size);                                                                 \
        rt = nvJitLinkGetErrorLog(handle, log.get());                                                                  \
        if (rt == NVJITLINK_SUCCESS) {                                                                                 \
          std::cerr << log.get() << std::endl;                                                                         \
        }                                                                                                              \
      }                                                                                                                \
      std::exit(1);                                                                                                    \
    }                                                                                                                  \
  } while (0)
#endif // NVJITLINK_CHECK

void print_nvrtc_program_log(std::ostream& os, const hiprtcProgram& prog) {
  size_t log_size;
  NVRTC_CHECK(hiprtcGetProgramLogSize(prog, &log_size));
  auto log = std::make_unique<char[]>(log_size);
  NVRTC_CHECK(hiprtcGetProgramLog(prog, log.get()));
  os << log.get() << std::endl;
}

unsigned int get_device_architecture(hipDevice_t& device) {
  int major = 0;
  int minor = 0;
  CU_CHECK(hipDeviceGetAttribute(&major, hipDeviceAttributeComputeCapabilityMajor, device));
  CU_CHECK(hipDeviceGetAttribute(&minor, hipDeviceAttributeComputeCapabilityMinor, device));
  return static_cast<unsigned int>(major * 10 + minor);
}
