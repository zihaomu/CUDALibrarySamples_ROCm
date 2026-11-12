// SPDX-License-Identifier: Apache-2.0
#include "../../backends/codec/jpeg2000/container.hpp"
#include <fstream>
#include <iostream>
#include <iterator>

int main(int argc, char** argv) {
    try {
        if (argc != 2) throw std::runtime_error("usage: jp2-or-j2k-file");
        std::ifstream file(argv[1], std::ios::binary);
        if (!file) throw std::runtime_error("cannot open JPEG2000 file");
        std::vector<unsigned char> bytes(std::istreambuf_iterator<char>{file}, {});
        auto h = image_j2k_container::parse(bytes);
        std::cout << "{\"jp2\":" << (h.jp2 ? "true" : "false")
                  << ",\"width\":" << h.width << ",\"height\":" << h.height
                  << ",\"tile_width\":" << h.tile_width
                  << ",\"tile_height\":" << h.tile_height
                  << ",\"tiles_x\":" << h.tiles_x << ",\"tiles_y\":" << h.tiles_y
                  << ",\"components\":" << h.components << ",\"layers\":" << h.layers
                  << ",\"progression\":" << unsigned(h.progression)
                  << ",\"mct\":" << unsigned(h.mct)
                  << ",\"levels\":" << unsigned(h.levels)
                  << ",\"transform\":" << unsigned(h.transform)
                  << ",\"codestream_offset\":" << h.codestream_offset
                  << ",\"codestream_bytes\":" << h.codestream_bytes << ",\"bit_depth\":[";
        for (size_t i = 0; i < h.components; ++i) std::cout << (i ? "," : "") << unsigned(h.bit_depth[i]);
        std::cout << "],\"signed\":[";
        for (size_t i = 0; i < h.components; ++i) std::cout << (i ? "," : "") << unsigned(h.is_signed[i]);
        std::cout << "]}" << std::endl;
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "RESULT status=FAIL reason=" << error.what() << std::endl;
        return 1;
    }
}
