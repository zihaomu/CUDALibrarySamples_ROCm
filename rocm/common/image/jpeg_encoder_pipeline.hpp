// SPDX-License-Identifier: Apache-2.0
// Reusable asynchronous JPEG slot. CPU handles markers and optimized DHT only.
#pragma once
#include "jpeg_optimal_huffman.hpp"
#include "jpeg_checked_prefix.hpp"
#include <cstring>
#include <limits>
#include <atomic>

namespace image_jpeg_pipeline {
using image_jpeg_encoder::check;
using PrefixResult = image_jpeg_checked_prefix::Result;
inline std::atomic<size_t> workspace_growths{0};
#ifdef IMAGE_JPEG_PIPELINE_TEST_FAULTS
inline int workspace_fail_after = -1;
#endif

template<class T, bool Pinned = false> class Buffer {
    T* pointer_ = nullptr;
    size_t capacity_ = 0;
public:
    Buffer() = default;
    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;
    ~Buffer() { if(pointer_) { if constexpr(Pinned) hipHostFree(pointer_); else hipFree(pointer_); } }
    void ensure(size_t elements) {
        if(elements <= capacity_) return;
        if(elements > std::numeric_limits<size_t>::max()/sizeof(T))
            throw std::runtime_error("JPEG workspace size overflow");
#ifdef IMAGE_JPEG_PIPELINE_TEST_FAULTS
        if(workspace_fail_after==0)throw std::runtime_error("injected JPEG workspace allocation failure");
        if(workspace_fail_after>0)--workspace_fail_after;
#endif
        T* replacement=nullptr;
        if constexpr(Pinned) check(hipHostMalloc(&replacement,elements*sizeof(T)),"pinned JPEG allocation");
        else check(hipMalloc(&replacement,elements*sizeof(T)),"device JPEG allocation");
        ++workspace_growths;
        if(pointer_) { if constexpr(Pinned) hipHostFree(pointer_); else hipFree(pointer_); }
        pointer_=replacement;capacity_=elements;
    }
    T* get() { return pointer_; }
    const T* get() const { return pointer_; }
    size_t bytes() const { return capacity_*sizeof(T); }
};

class Slot {
public:
    enum class Phase { Idle, Preparing, Histogram, Bits, Stuff, Download, Ready, Failed };
private:
    hipStream_t stream_ = nullptr;
    hipEvent_t event_ = nullptr;
    jpeg_compress_struct jpeg_{};
    jpeg_error_mgr jpeg_errors_{};
    bool jpeg_live_ = false;
    Phase phase_ = Phase::Idle;
    int width_=0,height_=0,sampling_=0,blocks_=0,quality_=0;
    unsigned raw_bytes_=0,stuffed_bytes_=0;
    bool optimized_=false,download_=false,prepared_=false;
    std::vector<unsigned char> header_;
    Buffer<unsigned char> rgb_,planes_[3],components_,bits_,packed_,stuffed_;
    Buffer<short> coefficients_[3],scan_;
    Buffer<unsigned short> quant_[3],lengths_;
    Buffer<float> cosine_;
    Buffer<int> previous_;
    Buffer<Code> dc_,ac_;
    Buffer<unsigned> offsets_,positions_,sums_,bases_,histogram_,invalid_;
    Buffer<PrefixResult> result_;
    Buffer<unsigned char,true> host_rgb_,host_entropy_;
    Buffer<unsigned short,true> host_quant_;
    Buffer<float,true> host_cosine_;
    Buffer<Code,true> host_codes_;
    Buffer<unsigned,true> host_histogram_;
    Buffer<PrefixResult,true> host_result_;

    void event(Phase phase) {
        check(hipEventRecord(event_,stream_),"record JPEG stage event");phase_=phase;
    }
    void prefix_result(Phase phase) {
        check(hipMemcpyAsync(host_result_.get(),result_.get(),sizeof(PrefixResult),
                             hipMemcpyDeviceToHost,stream_),"copy JPEG prefix metadata");
        event(phase);
    }
    void entropy() {
        host_codes_.ensure(6*256);dc_.ensure(3*256);ac_.ensure(3*256);
        for(int c=0;c<3;++c) {
            const auto& component=jpeg_.comp_info[c];
            auto dc=make_codes(jpeg_.dc_huff_tbl_ptrs[component.dc_tbl_no]);
            auto ac=make_codes(jpeg_.ac_huff_tbl_ptrs[component.ac_tbl_no]);
            std::copy(dc.begin(),dc.end(),host_codes_.get()+c*256);
            std::copy(ac.begin(),ac.end(),host_codes_.get()+(c+3)*256);
        }
        check(hipMemcpyAsync(dc_.get(),host_codes_.get(),3*256*sizeof(Code),hipMemcpyHostToDevice,stream_),"upload DC table");
        check(hipMemcpyAsync(ac_.get(),host_codes_.get()+3*256,3*256*sizeof(Code),hipMemcpyHostToDevice,stream_),"upload AC table");
        bits_.ensure(size_t(blocks_)*(MAX_BITS/8));lengths_.ensure(blocks_);offsets_.ensure(blocks_);
        const auto tiles=image_jpeg_checked_prefix::tile_count(blocks_);sums_.ensure(tiles);bases_.ensure(tiles);
        check(hipMemsetAsync(bits_.get(),0,size_t(blocks_)*(MAX_BITS/8),stream_),"clear JPEG entropy blocks");
        encode_blocks<<<(blocks_+127)/128,128,0,stream_>>>(scan_.get(),previous_.get(),components_.get(),dc_.get(),ac_.get(),bits_.get(),lengths_.get(),blocks_);
        check(hipGetLastError(),"GPU JPEG Huffman encode");
        check(image_jpeg_checked_prefix::launch<unsigned short,false>(lengths_.get(),offsets_.get(),sums_.get(),bases_.get(),result_.get(),blocks_,stream_),"checked JPEG bit prefix");
        header_=image_jpeg_full::header(jpeg_,width_,height_,sampling_);
        prefix_result(Phase::Bits);
    }
public:
    Slot() {
        check(hipSetDevice(0),"select JPEG device");
        check(hipStreamCreateWithFlags(&stream_,hipStreamNonBlocking),"create JPEG slot stream");
        auto code=hipEventCreateWithFlags(&event_,hipEventDisableTiming);
        if(code!=hipSuccess) {hipStreamDestroy(stream_);stream_=nullptr;check(code,"create JPEG slot event");}
    }
    Slot(const Slot&)=delete;
    Slot& operator=(const Slot&)=delete;
    ~Slot() {
        if(stream_)hipStreamSynchronize(stream_);
        if(jpeg_live_)jpeg_destroy_compress(&jpeg_);
        if(event_)hipEventDestroy(event_);
        if(stream_)hipStreamDestroy(stream_);
        // Buffer destructors run only after all asynchronous references are retired.
    }
    bool idle() const {return phase_==Phase::Idle;}
    Phase phase() const {return phase_;}
    hipStream_t stream() const {return stream_;}
    void start(const std::vector<unsigned char>& rgb,int width,int height,int quality,
               int sampling,bool optimized,bool download) {
        if(!idle())throw std::runtime_error("JPEG slot is still occupied");
        prepared_=false;
        submit(&rgb,width,height,quality,sampling,optimized,download);
    }
    // Preparation owns a private immutable device copy. A normal start invalidates
    // it even when dimensions match, so changing host inputs cannot reuse old RGB.
    void prepare(const std::vector<unsigned char>& rgb,int width,int height,int quality,
                 int sampling,bool optimized,bool download) {
        start(rgb,width,height,quality,sampling,optimized,download);
        try {
            while(!poll())check(hipEventSynchronize(event_),"wait JPEG preparation stage");
            (void)finish();prepared_=true;
        }catch(...) {hipStreamSynchronize(stream_);phase_=Phase::Failed;prepared_=false;throw;}
    }
    void start_prepared() {
        if(!idle()||!prepared_)throw std::runtime_error("JPEG slot has no idle prepared input");
        submit(nullptr,width_,height_,quality_,sampling_,optimized_,download_);
    }
private:
    void submit(const std::vector<unsigned char>* rgb,int width,int height,int quality,
                int sampling,bool optimized,bool download) {
        if(width<=0||height<=0||width>65535||height>65535||quality<1||quality>100||
           (sampling!=1&&sampling!=2)||(rgb&&rgb->size()!=size_t(width)*height*3))
            throw std::runtime_error("invalid JPEG slot input");
        const int mx=(width+sampling*8-1)/(sampling*8),my=(height+sampling*8-1)/(sampling*8);
        const size_t blocks=size_t(mx)*my*(sampling==2?6:3);
        // Current shared transform kernels use signed coefficient indices.
        // Reject before allocation/dispatch instead of overflowing those indices.
        if(blocks>size_t(std::numeric_limits<int>::max())/64)
            throw std::runtime_error("JPEG slot exceeds current transform index capacity");
        phase_=Phase::Preparing;
        try {
        width_=width;height_=height;sampling_=sampling;blocks_=int(blocks);quality_=quality;
        optimized_=optimized;download_=download;
        if(jpeg_live_)jpeg_destroy_compress(&jpeg_);
        jpeg_={};jpeg_.err=jpeg_std_error(&jpeg_errors_);jpeg_create_compress(&jpeg_);jpeg_live_=true;
        jpeg_.image_width=width;jpeg_.image_height=height;jpeg_.input_components=3;jpeg_.in_color_space=JCS_RGB;
        jpeg_set_defaults(&jpeg_);jpeg_set_quality(&jpeg_,quality,TRUE);
        jpeg_.comp_info[0].h_samp_factor=sampling;jpeg_.comp_info[0].v_samp_factor=sampling;
        for(int c=1;c<3;++c) {jpeg_.comp_info[c].h_samp_factor=1;jpeg_.comp_info[c].v_samp_factor=1;}
        if(rgb) {
            rgb_.ensure(rgb->size());host_rgb_.ensure(rgb->size());
            std::memcpy(host_rgb_.get(),rgb->data(),rgb->size());
            check(hipMemcpyAsync(rgb_.get(),host_rgb_.get(),rgb->size(),hipMemcpyHostToDevice,stream_),"upload pinned RGB");
        }
        host_cosine_.ensure(64);cosine_.ensure(64);host_quant_.ensure(3*64);
        host_result_.ensure(1);result_.ensure(1);
        for(int x=0;x<8;++x)for(int u=0;u<8;++u)
            host_cosine_.get()[x*8+u]=std::cos(float((2*x+1)*u)*3.14159265358979323846f/16.0f);
        check(hipMemcpyAsync(cosine_.get(),host_cosine_.get(),64*sizeof(float),hipMemcpyHostToDevice,stream_),"upload pinned cosine");
        std::array<int,3> bx{},by{};
        for(int c=0;c<3;++c) {
            const int scale=c?sampling:1,pw=(width+scale-1)/scale,ph=(height+scale-1)/scale;
            bx[c]=(pw+7)/8;by[c]=(ph+7)/8;size_t pixels=size_t(pw)*ph,terms=size_t(bx[c])*by[c]*64;
            planes_[c].ensure(pixels);coefficients_[c].ensure(terms);quant_[c].ensure(64);
            std::copy_n(jpeg_.quant_tbl_ptrs[jpeg_.comp_info[c].quant_tbl_no]->quantval,64,host_quant_.get()+c*64);
            check(hipMemcpyAsync(quant_[c].get(),host_quant_.get()+c*64,64*sizeof(unsigned short),hipMemcpyHostToDevice,stream_),"upload pinned quant table");
            image_jpeg_encoder::rgb_to_plane<<<(pixels+255)/256,256,0,stream_>>>(rgb_.get(),planes_[c].get(),width,height,pw,ph,c,sampling);
            check(hipGetLastError(),"GPU JPEG color");
            image_jpeg_encoder::forward_dct_quantize<<<(terms+255)/256,256,0,stream_>>>(planes_[c].get(),quant_[c].get(),cosine_.get(),coefficients_[c].get(),pw,ph,bx[c],by[c]);
            check(hipGetLastError(),"GPU JPEG transform");
        }
        scan_.ensure(blocks*64);previous_.ensure(blocks);components_.ensure(blocks);
        image_jpeg_full::gather_mcu_coefficients<<<(blocks*64+255)/256,256,0,stream_>>>(coefficients_[0].get(),coefficients_[1].get(),coefficients_[2].get(),scan_.get(),previous_.get(),components_.get(),bx[0],by[0],bx[1],by[1],mx,mx*my,sampling);
        check(hipGetLastError(),"GPU JPEG MCU gather");
        if(optimized_) {
            histogram_.ensure(4*256);invalid_.ensure(1);host_histogram_.ensure(4*256+1);
            check(hipMemsetAsync(histogram_.get(),0,4*256*sizeof(unsigned),stream_),"clear JPEG histogram");
            check(hipMemsetAsync(invalid_.get(),0,sizeof(unsigned),stream_),"clear JPEG histogram guard");
            image_jpeg_opt::histogram<<<(blocks_+127)/128,128,0,stream_>>>(scan_.get(),previous_.get(),components_.get(),histogram_.get(),invalid_.get(),blocks_);
            check(hipGetLastError(),"GPU JPEG histogram");
            check(hipMemcpyAsync(host_histogram_.get(),histogram_.get(),4*256*sizeof(unsigned),hipMemcpyDeviceToHost,stream_),"download symbol counts");
            check(hipMemcpyAsync(host_histogram_.get()+4*256,invalid_.get(),sizeof(unsigned),hipMemcpyDeviceToHost,stream_),"download histogram guard");
            event(Phase::Histogram);
        } else entropy();
        } catch(...) {
            hipStreamSynchronize(stream_);phase_=Phase::Failed;prepared_=false;throw;
        }
    }
public:
    bool poll() {
        try {return advance();}
        catch(...) {hipStreamSynchronize(stream_);phase_=Phase::Failed;prepared_=false;throw;}
    }
private:
    bool advance() {
        if(phase_==Phase::Failed||phase_==Phase::Preparing)
            throw std::runtime_error("JPEG slot is not usable after submission failure");
        if(phase_==Phase::Ready)return true;
        if(phase_==Phase::Idle)return false;
        auto ready=hipEventQuery(event_);if(ready==hipErrorNotReady)return false;check(ready,"query JPEG stage event");
        if(phase_==Phase::Histogram) {
            if(host_histogram_.get()[4*256])throw std::runtime_error("invalid optimized JPEG symbol");
            for(int g=0;g<2;++g) {
                image_jpeg_opt::make_table(jpeg_.dc_huff_tbl_ptrs[g],host_histogram_.get()+g*256);
                image_jpeg_opt::make_table(jpeg_.ac_huff_tbl_ptrs[g],host_histogram_.get()+(g+2)*256);
            }
            entropy();return false;
        }
        if(phase_==Phase::Bits) {
            auto result=*host_result_.get();
            if(result.errors||!result.total)throw std::runtime_error("invalid or overflowing GPU JPEG entropy");
            raw_bytes_=result.total/8+(result.total%8!=0);
            packed_.ensure(raw_bytes_);positions_.ensure(raw_bytes_);
            auto tiles=image_jpeg_checked_prefix::tile_count(raw_bytes_);sums_.ensure(tiles);bases_.ensure(tiles);
            pack_bytes<<<(raw_bytes_+255)/256,256,0,stream_>>>(bits_.get(),offsets_.get(),packed_.get(),blocks_,result.total,raw_bytes_);
            check(hipGetLastError(),"GPU JPEG packing");
            check(image_jpeg_checked_prefix::launch<unsigned char,true>(packed_.get(),positions_.get(),sums_.get(),bases_.get(),result_.get(),raw_bytes_,stream_),"checked JPEG stuffing prefix");
            prefix_result(Phase::Stuff);return false;
        }
        if(phase_==Phase::Stuff) {
            auto result=*host_result_.get();
            if(result.errors||result.total<raw_bytes_)throw std::runtime_error("invalid or overflowing JPEG stuffing");
            stuffed_bytes_=result.total;stuffed_.ensure(stuffed_bytes_);
            scatter_stuff<<<(raw_bytes_+255)/256,256,0,stream_>>>(packed_.get(),positions_.get(),stuffed_.get(),raw_bytes_);
            check(hipGetLastError(),"GPU JPEG stuffing");
            if(download_) {
                host_entropy_.ensure(stuffed_bytes_);
                check(hipMemcpyAsync(host_entropy_.get(),stuffed_.get(),stuffed_bytes_,hipMemcpyDeviceToHost,stream_),"download pinned JPEG entropy");
            }
            event(Phase::Download);return false;
        }
        phase_=Phase::Ready;return true;
    }
public:
    std::vector<unsigned char> finish() {
        if(phase_!=Phase::Ready)throw std::runtime_error("JPEG result not ready");
        std::vector<unsigned char> output;
        if(download_) {
            output=header_;output.insert(output.end(),host_entropy_.get(),host_entropy_.get()+stuffed_bytes_);
            output.push_back(0xff);output.push_back(0xd9);
        }
        phase_=Phase::Idle;return output;
    }
    size_t encoded_bytes() const {return header_.size()+stuffed_bytes_+2;}
};
} // namespace image_jpeg_pipeline
