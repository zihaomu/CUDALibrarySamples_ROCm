#!/usr/bin/env python3
import json,re
from pathlib import Path
from experiment import Experiment,ROOT,write
from snapshot import capture
e=Experiment('P1','existing-M1-CMake-regression','rocm',sources=[ROOT/'rocm/CMakeLists.txt',ROOT/'cmake/RewriteSamples.cmake',Path(__file__)])
write(e.path/'backend.observed.json',capture())
rc=e.command(['cmake','--build','build/rewrite-cmake','-j4'],'build-M1',timeout=240)
if rc==0:rc=e.command(['ctest','--test-dir','build/rewrite-cmake','--output-on-failure','--parallel','1'],'GPU-CTest',timeout=240)
text=(e.path/e.commands[-1]['stdout']).read_text();checks=[dict(check='build-and-CTest-processes',passed=rc==0),dict(check='all-16-existing-GPU-tests',passed='100% tests passed' in text and 'out of 16' in text)]
validation=dict(status='PASSED' if all(x['passed'] for x in checks) else 'FAILED',checks=checks)
evidence=e.finish(validation['status'],validation,reason=None if validation['status']=='PASSED' else 'CMake regression failure')
write(ROOT/'migration/reports/rewrite-cmake-regression.json',dict(**validation,evidence=evidence));print(evidence)
