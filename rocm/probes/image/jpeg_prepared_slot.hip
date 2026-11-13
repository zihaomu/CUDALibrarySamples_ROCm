// SPDX-License-Identifier: Apache-2.0
// Resident-input ownership and invalidation regression; no CPU entropy path.
#include "image/jpeg_encoder_pipeline.hpp"
#include "image/jpeg_opt_full_gpu.hpp"

static std::vector<unsigned char> complete(image_jpeg_pipeline::Slot& slot) {
    while(!slot.poll())image_jpeg_encoder::check(hipStreamSynchronize(slot.stream()),"wait prepared slot stage");
    return slot.finish();
}

int main() {
    try {
        constexpr int width=17,height=19;
        std::vector<unsigned char> first(size_t(width)*height*3),second(first.size());
        for(size_t i=0;i<first.size();++i) {first[i]=(i*29+17)%256;second[i]=255-first[i];}
        auto a=image_jpeg_full::encode(first,width,height,80,2);
        auto b=image_jpeg_full::encode(second,width,height,80,2);
        if(a==b)throw std::runtime_error("reference inputs are not discriminating");
        image_jpeg_pipeline::Slot slot;
        slot.prepare(first,width,height,80,2,false,true);
        first=second; // Prepared device storage must not alias the host vector.
        for(int i=0;i<3;++i) {
            slot.start_prepared();
            bool occupied_rejected=false;
            try {slot.start_prepared();}catch(const std::exception&) {occupied_rejected=true;}
            if(!occupied_rejected||complete(slot)!=a)throw std::runtime_error("prepared ownership/reuse failure");
        }
        slot.start(second,width,height,80,2,false,true);
        if(complete(slot)!=b)throw std::runtime_error("normal start did not replace RGB");
        bool invalidated=false;
        try {slot.start_prepared();}catch(const std::exception&) {invalidated=true;}
        if(!invalidated)throw std::runtime_error("normal start failed to invalidate prepared input");
        slot.prepare(second,width,height,80,2,false,true);slot.start_prepared();
        if(complete(slot)!=b)throw std::runtime_error("reprepare failed");
        std::cout<<"{\"resident_ownership\":true,\"occupied_rejected\":true,\"normal_invalidates\":true,\"reprepare\":true}\n";
        return 0;
    }catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
