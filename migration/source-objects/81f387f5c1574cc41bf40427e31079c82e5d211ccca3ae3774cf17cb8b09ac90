// SPDX-License-Identifier: Apache-2.0
#include "jpeg_encoder_gpu.hpp"
int main(int argc, char** argv) {
  try {
    if (argc != 7)
      throw std::runtime_error("usage: input.rgb width height quality 420|444 output.jpg");
    auto bytes = image_jpeg_encoder::read_binary(argv[1]);
    int width = std::stoi(argv[2]), height = std::stoi(argv[3]);
    int quality = std::stoi(argv[4]);
    std::string sampling = argv[5];
    if (sampling != "420" && sampling != "444")
      throw std::runtime_error("sampling must be 420 or 444");
    image_jpeg_encoder::check(hipSetDevice(0), "select GPU");
    image_jpeg_encoder::encode(bytes, width, height, quality,
                               sampling == "420" ? 2 : 1, argv[6]);
    std::cout << "{\"width\":" << width << ",\"height\":" << height
              << ",\"quality\":" << quality << ",\"sampling\":\"" << sampling
              << "\",\"gpu_colorspace\":true,\"gpu_fdct_quant\":true,"
              << "\"cpu_entropy\":true}\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
