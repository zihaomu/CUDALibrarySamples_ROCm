// SPDX-License-Identifier: Apache-2.0
// Pure geometry and minimum device-workspace preflight; not a peak estimate.
#pragma once
#include <array>
#include <cstdint>
#include <stdexcept>
#include <string>

namespace image_jpeg_layout {
struct CapacityError:std::runtime_error {using std::runtime_error::runtime_error;};
struct Frame {
    std::array<uint64_t,3> pixels{},coefficients{};
    uint64_t blocks=0,minimum_bytes=0;
    bool histogram_safe=true;
};
inline Frame frame(int width,int height,int sampling,bool optimized) {
    if(width<=0||height<=0||width>65535||height>65535||(sampling!=1&&sampling!=2))
        throw std::invalid_argument("invalid JPEG frame geometry");
    Frame out;out.minimum_bytes=uint64_t(width)*height*3;
    for(unsigned c=0;c<3;++c) {
        const unsigned scale=c?sampling:1,pw=(width+scale-1)/scale,ph=(height+scale-1)/scale;
        out.pixels[c]=uint64_t(pw)*ph;
        out.coefficients[c]=uint64_t((pw+7)/8)*((ph+7)/8)*64;
        out.minimum_bytes+=out.pixels[c]+out.coefficients[c]*2;
    }
    const unsigned mx=(width+sampling*8-1)/(sampling*8),my=(height+sampling*8-1)/(sampling*8);
    out.blocks=uint64_t(mx)*my*(sampling==2?6:3);
    out.histogram_safe=!optimized||out.blocks<=UINT32_MAX/63;
    // 128-byte scan, int predecessor, component, 512-byte entropy scratch,
    // ushort length, uint offset; two uint arrays for the initial bit tiles.
    out.minimum_bytes+=out.blocks*(128+4+1+512+2+4)+(out.blocks/256+(out.blocks%256!=0))*8;
    // Three quant tables, cosine table, six Code[256] tables (sizeof(Code)=4),
    // prefix result and optional four symbol histograms plus one invalid flag.
    out.minimum_bytes+=3*64*2+64*4+6*256*4+8+(optimized?4*256*4+4:0);
    return out;
}
inline bool fits(const Frame& frame,uint64_t available,uint64_t owned=0) {
    return frame.histogram_safe&&(frame.minimum_bytes<=available||frame.minimum_bytes-available<=owned);
}
inline void require(const Frame& frame,uint64_t available,uint64_t owned=0) {
    if(!frame.histogram_safe)throw CapacityError("JPEG optimized histogram exceeds current uint32 symbol capacity");
    if(!fits(frame,available,owned))throw CapacityError("JPEG minimum workspace exceeds available device capacity: minimum="+
        std::to_string(frame.minimum_bytes)+" available="+std::to_string(available)+" reusable="+std::to_string(owned));
}
} // namespace image_jpeg_layout
