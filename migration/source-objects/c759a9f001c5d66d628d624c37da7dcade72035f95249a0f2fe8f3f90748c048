// SPDX-License-Identifier: Apache-2.0
// Experimental I5 JPEG forward transform: GPU pixels/FDCT, CPU JPEG entropy.
#pragma once
#include <hip/hip_runtime.h>
#include <jpeglib.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

namespace image_jpeg_encoder {

inline void check(hipError_t code, const char* what) {
  if (code != hipSuccess)
    throw std::runtime_error(std::string(what) + ": " + hipGetErrorString(code));
}

inline std::vector<unsigned char> read_binary(const char* path) {
  std::ifstream stream(path, std::ios::binary);
  if (!stream) throw std::runtime_error(std::string("cannot open ") + path);
  return {std::istreambuf_iterator<char>(stream), {}};
}

inline void write_binary(const char* path, const unsigned char* data, size_t count) {
  std::ofstream stream(path, std::ios::binary);
  stream.write(reinterpret_cast<const char*>(data), count);
  if (!stream) throw std::runtime_error(std::string("cannot write ") + path);
}

__device__ inline unsigned char byte(float value) {
  int integer = __float2int_rn(value);
  return static_cast<unsigned char>(integer < 0 ? 0 : integer > 255 ? 255 : integer);
}

__global__ void rgb_to_plane(const unsigned char* rgb, unsigned char* plane,
                             int image_width, int image_height, int plane_width,
                             int plane_height, int channel, int sampling) {
  int index = blockIdx.x * blockDim.x + threadIdx.x;
  if (index >= plane_width * plane_height) return;
  int x = index % plane_width, y = index / plane_width;
  int scale = channel == 0 ? 1 : sampling;
  float total = 0.0f;
  for (int dy = 0; dy < scale; ++dy) {
    for (int dx = 0; dx < scale; ++dx) {
      int sx = x * scale + dx < image_width ? x * scale + dx : image_width - 1;
      int sy = y * scale + dy < image_height ? y * scale + dy : image_height - 1;
      const unsigned char* color = rgb + (size_t(sy) * image_width + sx) * 3;
      float r = color[0], g = color[1], b = color[2];
      total += channel == 0 ? 0.299f*r + 0.587f*g + 0.114f*b :
               channel == 1 ? 128.0f - 0.168736f*r - 0.331264f*g + 0.5f*b :
                              128.0f + 0.5f*r - 0.418688f*g - 0.081312f*b;
    }
  }
  plane[index] = byte(total / float(scale * scale));
}

__global__ void forward_dct_quantize(const unsigned char* plane, const unsigned short* quant,
                                     const float* cosine, short* coefficients,
                                     int width, int height, int block_width, int block_height) {
  int index = blockIdx.x * blockDim.x + threadIdx.x;
  if (index >= block_width * block_height * 64) return;
  int frequency = index % 64;
  int u = frequency % 8, v = frequency / 8;
  int block = index / 64;
  int block_x = block % block_width, block_y = block / block_width;
  float sum = 0.0f;
  for (int y = 0; y < 8; ++y) {
    int source_y = block_y * 8 + y < height ? block_y * 8 + y : height - 1;
    for (int x = 0; x < 8; ++x) {
      int source_x = block_x * 8 + x < width ? block_x * 8 + x : width - 1;
      sum += (float(plane[size_t(source_y) * width + source_x]) - 128.0f) *
             cosine[x * 8 + u] * cosine[y * 8 + v];
    }
  }
  float normalizer = (u ? 1.0f : 0.7071067811865475f) *
                     (v ? 1.0f : 0.7071067811865475f) * 0.25f;
  coefficients[index] = static_cast<short>(__float2int_rn(sum * normalizer / quant[frequency]));
}

inline void encode(const std::vector<unsigned char>& rgb, int width, int height,
                   int quality, int subsampling, const char* destination,
                   bool optimized_huffman = false, hipStream_t stream = nullptr) {
  if (width <= 0 || height <= 0 || quality < 1 || quality > 100 ||
      (subsampling != 1 && subsampling != 2) ||
      rgb.size() != size_t(width) * height * 3)
    throw std::runtime_error("invalid RGB image dimensions, length, quality or sampling");
  jpeg_compress_struct compressor{};
  jpeg_error_mgr errors{};
  compressor.err = jpeg_std_error(&errors);
  jpeg_create_compress(&compressor);
  unsigned char* bitstream = nullptr;
  unsigned long bitstream_size = 0;
  jpeg_mem_dest(&compressor, &bitstream, &bitstream_size);
  compressor.image_width = width;
  compressor.image_height = height;
  compressor.input_components = 3;
  compressor.in_color_space = JCS_RGB;
  jpeg_set_defaults(&compressor);
  jpeg_set_quality(&compressor, quality, TRUE);
  compressor.optimize_coding = optimized_huffman ? TRUE : FALSE;
  compressor.comp_info[0].h_samp_factor = subsampling;
  compressor.comp_info[0].v_samp_factor = subsampling;
  for (int channel = 1; channel < 3; ++channel) {
    compressor.comp_info[channel].h_samp_factor = 1;
    compressor.comp_info[channel].v_samp_factor = 1;
  }
  std::array<int, 3> plane_width{}, plane_height{}, blocks_x{}, blocks_y{};
  jvirt_barray_ptr arrays[3];
  for (int channel = 0; channel < 3; ++channel) {
    int scale = channel == 0 ? 1 : subsampling;
    plane_width[channel] = (width + scale - 1) / scale;
    plane_height[channel] = (height + scale - 1) / scale;
    blocks_x[channel] = (plane_width[channel] + 7) / 8;
    blocks_y[channel] = (plane_height[channel] + 7) / 8;
    int mcu_x = channel == 0 ? subsampling : 1;
    int mcu_y = channel == 0 ? subsampling : 1;
    int padded_x = ((blocks_x[channel] + mcu_x - 1) / mcu_x) * mcu_x;
    int padded_y = ((blocks_y[channel] + mcu_y - 1) / mcu_y) * mcu_y;
    arrays[channel] = compressor.mem->request_virt_barray(
        reinterpret_cast<j_common_ptr>(&compressor), JPOOL_IMAGE, TRUE,
        padded_x, padded_y, mcu_y);
  }
  jpeg_write_coefficients(&compressor, arrays);
  float cosine[64];
  for (int x = 0; x < 8; ++x)
    for (int u = 0; u < 8; ++u)
      cosine[x * 8 + u] = std::cos(float((2*x + 1) * u) * 3.14159265358979323846f / 16.0f);
  unsigned char* device_rgb = nullptr;
  float* device_cosine = nullptr;
  check(hipMalloc(&device_rgb, rgb.size()), "allocate RGB");
  check(hipMalloc(&device_cosine, sizeof(cosine)), "allocate cosine");
  check(hipMemcpyAsync(device_rgb, rgb.data(), rgb.size(), hipMemcpyHostToDevice, stream), "copy RGB");
  check(hipMemcpyAsync(device_cosine, cosine, sizeof(cosine), hipMemcpyHostToDevice, stream), "copy cosine");
  for (int channel = 0; channel < 3; ++channel) {
    size_t pixel_count = size_t(plane_width[channel]) * plane_height[channel];
    size_t coefficient_count = size_t(blocks_x[channel]) * blocks_y[channel] * 64;
    unsigned char* plane = nullptr;
    unsigned short* quant = nullptr;
    short* coefficients = nullptr;
    check(hipMalloc(&plane, pixel_count), "allocate image plane");
    check(hipMalloc(&quant, 64 * sizeof(unsigned short)), "allocate quant table");
    check(hipMalloc(&coefficients, coefficient_count * sizeof(short)), "allocate coefficients");
    auto* table = compressor.quant_tbl_ptrs[compressor.comp_info[channel].quant_tbl_no];
    if (!table) throw std::runtime_error("missing compressor quantization table");
    check(hipMemcpyAsync(quant, table->quantval, 64 * sizeof(unsigned short),
                         hipMemcpyHostToDevice, stream),
          "copy quantization table");
    rgb_to_plane<<<(pixel_count + 255) / 256, 256, 0, stream>>>(device_rgb, plane, width, height,
        plane_width[channel], plane_height[channel], channel, subsampling);
    check(hipGetLastError(), "launch RGB conversion and chroma downsampling");
    forward_dct_quantize<<<(coefficient_count + 255) / 256, 256, 0, stream>>>(plane, quant, device_cosine,
        coefficients, plane_width[channel], plane_height[channel],
        blocks_x[channel], blocks_y[channel]);
    check(hipGetLastError(), "launch GPU FDCT and quantization");
    std::vector<short> host(coefficient_count);
    check(hipMemcpyAsync(host.data(), coefficients, coefficient_count * sizeof(short),
                         hipMemcpyDeviceToHost, stream), "copy quantized coefficients");
    check(hipStreamSynchronize(stream), "synchronize GPU coefficients before CPU entropy");
    for (int row = 0; row < blocks_y[channel]; ++row) {
      JBLOCKARRAY blocks = compressor.mem->access_virt_barray(
          reinterpret_cast<j_common_ptr>(&compressor), arrays[channel], row, 1, TRUE);
      for (int column = 0; column < blocks_x[channel]; ++column)
        std::copy_n(host.data() + (size_t(row) * blocks_x[channel] + column) * 64,
                    64, blocks[0][column]);
    }
    check(hipFree(coefficients), "free coefficients");
    check(hipFree(quant), "free quantization table");
    check(hipFree(plane), "free image plane");
  }
  check(hipFree(device_cosine), "free cosine table");
  check(hipFree(device_rgb), "free RGB");
  jpeg_finish_compress(&compressor);
  write_binary(destination, bitstream, bitstream_size);
  jpeg_destroy_compress(&compressor);
  free(bitstream);
}
}  // namespace image_jpeg_encoder
