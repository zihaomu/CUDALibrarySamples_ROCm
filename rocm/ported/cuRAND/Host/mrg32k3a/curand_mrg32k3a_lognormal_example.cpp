/*
 * SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

/*
 * This program uses the host CURAND API to generate 100
 * pseudorandom floats.
 */
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <vector>

#include <hip/hip_runtime.h>
#include <hiprand/hiprand.h>

#include "curand_utils.h"

using data_type = float;

void run_on_device(const int &n, const data_type &mean, const data_type &stddev,
                   const unsigned long long &offset,
                   const unsigned long long &seed,
                   const hiprandOrdering_t &order, const hiprandRngType_t &rng,
                   const hipStream_t &stream, hiprandGenerator_t &gen,
                   std::vector<data_type> &h_data) {

  data_type *d_data = nullptr;

  /* C data to device */
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_data),
                        sizeof(data_type) * h_data.size()));

  /* Create pseudo-random number generator */
  CURAND_CHECK(hiprandCreateGenerator(&gen, HIPRAND_RNG_PSEUDO_MRG32K3A));

  /* Set cuRAND to stream */
  CURAND_CHECK(hiprandSetStream(gen, stream));

  /* Set offset */
  CURAND_CHECK(hiprandSetGeneratorOffset(gen, offset));

  /* Set ordering */
  CURAND_CHECK(hiprandSetGeneratorOrdering(gen, order));

  /* Set seed */
  CURAND_CHECK(hiprandSetPseudoRandomGeneratorSeed(gen, seed));

  /* Generate n floats on device */
  CURAND_CHECK(
      hiprandGenerateLogNormal(gen, d_data, h_data.size(), mean, stddev));

  /* Copy data to host */
  CUDA_CHECK(hipMemcpyAsync(h_data.data(), d_data,
                             sizeof(data_type) * h_data.size(),
                             hipMemcpyDeviceToHost, stream));

  /* Sync stream */
  CUDA_CHECK(hipStreamSynchronize(stream));

  /* Cleanup */
  CUDA_CHECK(hipFree(d_data));

  CURAND_CHECK(hiprandDestroyGenerator(gen));gen=nullptr;
}

void run_on_host(const int &n, const data_type &mean, const data_type &stddev,
                 const unsigned long long &offset,
                 const unsigned long long &seed, const hiprandOrdering_t &order,
                 const hiprandRngType_t &rng, const hipStream_t &stream,
                 hiprandGenerator_t &gen, std::vector<data_type> &h_data) {

  /* Create pseudo-random number generator */
  CURAND_CHECK(hiprandCreateGeneratorHost(&gen, HIPRAND_RNG_PSEUDO_MRG32K3A));

  /* Set cuRAND to stream */
  CURAND_CHECK(hiprandSetStream(gen, stream));

  /* Set offset */
  CURAND_CHECK(hiprandSetGeneratorOffset(gen, offset));

  /* Set ordering */
  CURAND_CHECK(hiprandSetGeneratorOrdering(gen, order));

  /* Set seed */
  CURAND_CHECK(hiprandSetPseudoRandomGeneratorSeed(gen, seed));

  /* Generate n floats on host */
  CURAND_CHECK(
      hiprandGenerateLogNormal(gen, h_data.data(), h_data.size(), mean, stddev));

  CURAND_CHECK(hiprandDestroyGenerator(gen));gen=nullptr;
}

int main(int argc, char *argv[]) {

  hipStream_t stream = NULL;
  hiprandGenerator_t gen = NULL;
  hiprandRngType_t rng = HIPRAND_RNG_PSEUDO_MRG32K3A;
  hiprandOrdering_t order = HIPRAND_ORDERING_PSEUDO_BEST;

  const int n = 10;

  const unsigned long long offset = 0ULL;
  const unsigned long long seed = 1234ULL;

  const data_type mean = 1.0f;
  const data_type stddev = 2.0f;

  /* Create stream */
  CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));

  /* Allocate n floats on host */
  std::vector<data_type> h_data(n, 0);

  run_on_host(n, mean, stddev, offset, seed, order, rng, stream, gen, h_data);

  printf("Host\n");
  print_vector(h_data);
  printf("=====\n");

  run_on_device(n, mean, stddev, offset, seed, order, rng, stream, gen, h_data);

  printf("Device\n");
  print_vector(h_data);
  printf("=====\n");

  /* Cleanup */
  if(gen){CURAND_CHECK(hiprandDestroyGenerator(gen));gen=nullptr;}

  CUDA_CHECK(hipStreamDestroy(stream));

  // Keep HIP alive until library-owned caches finish process-exit cleanup.

  return EXIT_SUCCESS;
}