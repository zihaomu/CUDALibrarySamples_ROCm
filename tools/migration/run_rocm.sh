#!/usr/bin/env bash
set -euo pipefail
export HIP_VISIBLE_DEVICES=${HIP_VISIBLE_DEVICES:-2}
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
exec /home/zihaomu/zihaomu_workspace/rocm10-launch.sh bash -c '
  export TRITON_CACHE_DIR="$PWD/build/cache/rocm10.1-gfx1201/triton"
  export TORCH_EXTENSIONS_DIR="$PWD/build/cache/rocm10.1-gfx1201/torch"
  exec python tools/migration/run.py "$@"
' bash "$@"
