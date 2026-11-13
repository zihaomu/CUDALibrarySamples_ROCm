// SPDX-License-Identifier: Apache-2.0
// Test-only observation of real HIP copy arguments, including kernel-based copies.
#include <hip/hip_runtime_api.h>
#include <dlfcn.h>
#include <cstdio>
#include <mutex>
static std::mutex output_mutex;
extern "C" hipError_t hipMemcpyAsync(void* dst,const void* src,size_t bytes,
                                     hipMemcpyKind kind,hipStream_t stream) {
    using Function=hipError_t(*)(void*,const void*,size_t,hipMemcpyKind,hipStream_t);
    static auto real=reinterpret_cast<Function>(dlsym(RTLD_NEXT,"hipMemcpyAsync"));
    if(!real)return hipErrorUnknown;
    auto result=real(dst,src,bytes,kind,stream);
    std::lock_guard<std::mutex> guard(output_mutex);
    std::fprintf(stderr,"JPEG_COPY_AUDIT kind=%d bytes=%zu stream=%p rc=%d\n",int(kind),bytes,reinterpret_cast<void*>(stream),int(result));
    return result;
}
