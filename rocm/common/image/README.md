# Shared HIP image stages

This directory starts the shared backend in the [image migration plan](../../../migration/image-libraries-plan.md).
`canny_stages.h` exposes a C ABI for pitched C1/C3 unsigned-byte input and tightly packed device outputs: signed Sobel dx/dy, exact integer L2 magnitude, and non-maximum suppression. The caller supplies the stream and all buffers. The implementation performs pixel arithmetic in HIP kernels.

These stages are a development component. They do not produce a final Canny mask and do not qualify an original NPP or NPP+ sample. Native threshold/connection behavior, original Python preprocessing, complete file workflows and benchmarks remain pending. The [frozen stage contract](../../../migration/rewrite/image-canny-stages-contract.json) describes precisely what the independent checks establish.

Run inside the locked ROCm 10.1 foundation using an allowed device selected as described in [the project usage guide](../../../migration/usage.md):

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh \
  python3 tools/moat/image_canny_stages.py
build/image-cpu-venv/bin/python tools/moat/image_canny_stages_reference.py
```

The second command uses the private CPU reference environment recorded in `migration/reports/image-I0-CPU-environment.json`. Its NumPy oracle is separate from the GPU implementation. Every build, invocation and full-array comparison is archived through the experiment recorder. Current results and unresolved differences are in [the execution log](../../../migration/reports/image-libraries-progress.md).
