// SPDX-License-Identifier: Apache-2.0
// Bounded JPEG2000 JP2/J2K container and main-header metadata parser.
#pragma once
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

namespace image_j2k_container {
inline uint16_t be16(const std::vector<unsigned char>& b, size_t p) {
    if (p > b.size() || b.size() - p < 2) throw std::runtime_error("truncated u16");
    return uint16_t((unsigned(b[p]) << 8) | b[p + 1]);
}
inline uint32_t be32(const std::vector<unsigned char>& b, size_t p) {
    if (p > b.size() || b.size() - p < 4) throw std::runtime_error("truncated u32");
    return (uint32_t(be16(b, p)) << 16) | be16(b, p + 2);
}
inline uint64_t be64(const std::vector<unsigned char>& b, size_t p) {
    if (p > b.size() || b.size() - p < 8) throw std::runtime_error("truncated u64");
    return (uint64_t(be32(b, p)) << 32) | be32(b, p + 4);
}
struct Header {
    bool jp2 = false;
    size_t codestream_offset = 0, codestream_bytes = 0;
    uint32_t width = 0, height = 0, tile_width = 0, tile_height = 0;
    uint32_t tile_origin_x = 0, tile_origin_y = 0, tiles_x = 0, tiles_y = 0;
    uint16_t components = 0, layers = 0;
    uint8_t progression = 0, mct = 0, levels = 0, transform = 0;
    std::vector<uint8_t> bit_depth, is_signed, subsample_x, subsample_y;
};
inline Header parse(const std::vector<unsigned char>& bytes) {
    if (bytes.size() < 8 || bytes.size() > 512ULL * 1024 * 1024)
        throw std::runtime_error("unsupported JPEG2000 input size");
    Header result;
    size_t start = 0, end = bytes.size();
    if (be32(bytes, 4) == 0x6a502020) { // JP2 signature box type: 'jP  '
        result.jp2 = true;
        if (be32(bytes, 0) != 12 || be32(bytes, 8) != 0x0d0a870a)
            throw std::runtime_error("invalid JP2 signature box");
        size_t box = 0;
        bool found = false;
        while (box < bytes.size()) {
            if (bytes.size() - box < 8) throw std::runtime_error("truncated JP2 box");
            uint64_t length = be32(bytes, box), header_bytes = 8;
            uint32_t type = be32(bytes, box + 4);
            if (length == 1) {
                if (bytes.size() - box < 16) throw std::runtime_error("truncated extended JP2 box");
                length = be64(bytes, box + 8); header_bytes = 16;
            } else if (length == 0) length = bytes.size() - box;
            if (length < header_bytes || length > bytes.size() - box)
                throw std::runtime_error("invalid JP2 box length");
            if (type == 0x6a703263) { // 'jp2c'
                if (found) throw std::runtime_error("multiple JP2 codestream boxes");
                start = box + header_bytes; end = box + length; found = true;
            }
            box += length;
        }
        if (!found) throw std::runtime_error("JP2 codestream box missing");
    }
    if (end - start < 4 || be16(bytes, start) != 0xff4f)
        throw std::runtime_error("J2K SOC marker missing");
    result.codestream_offset = start; result.codestream_bytes = end - start;
    bool siz = false, cod = false, sot = false;
    for (size_t p = start + 2; p + 2 <= end;) {
        if (bytes[p] != 0xff || bytes[p + 1] == 0x00)
            throw std::runtime_error("invalid main-header marker");
        uint16_t marker = be16(bytes, p);
        if (marker == 0xff90) { sot = true; break; }
        if (p + 4 > end) throw std::runtime_error("truncated main-header segment");
        uint16_t length = be16(bytes, p + 2);
        if (length < 2 || length > end - (p + 2))
            throw std::runtime_error("invalid main-header segment length");
        size_t data = p + 4;
        if (marker == 0xff51) { // SIZ
            if (siz || length < 41) throw std::runtime_error("duplicate or short SIZ");
            uint32_t xsiz = be32(bytes, data + 2), ysiz = be32(bytes, data + 6);
            uint32_t xosiz = be32(bytes, data + 10), yosiz = be32(bytes, data + 14);
            result.tile_width = be32(bytes, data + 18);
            result.tile_height = be32(bytes, data + 22);
            result.tile_origin_x = be32(bytes, data + 26);
            result.tile_origin_y = be32(bytes, data + 30);
            result.components = be16(bytes, data + 34);
            if (!result.components || result.components > 16384 ||
                length != 38U + 3U * result.components || xsiz <= xosiz || ysiz <= yosiz ||
                !result.tile_width || !result.tile_height ||
                result.tile_origin_x > xosiz || result.tile_origin_y > yosiz ||
                result.tile_origin_x >= xsiz || result.tile_origin_y >= ysiz)
                throw std::runtime_error("invalid SIZ geometry or component count");
            result.width = xsiz - xosiz; result.height = ysiz - yosiz;
            result.tiles_x = 1 + (xsiz - result.tile_origin_x - 1) / result.tile_width;
            result.tiles_y = 1 + (ysiz - result.tile_origin_y - 1) / result.tile_height;
            for (unsigned c = 0; c < result.components; ++c) {
                unsigned depth = bytes[data + 36 + 3 * c];
                unsigned dx = bytes[data + 37 + 3 * c], dy = bytes[data + 38 + 3 * c];
                if (!dx || !dy) throw std::runtime_error("zero component subsampling");
                result.bit_depth.push_back((depth & 127) + 1);
                result.is_signed.push_back(depth >> 7);
                result.subsample_x.push_back(dx); result.subsample_y.push_back(dy);
            }
            siz = true;
        } else if (marker == 0xff52) { // COD
            if (!siz || cod || length < 12) throw std::runtime_error("missing SIZ or duplicate/short COD");
            uint8_t scod = bytes[data];
            result.progression = bytes[data + 1]; result.layers = be16(bytes, data + 2);
            result.mct = bytes[data + 4]; result.levels = bytes[data + 5];
            result.transform = bytes[data + 9];
            if (!result.layers || result.progression > 4 || result.transform > 1 ||
                result.levels > 32 || (scod & ~1U))
                throw std::runtime_error("invalid COD coding style");
            cod = true;
        }
        p += 2 + length;
    }
    if (!siz || !cod || !sot) throw std::runtime_error("incomplete J2K main header");
    return result;
}
} // namespace image_j2k_container
