// SPDX-License-Identifier: Apache-2.0
#include "jpeg_parallel_prefix.hpp"
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static void check(hipError_t value, const char* label) {
    if (value != hipSuccess) throw std::runtime_error(std::string(label) + ": " + hipGetErrorString(value));
}

template<class T, bool STUFF>
__global__ void serial_prefix(const T* input, unsigned* output, unsigned* total, unsigned count) {
    if (threadIdx.x || blockIdx.x) return;
    unsigned sum=0;
    for (unsigned i=0;i<count;++i) {
        output[i]=sum+(STUFF?i:0);
        sum+=STUFF?unsigned(input[i]==T(0xff)):unsigned(input[i]);
    }
    total[0]=sum+(STUFF?count:0);
}

template<class T, bool STUFF>
static void execute(unsigned count, unsigned seed) {
    std::vector<T> input(count);
    std::vector<unsigned> expected(count),actual(count);
    unsigned random=seed,sum=0;
    for (unsigned i=0;i<count;++i) {
        random^=random<<13;random^=random>>17;random^=random<<5;
        input[i]=STUFF?T((i%13==0 || (random&15)==0)?255:(random%255)):T(random%4097);
        expected[i]=sum+(STUFF?i:0);
        sum+=STUFF?unsigned(input[i]==T(0xff)):unsigned(input[i]);
    }
    unsigned expected_total=sum+(STUFF?count:0);
    unsigned tiles=(count+image_jpeg_parallel_prefix::TILE-1)/image_jpeg_parallel_prefix::TILE;
    T* device_input{};unsigned *device_output{},*device_total{},*device_sums{},*device_bases{};
    check(hipSetDevice(0),"select GPU");
    check(hipMalloc(&device_input,input.size()*sizeof(T)),"allocate input");
    check(hipMalloc(&device_output,count*sizeof(unsigned)),"allocate output");
    check(hipMalloc(&device_total,sizeof(unsigned)),"allocate total");
    check(hipMalloc(&device_sums,tiles*sizeof(unsigned)),"allocate sums");
    check(hipMalloc(&device_bases,tiles*sizeof(unsigned)),"allocate bases");
    check(hipMemcpy(device_input,input.data(),input.size()*sizeof(T),hipMemcpyHostToDevice),"copy input");
    auto verify=[&](bool parallel) {
        if (parallel) image_jpeg_parallel_prefix::launch<T,STUFF>(device_input,device_output,device_sums,device_bases,device_total,count);
        else serial_prefix<T,STUFF><<<1,1>>>(device_input,device_output,device_total,count);
        check(hipGetLastError(),"launch prefix");
        unsigned gpu_total{};
        check(hipMemcpy(actual.data(),device_output,count*sizeof(unsigned),hipMemcpyDeviceToHost),"read positions");
        check(hipMemcpy(&gpu_total,device_total,sizeof(gpu_total),hipMemcpyDeviceToHost),"read total");
        if (actual!=expected || gpu_total!=expected_total) throw std::runtime_error("benchmark prefix numerical mismatch");
    };
    verify(false);verify(true);
    auto benchmark=[&](bool parallel) {
        hipEvent_t start{},stop{};check(hipEventCreate(&start),"start event");check(hipEventCreate(&stop),"stop event");
        std::vector<float> milliseconds;
        for (int iteration=0;iteration<23;++iteration) {
            check(hipEventRecord(start),"record start");
            if (parallel) image_jpeg_parallel_prefix::launch<T,STUFF>(device_input,device_output,device_sums,device_bases,device_total,count);
            else serial_prefix<T,STUFF><<<1,1>>>(device_input,device_output,device_total,count);
            check(hipEventRecord(stop),"record stop");check(hipEventSynchronize(stop),"wait stop");
            float ms{};check(hipEventElapsedTime(&ms,start,stop),"elapsed");
            if (iteration>=3) milliseconds.push_back(ms);
        }
        std::sort(milliseconds.begin(),milliseconds.end());
        check(hipEventDestroy(start),"destroy start");check(hipEventDestroy(stop),"destroy stop");
        return double(milliseconds[milliseconds.size()/2]);
    };
    double serial=benchmark(false),parallel=benchmark(true);
    std::cout<<"{\"status\":\"PASSED\",\"mode\":\""<<(STUFF?"stuff":"bits")
             <<"\",\"count\":"<<count<<",\"total\":"<<expected_total
             <<",\"serial_median_ms\":"<<serial<<",\"parallel_median_ms\":"<<parallel
             <<",\"repeats\":20}"<<std::endl;
    hipFree(device_input);hipFree(device_output);hipFree(device_total);hipFree(device_sums);hipFree(device_bases);
}

int main(int argc,char**argv) {
    try {
        if (argc!=4) throw std::runtime_error("usage: bench bits|stuff count seed");
        auto count=std::stoul(argv[2]);auto seed=std::stoul(argv[3]);
        if (!count || count>1048576 || !seed) throw std::runtime_error("invalid benchmark dimensions");
        if (std::string(argv[1])=="bits") execute<unsigned short,false>(unsigned(count),unsigned(seed));
        else if (std::string(argv[1])=="stuff") execute<unsigned char,true>(unsigned(count),unsigned(seed));
        else throw std::runtime_error("invalid mode");
        return 0;
    } catch (const std::exception& error) {
        std::cerr<<"RESULT status=FAIL reason="<<error.what()<<std::endl;return 1;
    }
}
