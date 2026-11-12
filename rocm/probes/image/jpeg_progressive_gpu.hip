// SPDX-License-Identifier: Apache-2.0
#include "progressive_jpeg.hpp"
int main(int argc, char** argv) {
  try {
    if (argc != 4) throw std::runtime_error("usage: input.jpg gpu.rgb cpu.rgb");
    auto input = read_file(argv[1]);
    auto picture = extract(input);
    auto cpu = cpu_reference(input, picture.width, picture.height);
    checked(hipSetDevice(0), "select AMD GPU");
    std::vector<void*> allocations;
    auto allocate = [&](size_t bytes) {
      void* pointer = nullptr;
      checked(hipMalloc(&pointer, bytes), "allocate GPU buffer");
      allocations.push_back(pointer);
      return pointer;
    };
    float cosine[64];
    for (int x = 0; x < 8; ++x)
      for (int u = 0; u < 8; ++u)
        cosine[x * 8 + u] = std::cos(float((2 * x + 1) * u) * 3.14159265358979323846f / 16.0f);
    auto* device_cos = static_cast<float*>(allocate(sizeof(cosine)));
    checked(hipMemcpy(device_cos, cosine, sizeof(cosine), hipMemcpyHostToDevice), "copy cosine");
    uint8_t* planes[3];
    for (int channel = 0; channel < 3; ++channel) {
      auto& component = picture.components[channel];
      auto* device_coeff = static_cast<int16_t*>(allocate(component.data.size() * sizeof(int16_t)));
      auto* device_quant = static_cast<uint16_t*>(allocate(64 * sizeof(uint16_t)));
      planes[channel] = static_cast<uint8_t*>(allocate(size_t(component.width) * component.height));
      checked(hipMemcpy(device_coeff, component.data.data(), component.data.size() * sizeof(int16_t),
                        hipMemcpyHostToDevice), "copy coefficients");
      checked(hipMemcpy(device_quant, component.quant.data(), 64 * sizeof(uint16_t),
                        hipMemcpyHostToDevice), "copy quantization");
      int pixels = component.width * component.height;
      inverse_dct<<<(pixels + 255) / 256, 256>>>(device_coeff, device_quant, device_cos,
        planes[channel], component.width, component.height, component.blocks_x);
      checked(hipGetLastError(), "launch GPU IDCT");
    }
    int total = picture.width * picture.height;
    auto* gpu_rgb = static_cast<uint8_t*>(allocate(size_t(total) * 3));
    auto& cb = picture.components[1];
    convert_rgb<<<(total + 255) / 256, 256>>>(planes[0], planes[1], planes[2], gpu_rgb,
      picture.width, picture.height, cb.width, cb.height,
      cb.h_factor, cb.v_factor, picture.max_h, picture.max_v);
    checked(hipGetLastError(), "launch GPU RGB conversion");
    checked(hipDeviceSynchronize(), "synchronize GPU pixel synthesis");
    std::vector<unsigned char> gpu(size_t(total) * 3);
    checked(hipMemcpy(gpu.data(), gpu_rgb, gpu.size(), hipMemcpyDeviceToHost), "copy GPU pixels");
    for (auto* pointer : allocations) checked(hipFree(pointer), "free GPU buffer");
    write_file(argv[2], gpu);
    write_file(argv[3], cpu);
    std::cout << "{\"width\":" << picture.width << ",\"height\":" << picture.height
              << ",\"components\":3,\"progressive\":true,\"cpu_entropy\":true,"
              << "\"gpu_idct\":true,\"gpu_chroma_rgb\":true,\"cpu_pixel_fallback\":false}\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
