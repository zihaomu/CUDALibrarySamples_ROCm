// SPDX-License-Identifier: Apache-2.0
#include "../../backends/codec/jpeg2000/mq_decode.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static void check(hipError_t result, const char *stage) {
    if (result != hipSuccess)
        throw std::runtime_error(std::string(stage) + ": " + hipGetErrorString(result));
}
static std::vector<unsigned char> read_file(const char *name) {
    std::ifstream file(name, std::ios::binary | std::ios::ate);
    if (!file) throw std::runtime_error("cannot open input");
    auto size = file.tellg();
    if (size < 0 || size > 65536) throw std::runtime_error("input length outside bound");
    std::vector<unsigned char> data(static_cast<size_t>(size));
    file.seekg(0); file.read(reinterpret_cast<char *>(data.data()), data.size());
    if (!file) throw std::runtime_error("truncated input read");
    return data;
}
int main(int argc, char **argv) {
    try {
        if (argc != 4) throw std::runtime_error("usage: coded.mq contexts.ctx output.bits");
        auto coded = read_file(argv[1]);
        auto context = read_file(argv[2]);
        if (coded.size() < 2 || context.empty())
            throw std::runtime_error("truncated coded payload or empty context schedule");
        if (context.size() > 65536) throw std::runtime_error("too many symbols");
        for (unsigned char value : context)
            if (value >= 19) throw std::runtime_error("invalid MQ context index");
        check(hipSetDevice(0), "GPU device");
        unsigned char *device_coded = nullptr, *device_context = nullptr, *device_output = nullptr;
        int *device_status = nullptr;
        check(hipMalloc(&device_coded, coded.size()), "allocate coded bytes");
        check(hipMalloc(&device_context, context.size()), "allocate contexts");
        check(hipMalloc(&device_output, context.size()), "allocate output");
        check(hipMalloc(&device_status, sizeof(int)), "allocate status");
        check(hipMemcpy(device_coded, coded.data(), coded.size(), hipMemcpyHostToDevice), "copy coded bytes");
        check(hipMemcpy(device_context, context.data(), context.size(), hipMemcpyHostToDevice), "copy contexts");
        image_j2k_mq::decode_one<<<1, 1>>>(device_coded, static_cast<int>(coded.size()),
                                             device_context, static_cast<int>(context.size()),
                                             device_output, device_status);
        check(hipGetLastError(), "dispatch MQ decoder");
        check(hipDeviceSynchronize(), "execute MQ decoder");
        int status = -1;
        check(hipMemcpy(&status, device_status, sizeof(int), hipMemcpyDeviceToHost), "read status");
        if (status != 0) throw std::runtime_error("GPU MQ decoder rejected payload");
        std::vector<unsigned char> output(context.size());
        check(hipMemcpy(output.data(), device_output, output.size(), hipMemcpyDeviceToHost),
              "read decoded bits");
        std::ofstream file(argv[3], std::ios::binary);
        if (!file) throw std::runtime_error("cannot open output");
        file.write(reinterpret_cast<const char *>(output.data()), output.size());
        if (!file) throw std::runtime_error("cannot write decoded bits");
        check(hipFree(device_status), "free status");
        check(hipFree(device_output), "free output");
        check(hipFree(device_context), "free contexts");
        check(hipFree(device_coded), "free coded bytes");
        std::cout << "{\"gpu_mq\":true,\"symbols\":" << context.size()
                  << ",\"full_codeblock\":false,\"full_jp2_decode\":false}" << std::endl;
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "RESULT status=FAIL reason=" << error.what() << std::endl;
        return 1;
    }
}
