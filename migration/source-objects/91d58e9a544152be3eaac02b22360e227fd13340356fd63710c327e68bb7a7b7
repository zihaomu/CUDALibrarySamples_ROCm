// SPDX-License-Identifier: Apache-2.0
#include "../../backends/codec/jpeg2000/reversible53.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static void check(hipError_t status, const char* stage) {
    if (status != hipSuccess) throw std::runtime_error(std::string(stage) + ": " +
                                                     hipGetErrorString(status));
}
static std::vector<unsigned char> read_binary(const char* path) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    if (!input) throw std::runtime_error("cannot open coefficient input");
    auto size = input.tellg();
    if (size < 0) throw std::runtime_error("invalid coefficient length");
    std::vector<unsigned char> data(static_cast<size_t>(size));
    input.seekg(0); input.read(reinterpret_cast<char*>(data.data()), data.size());
    if (!input) throw std::runtime_error("truncated coefficient input");
    return data;
}
int main(int argc, char** argv) {
    try {
        if (argc != 5) throw std::runtime_error("usage: coefficients.i32 width height output.rgb");
        size_t used = 0;
        int width = std::stoi(argv[2], &used);
        if (used != std::string(argv[2]).size()) throw std::runtime_error("invalid width");
        int height = std::stoi(argv[3], &used);
        if (used != std::string(argv[3]).size()) throw std::runtime_error("invalid height");
        if (width < 1 || height < 1 || width > 64 || height > 64)
            throw std::runtime_error("unsupported transform dimensions");
        auto input = read_binary(argv[1]);
        size_t pixels = size_t(width) * height;
        if (input.size() != pixels * 3 * sizeof(int))
            throw std::runtime_error("coefficient payload size mismatch");
        check(hipSetDevice(0), "GPU device");
        int *coefficients = nullptr, *vertical = nullptr, *spatial = nullptr;
        unsigned char* device_rgb = nullptr;
        check(hipMalloc(&coefficients, input.size()), "allocate coefficients");
        check(hipMalloc(&vertical, input.size()), "allocate vertical workspace");
        check(hipMalloc(&spatial, input.size()), "allocate spatial workspace");
        check(hipMalloc(&device_rgb, pixels * 3), "allocate RGB");
        check(hipMemcpy(coefficients, input.data(), input.size(), hipMemcpyHostToDevice),
              "copy coefficients");
        image_j2k_i53::inverse_vertical<<<dim3((width + 63) / 64, 3), 64>>>(
            coefficients, vertical, width, height);
        check(hipGetLastError(), "inverse vertical dispatch");
        image_j2k_i53::inverse_horizontal<<<dim3((height + 63) / 64, 3), 64>>>(
            vertical, spatial, width, height);
        check(hipGetLastError(), "inverse horizontal dispatch");
        image_j2k_i53::inverse_rct_rgb<<<(pixels + 255) / 256, 256>>>(
            spatial, device_rgb, pixels);
        check(hipGetLastError(), "inverse RCT dispatch");
        check(hipDeviceSynchronize(), "GPU inverse transform");
        std::vector<unsigned char> output(pixels * 3);
        check(hipMemcpy(output.data(), device_rgb, output.size(), hipMemcpyDeviceToHost),
              "copy RGB");
        std::ofstream file(argv[4], std::ios::binary);
        if (!file) throw std::runtime_error("cannot open RGB output");
        file.write(reinterpret_cast<const char*>(output.data()), output.size());
        if (!file) throw std::runtime_error("cannot write RGB output");
        check(hipFree(device_rgb), "free RGB"); check(hipFree(spatial), "free spatial");
        check(hipFree(vertical), "free vertical");
        check(hipFree(coefficients), "free coefficients");
        std::cout << "{\"gpu_inverse53\":true,\"gpu_inverse_rct\":true,\"cpu_tier1\":false,\"full_jp2_decode\":false}" << std::endl;
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "RESULT status=FAIL reason=" << error.what() << std::endl;
        return 1;
    }
}
