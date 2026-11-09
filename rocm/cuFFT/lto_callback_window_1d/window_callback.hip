// SPDX-License-Identifier: Apache-2.0
#ifdef __HIPCC_RTC__
using hipfftComplex=float2;
#else
#include <hipfft/hipfft.h>
#endif
struct callback_params {unsigned window_size;unsigned signal_size;};
extern "C" __device__ hipfftComplex windowing_callback(void* input,size_t index,void* info,void*){auto p=static_cast<const callback_params*>(info);auto values=static_cast<const hipfftComplex*>(input);return index%p->signal_size<p->window_size?values[index]:hipfftComplex{0,0};}
