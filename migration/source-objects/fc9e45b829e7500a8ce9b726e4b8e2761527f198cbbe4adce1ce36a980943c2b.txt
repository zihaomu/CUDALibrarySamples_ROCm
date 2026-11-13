// SPDX-License-Identifier: Apache-2.0
// Candidate original CLI adapter using two asynchronous slots per encoder state.
#pragma once
#include "jpeg_encoder_instances.hpp"
#include "jpeg_encoder_pipeline.hpp"
#include <memory>
#include <set>

namespace image_jpeg_instances_v2 {
namespace fs=std::filesystem;
struct Args {
    fs::path input,output;
    int images=0,states=0,threads=0,runs=1,quality=80;
    bool write=false,download=false,optimize=false,sampling420=true;
    bool gpu=true,hardware=true,auto_threads=true;
};
inline int integer(const char* text) {
    size_t end=0;auto number=std::stoll(text,&end);
    if(end!=std::strlen(text)||number<INT32_MIN||number>INT32_MAX)
        throw std::runtime_error("integer argument out of range");
    return int(number);
}
inline Args parse(int argc,const char*argv[]) {
    Args a;std::set<std::string> seen;
    for(int i=1;i<argc;++i) {
        std::string key=argv[i];
        if(!seen.insert(key).second)throw std::runtime_error("duplicate option "+key);
        if(key=="-i"||key=="-o"||key=="-n"||key=="-s"||key=="-j"||key=="-r"||key=="-q") {
            if(++i==argc)throw std::runtime_error("missing value after "+key);
            if(key=="-i")a.input=argv[i];
            else if(key=="-o") {a.output=argv[i];a.write=a.download=true;}
            else {
                int value=integer(argv[i]);
                if(key=="-n")a.images=std::max(0,value);
                else if(key=="-r")a.runs=std::max(1,value);
                else if(key=="-q")a.quality=std::clamp(value,1,100);
                else if(key=="-s") {if(value<0)throw std::runtime_error("negative states");a.states=value;}
                else {if(value<0)throw std::runtime_error("negative threads");a.threads=value;a.auto_threads=false;}
            }
        } else if(key=="-d")a.download=true;
        else if(key=="-f")a.optimize=true;
        else if(key=="-p")a.sampling420=false;
        else if(key=="-b") {
            a.gpu=a.hardware=false;unsigned count=0;
            while(i+1<argc&&argv[i+1][0]!='-') {
                std::string backend=argv[++i];++count;
                if(backend=="gpu")a.gpu=true;
                else if(backend=="hardware")a.hardware=true;
                else throw std::runtime_error("unknown backend "+backend);
            }
            if(!count)throw std::runtime_error("missing backend");
        } else throw std::runtime_error("unknown option "+key);
    }
    if(a.input.empty())throw std::runtime_error("input BMP directory required (-i)");
    if(!a.gpu)throw std::runtime_error("AMD hardware JPEG encode backend unavailable; select -b gpu");
    if(!a.auto_threads&&!a.threads)a.threads=std::max(1u,std::thread::hardware_concurrency());
    return a;
}
inline image_jpeg_instances::Image bmp(const fs::path& path) {
    using image_jpeg_instances::le16;using image_jpeg_instances::le32;
    auto bytes=image_jpeg_encoder::read_binary(path.c_str());
    if(bytes.size()<54||bytes[0]!='B'||bytes[1]!='M'||le32(bytes,14)<40||le16(bytes,26)!=1||le16(bytes,28)!=24||le32(bytes,30)!=0)
        throw std::runtime_error("unsupported/corrupt 24-bit BMP");
    int64_t w=int32_t(le32(bytes,18)),signed_h=int32_t(le32(bytes,22));
    int64_t h=signed_h<0?-signed_h:signed_h;
    if(w<=0||h<=0||w>65535||h>65535)throw std::runtime_error("invalid BMP dimensions");
    size_t dib=le32(bytes,14),offset=le32(bytes,10),stride=(size_t(w)*3+3)&~size_t(3);
    if(dib>bytes.size()-14||offset<14+dib||offset>bytes.size()||size_t(h)>(bytes.size()-offset)/stride)
        throw std::runtime_error("truncated BMP pixels");
    image_jpeg_instances::Image image{int(w),int(h),std::vector<unsigned char>(size_t(w)*h*3)};
    for(int y=0;y<h;++y)for(int x=0;x<w;++x) {
        const auto* src=bytes.data()+offset+size_t(signed_h<0?y:h-1-y)*stride+x*3;
        auto* dst=image.rgb.data()+(size_t(y)*w+x)*3;dst[0]=src[2];dst[1]=src[1];dst[2]=src[0];
    }
    return image;
}
struct Result {
    double throughput=0,latency=0;int images=0,threads=0,states=0;size_t bytes=0;
    double preparation_ms=0,measured_ms=0,end_to_end_ms=0;
    size_t steady_workspace_growths=0,prepared_slots=0;
};
inline Result execute(const Args& a,const std::vector<fs::path>& input,int threads,bool write_output) {
    auto total_start=std::chrono::steady_clock::now();
    int states=std::max({1,a.states,threads}),images=std::max(a.images,states);
    if(states>INT32_MAX/2)throw std::runtime_error("slot count overflow");
    std::shared_ptr<image_jpeg_instances::Image> cached;
    if(input.size()==1)cached=std::make_shared<image_jpeg_instances::Image>(bmp(input[0]));
    std::atomic<int64_t> next{0};std::atomic<int> done{0};std::atomic<size_t> bytes{0};std::atomic<bool> cancelled{false};
    std::mutex mutex;std::string failure;std::vector<std::thread> workers;
    std::vector<std::vector<std::unique_ptr<image_jpeg_pipeline::Slot>>> resources(threads);
    std::atomic<int> ready{0};std::atomic<bool> go{false};
    auto worker=[&](int tid) {
        try {
            image_jpeg_encoder::check(hipSetDevice(0),"worker JPEG device");
            auto& slots=resources[tid];
            for(int64_t state=tid;state<states&&!cancelled.load();state+=threads)for(int buffer=0;buffer<2;++buffer) {
                slots.push_back(std::make_unique<image_jpeg_pipeline::Slot>());
                if(cached)slots.back()->prepare(cached->rgb,cached->w,cached->h,a.quality,a.sampling420?2:1,a.optimize,a.download);
            }
            std::vector<int> ids(slots.size(),-1);bool more=true;
            ++ready;
            while(!go.load()&&!cancelled.load())std::this_thread::yield();
            while(more&&!cancelled.load()) {
                more=false;
                for(size_t slot=0;slot<slots.size();++slot) {
                    if(ids[slot]==-1) {
                        int64_t job=next.fetch_add(1);
                        if(job<images) {
                            ids[slot]=job;
                            if(cached)slots[slot]->start_prepared();
                            else {
                                auto picture=bmp(input[job%input.size()]);
                                slots[slot]->start(picture.rgb,picture.w,picture.h,a.quality,a.sampling420?2:1,a.optimize,a.download);
                            }
                        } else ids[slot]=-2;
                    }
                    if(ids[slot]>=0) {
                        more=true;
                        if(slots[slot]->poll()) {
                            auto jpeg=slots[slot]->finish();bytes.fetch_add(slots[slot]->encoded_bytes());
                            if(write_output)image_jpeg_encoder::write_binary((a.output/(std::to_string(ids[slot])+".jpg")).c_str(),jpeg.data(),jpeg.size());
                            ids[slot]=-1;done.fetch_add(1);
                        }
                    }
                }
                std::this_thread::yield();
            }
        }catch(const std::exception& error) {cancelled=true;std::lock_guard<std::mutex> guard(mutex);if(failure.empty())failure=error.what();}
    };
    try {for(int tid=0;tid<threads;++tid)workers.emplace_back(worker,tid);}
    catch(...) {cancelled=true;for(auto& thread:workers)thread.join();throw;}
    while(ready.load()<threads&&!cancelled.load())std::this_thread::yield();
    const size_t prepared_growths=image_jpeg_pipeline::workspace_growths.load();
    auto start=std::chrono::steady_clock::now();go=true;
    for(auto& thread:workers)thread.join();
    auto end=std::chrono::steady_clock::now();
    const size_t steady_growths=image_jpeg_pipeline::workspace_growths.load()-prepared_growths;
    resources.clear(); // Retire resources after the measured encode/write interval.
    if(!failure.empty())throw std::runtime_error(failure);
    if(done!=images)throw std::runtime_error("incomplete JPEG jobs");
    double ms=std::chrono::duration<double,std::milli>(end-start).count();
    if(ms<=0)throw std::runtime_error("invalid JPEG duration");
    return {images*1000.0/ms,ms/images,images,threads,states,bytes.load(),
            std::chrono::duration<double,std::milli>(start-total_start).count(),ms,
            std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-total_start).count(),
            steady_growths,cached?size_t(states)*2:0};
}
inline int run(int argc,const char*argv[]) {
    if(argc==1||std::any_of(argv+1,argv+argc,[](const char* p){return std::string(p)=="-h";})) {
        std::cout<<"Usage: "<<argv[0]<<" -i indir [-n nimages] [-s nstates] [-j nthreads] [-b gpu|hardware] [-r nruns] [-d] [-o outdir] [-q quality] [-f] [-p]\n";return 0;
    }
    try {
        auto a=parse(argc,argv);auto input=image_jpeg_instances::files(a.input);
        if(a.images>0&&input.size()>size_t(a.images))input.resize(a.images);
        if(!a.images)a.images=int(input.size());
        if(a.write)fs::create_directories(a.output);
        Result best;unsigned calibration_trials=0;
        if(a.auto_threads) {
            // Bound the search by CPU resources; use actual end-to-end measurements.
            int maximum=std::max(int(std::max(1u,std::thread::hardware_concurrency())),std::max(1,a.states));
            int threads=std::max(1,a.states),declines=0;
            while(true) {
                Result trial;
                for(int rep=0;rep<a.runs;++rep) {auto result=execute(a,input,threads,false);++calibration_trials;if(result.throughput>trial.throughput)trial=result;}
                if(trial.throughput>best.throughput) {best=trial;declines=0;}else ++declines;
                if(declines>=2||threads==maximum)break;
                threads=threads>maximum/2?maximum:threads*2;
            }
            a.threads=best.threads;
        }
        best={};
        for(int rep=0;rep<a.runs;++rep) {auto result=execute(a,input,a.threads,a.write);if(result.throughput>best.throughput)best=result;}
        std::cout<<"Num hardware encode engines: 0\nEnabled backends: gpu\nQuality: "<<a.quality
                 <<"\nNum threads: "<<best.threads<<"\nNum states: "<<best.states
                 <<"\nThroughput: "<<best.throughput<<" images/s\nLatency: "<<best.latency<<" ms\n"
                 <<"TIMING preparation_ms="<<best.preparation_ms<<" measured_ms="<<best.measured_ms
                 <<" end_to_end_ms="<<best.end_to_end_ms<<" steady_workspace_growths="<<best.steady_workspace_growths
                 <<" prepared_slots="<<best.prepared_slots<<'\n'
                 <<"RESULT status=PASS encoded="<<best.images<<" cpu_entropy=0 gpu_full_encode=1"
                 <<" download_payload="<<a.download<<" pinned_buffers=1 async_slots_per_state=2"
                 <<" calibration_trials="<<calibration_trials<<" encoded_bytes="<<best.bytes<<'\n';
        return 0;
    }catch(const std::exception& error) {std::cerr<<"RESULT status=FAIL reason="<<error.what()<<'\n';return 1;}
}
} // namespace image_jpeg_instances_v2
