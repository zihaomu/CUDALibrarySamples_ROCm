// SPDX-License-Identifier: Apache-2.0
#include "batches_runtime.hpp"
#include <rocrand/rocrand_kernel.h>
__global__ void normal_header_probe(double*out){rocrand_state_philox4x32_10 state;rocrand_init(1234,0,0,&state);out[0]=rocrand_log_normal_double(&state,1.,.5);}
int main(){migration_batch::Buffer<double> out(1);normal_header_probe<<<1,1>>>(out.p);MB_CHECK(hipDeviceSynchronize());return std::isfinite(out.get()[0])?0:1;}
