#!/usr/bin/env python3
"""Install the same explicit SpVV graph semantics for HIP and CUDA."""
import re
from catalog import ROOT
source='cuSPARSE/graph_capture/graph_capture_example.c'
main=(ROOT/'tools/migration/batch3_graph_main.cpp').read_text()
for backend in ['rocm','cuda']:
    p=ROOT/('rocm/ported' if backend=='rocm' else 'build/cuda-observed')/source
    if 'MIGRATION_BATCH3' in p.read_text():continue
    prefix=p.read_text().split('int main')[0]
    body=main
    if backend=='cuda':
        body=body.replace('hipsparse','cusparse').replace('HIPSPARSE','CUSPARSE').replace('HIP_R_32F','CUDA_R_32F')
        body=re.sub(r'\bhip(?=[A-Z])','cuda',body)
    p.write_text('#include "observe.hpp"\n#include <string>\n#include <vector>\n#include <cstdlib>\n'+prefix+body)
print('Prepared genuine graph capture/replay adapters')
