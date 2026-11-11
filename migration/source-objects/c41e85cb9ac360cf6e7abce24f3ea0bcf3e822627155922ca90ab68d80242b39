// SPDX-License-Identifier: Apache-2.0
// Capability probe only: an actual decoded buffer is retained for every success.
#include <hip/hip_runtime.h>
#include <rocjpeg/rocjpeg.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
#include <iterator>

static void check(hipError_t s, const char* operation) {
    if (s != hipSuccess) throw std::runtime_error(std::string(operation) + ": " + hipGetErrorString(s));
}
struct Buffer {
    unsigned char* data = nullptr;
    explicit Buffer(size_t n) { check(hipMalloc(&data, n), "allocate"); }
    ~Buffer() { if (data) hipFree(data); }
    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;
};

int main(int argc, char** argv) {
    try {
        if (argc != 3) throw std::runtime_error("expected input and output directories");
        std::filesystem::create_directories(argv[2]);
        check(hipSetDevice(0), "select device");
        for (int backend : {0, 1}) {
            RocJpegHandle decoder = nullptr;
            auto created = rocJpegCreate(static_cast<RocJpegBackend>(backend), 0, &decoder);
            std::cout << "{\"backend\":" << backend << ",\"create\":" << created << "}\n";
            if (created != ROCJPEG_STATUS_SUCCESS) continue;
            for (const auto& file : std::filesystem::directory_iterator(argv[1])) {
                if (!file.is_regular_file()) continue;
                std::ifstream f(file.path(), std::ios::binary);
                std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(f)), {});
                RocJpegStreamHandle stream = nullptr;
                auto stream_status = rocJpegStreamCreate(&stream);
                auto parsed = stream_status == 0 ? rocJpegStreamParse(bytes.data(), bytes.size(), stream) : stream_status;
                uint8_t components = 0;
                RocJpegChromaSubsampling subsampling{};
                uint32_t widths[4]{}, heights[4]{};
                int info = parsed == 0 ? rocJpegGetImageInfo(decoder, stream, &components, &subsampling, widths, heights) : -99;
                int decoded = -99;
                if (info == 0) {
                    if (!widths[0] || !heights[0] || widths[0] > 32768 || heights[0] > 32768)
                        throw std::runtime_error("invalid dimensions");
                    const size_t size = size_t(widths[0]) * heights[0] * 3;
                    Buffer buffer(size);
                    check(hipMemset(buffer.data, 173, size), "sentinel");
                    RocJpegImage image{};
                    image.channel[0] = buffer.data;
                    image.pitch[0] = widths[0] * 3;
                    RocJpegDecodeParams params{};
                    params.output_format = ROCJPEG_OUTPUT_RGB;
                    decoded = rocJpegDecode(decoder, stream, &params, &image);
                    check(hipDeviceSynchronize(), "decode synchronize");
                    if (decoded == 0) {
                        std::vector<unsigned char> output(size);
                        check(hipMemcpy(output.data(), buffer.data, size, hipMemcpyDeviceToHost), "read pixels");
                        auto path = std::filesystem::path(argv[2]) / (file.path().filename().string() + ".rgb");
                        std::ofstream o(path, std::ios::binary);
                        o.write(reinterpret_cast<const char*>(output.data()), output.size());
                        if (!o) throw std::runtime_error("write pixels");
                    }
                }
                std::cout << "{\"file\":\"" << file.path().filename().string() << "\",\"backend\":" << backend
                          << ",\"stream_create\":" << stream_status << ",\"parse\":" << parsed << ",\"info\":" << info
                          << ",\"decode\":" << decoded << ",\"width\":" << widths[0] << ",\"height\":" << heights[0]
                          << ",\"components\":" << int(components) << ",\"subsampling\":" << int(subsampling) << "}\n";
                if (stream) {
                    auto destroyed = rocJpegStreamDestroy(stream);
                    if (destroyed != 0) throw std::runtime_error("stream destroy");
                }
            }
            if (rocJpegDestroy(decoder) != 0) throw std::runtime_error("decoder destroy");
        }
        return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
