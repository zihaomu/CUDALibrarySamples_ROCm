// SPDX-License-Identifier: Apache-2.0
#define IMAGE_JPEG_PIPELINE_TEST_FAULTS
#include "image/jpeg_encoder_pipeline.hpp"
#include <thread>
int main() {
    try {
        using namespace image_jpeg_pipeline;
        std::vector<unsigned char> rgb(257*259*3);
        for(size_t i=0;i<rgb.size();++i)rgb[i]=(i*97+i/71)%256;
        for(int fail_after:{7,10,20,27,30}) {
            bool rejected=false,again=false,poll_again=false;
            {
                Slot slot;workspace_fail_after=fail_after;
                try {slot.start(rgb,257,259,90,2,false,true);while(!slot.poll())std::this_thread::yield();}
                catch(const std::exception&) {rejected=true;}
                workspace_fail_after=-1;
                if(!rejected||slot.idle()||slot.phase()!=Slot::Phase::Failed)
                    throw std::runtime_error("fault did not poison slot");
                try {slot.start(rgb,257,259,90,2,false,true);}catch(const std::exception&){again=true;}
                try {slot.poll();}catch(const std::exception&){poll_again=true;}
                if(!again||!poll_again)throw std::runtime_error("failed slot was reusable");
            }
            Slot recovery;recovery.start(rgb,257,259,90,2,false,true);
            while(!recovery.poll())std::this_thread::yield();
            auto jpeg=recovery.finish();if(jpeg.size()<4||jpeg[0]!=255||jpeg[1]!=216)throw std::runtime_error("recovery failed");
            std::cout<<"{\"fault_after\":"<<fail_after<<",\"rejected\":true,\"reuse_rejected\":true,\"new_slot_recovered\":true}\n";
        }
        return 0;
    }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
