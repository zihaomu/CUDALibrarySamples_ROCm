// SPDX-License-Identifier: Apache-2.0
#include "image/jpeg_encoder_pipeline.hpp"
#include "image/jpeg_opt_full_gpu.hpp"
#include <filesystem>
#include <thread>
#include <dlfcn.h>

int main(int argc,char**argv) {
    try {
        if(argc!=10)throw std::runtime_error("usage: input width height quality sampling optimized jobs download output-dir");
        Dl_info library{};
        if(!dladdr(reinterpret_cast<void*>(jpeg_std_error),&library)||!library.dli_fname)
            throw std::runtime_error("cannot resolve loaded libjpeg");
        std::cerr<<"JPEG_LIBRARY="<<library.dli_fname<<'\n';
        auto rgb=image_jpeg_encoder::read_binary(argv[1]);
        int w=std::stoi(argv[2]),h=std::stoi(argv[3]),q=std::stoi(argv[4]),s=std::stoi(argv[5]);
        bool opt=std::stoi(argv[6]),download=std::stoi(argv[8]);int jobs=std::stoi(argv[7]);
        std::filesystem::path out=argv[9];std::filesystem::create_directories(out);
        if(jobs==0) {
            auto reference=opt?image_jpeg_opt::encode_optimized(rgb,w,h,q,s):image_jpeg_full::encode(rgb,w,h,q,s);
            image_jpeg_encoder::write_binary((out/"serial-reference.jpg").c_str(),reference.data(),reference.size());
            return 0;
        }
        if(jobs!=6)throw std::runtime_error("six jobs required for reuse probe");
        image_jpeg_pipeline::Slot slots[2];int ids[2]={-1,-1},next=0,done=0,max_pending=0;
        size_t after_warmup=0,last=0;unsigned polls=0;bool warm=false;
        while(done<jobs) {
            for(int i=0;i<2;++i) {
                if(ids[i]<0&&next<jobs) {
                    // Finish both first-use jobs before the allocation-reuse interval.
                    if(next>=2&&!warm)continue;
                    ids[i]=next++;
                    slots[i].start(rgb,w,h,q,s,opt,download);
                }
            }
            max_pending=std::max(max_pending,int(ids[0]>=0)+int(ids[1]>=0));
            for(int i=0;i<2;++i)if(ids[i]>=0) {
                ++polls;
                if(slots[i].poll()) {
                    auto bytes=slots[i].finish();last=slots[i].encoded_bytes();
                    if(download)image_jpeg_encoder::write_binary((out/(std::to_string(ids[i])+".jpg")).c_str(),bytes.data(),bytes.size());
                    else if(!bytes.empty())throw std::runtime_error("device-only returned payload");
                    ids[i]=-1;++done;
                }
            }
            if(done==2&&!warm) {warm=true;after_warmup=image_jpeg_pipeline::workspace_growths.load();}
            std::this_thread::yield();
        }
        size_t steady_growth=image_jpeg_pipeline::workspace_growths.load()-after_warmup;
        std::cout<<"{\"completed\":"<<done<<",\"max_pending\":"<<max_pending
                 <<",\"steady_workspace_growths\":"<<steady_growth<<",\"initial_workspace_growths\":"<<after_warmup
                 <<",\"polls\":"<<polls<<",\"encoded_bytes\":"<<last<<",\"payload_download\":"<<(download?"true":"false")<<"}\n";
        if(steady_growth||max_pending!=2)throw std::runtime_error("workspace/pipeline probe failed");
        return 0;
    } catch(const std::exception&e) {std::cerr<<e.what()<<'\n';return 1;}
}
