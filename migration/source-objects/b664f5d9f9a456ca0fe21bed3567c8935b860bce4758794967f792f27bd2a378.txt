#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
[[ ${DEEPINFER_ROCM_RELEASE:-} == 10.1.0 ]] || { echo 'Use the locked ROCm 10.1.0 launcher.' >&2; exit 1; }
python tools/migration/device_guard.py
# The source commits are part of the project dependency lock.
if [[ ! -d build/deps/hipCOMP-core/.git ]]; then
  git clone https://github.com/ROCm/hipCOMP-core.git build/deps/hipCOMP-core
  git -C build/deps/hipCOMP-core checkout --detach 03df9f7369211ee15d370817165224c73fdc9a46
fi
if [[ ! -d build/deps/rocm-libraries/.git ]]; then
  git clone --filter=blob:none --sparse https://github.com/ROCm/rocm-libraries.git build/deps/rocm-libraries
  git -C build/deps/rocm-libraries sparse-checkout set projects/hiptensor
  git -C build/deps/rocm-libraries checkout --detach 380ea3ec237d03c4a384b4ed4c49fda82d9f81dd
fi
[[ $(git -C build/deps/hipCOMP-core rev-parse HEAD) == 03df9f7369211ee15d370817165224c73fdc9a46 ]]
[[ $(git -C build/deps/rocm-libraries rev-parse HEAD) == 380ea3ec237d03c4a384b4ed4c49fda82d9f81dd ]]
cmake -S build/deps/hipCOMP-core -B build/hipcomp -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=/opt/rocm/core-10.1 -DCMAKE_HIP_ARCHITECTURES=gfx1201 -DCMAKE_HIP_COMPILER=/opt/rocm/core-10.1/lib/llvm/bin/clang++ -DCMAKE_HIP_COMPILER_ROCM_ROOT=/opt/rocm/core-10.1 -DBUILD_TESTS=OFF
cmake --build build/hipcomp -j"${MIGRATION_BUILD_JOBS:-4}"
cmake -S build/deps/rocm-libraries/projects/hiptensor -B build/hiptensor -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=/opt/rocm/core-10.1 -DCMAKE_CXX_COMPILER=/opt/rocm/core-10.1/lib/llvm/bin/clang++ -DCMAKE_C_COMPILER=/opt/rocm/core-10.1/lib/llvm/bin/clang -DGPU_TARGETS=gfx1201 -DHIPTENSOR_BUILD_TESTS=OFF -DHIPTENSOR_BUILD_SAMPLES=OFF -DCMAKE_INSTALL_PREFIX="$PWD/build/project-sdk"
cmake --build build/hiptensor -j"${MIGRATION_BUILD_JOBS:-4}"
cmake --install build/hiptensor
