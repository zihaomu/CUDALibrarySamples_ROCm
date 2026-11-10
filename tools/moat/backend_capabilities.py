#!/usr/bin/env python3
"""Observe installed entrypoints and CPU dependencies; these are capability probes."""
import json,shutil
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
e=Experiment('R3-R6','locked-library-execution-capabilities','rocm-probe',sources=[__file__]);write(e.path/'backend.observed.json',capture());site=Path('/opt/venv/lib/python3.13/site-packages');libraries=[site/'_rocm_sdk_libraries/lib/libhipsolver.so.1',site/'_rocm_sdk_libraries/lib/librocsolver.so.0',site/'_rocm_sdk_core/lib/host-math/lib/librocm-openblas.so.0',ROOT/'build/hipcomp/lib/libhipcomp.so']
records=[]
for path in libraries:
 if not path.is_file():continue
 rc=e.command(['nm','-D',str(path)],'symbols-'+path.name,timeout=60)
 stdout=(e.path/e.commands[-1]['stdout']).read_text();matches=[line for line in stdout.splitlines() if any(s in line.lower() for s in ['geev','gesvd','gesdd','cascaded','ans','gdeflate','zstd','deflate','bitcomp'])]
 records.append(dict(path=str(path),sha256=digest(path),symbols=matches,return_code=rc))
write(e.path/'capabilities.json',dict(libraries=records,profiler={name:shutil.which(name) for name in ['rocprofv3','rocprofv2','rocprof','ltrace']},warning='Exported symbols and linked CPU libraries do not establish which execution backend a numerical routine uses. Actual per-routine calls must be checked.'))
evidence=e.finish('OBSERVED');write(ROOT/'migration/reports/rewrite-backend-capabilities.json',dict(evidence=evidence,libraries=records));print(evidence)
