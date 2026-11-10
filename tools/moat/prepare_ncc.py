#!/usr/bin/env python3
"""Retain the original file/CLI/annotation/timing harness around the HIP NCC core."""
import re
from experiment import ROOT
p=ROOT/'NPP/templateMatching/templateMatching.cpp';text=p.read_text().replace('#include <npp.h>','#include "ncc_contract.hpp"')
text=text.replace('#include <cuda_runtime.h>','#include <hip/hip_runtime.h>')
text=re.sub(r'\bcuda([A-Z]\w*)',r'hip\1',text).replace('hipDeviceProp prop','hipDeviceProp_t prop')
marker='    printf("Image %dx%d, template'
capture='''    if (const char* directory=std::getenv("REWRITE_OUTPUT")) {
        auto save=[&](const char*name,const void*data,size_t bytes){std::ofstream file(std::string(directory)+"/"+name,std::ios::binary);file.write(static_cast<const char*>(data),bytes);};
        save("input.bin",image.data(),image.size());save("template.bin",tpl.data(),tpl.size());save("scores.bin",score.data(),score.size()*sizeof(float));
        int config[]={W,H,tx,ty,tw,th,iterations,bestX,bestY};save("config.bin",config,sizeof(config));save("best.bin",&bestScore,sizeof(bestScore));
    }

'''
if marker not in text:raise RuntimeError('Original harness marker changed')
text=text.replace(marker,capture+marker)
(ROOT/'rocm/ported/NPP/templateMatching/templateMatching.cpp').write_text(text)
print('Restored original NCC CLI/file/annotation/HIP event timing around project GPU core')
