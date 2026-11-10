# Existing-fork adapter

The user authorized adopting the existing zihaomu/CUDALibrarySamples_ROCm fork.
MOAT is pinned at 7b5082cc516c61b91038295346adbe8a1b5d8315, under its MIT license.
The canonical state machine and skills are unchanged. `tools/moat/control.py`
sets the state library's `PORT_BRANCH` to `rocm` before invoking its CLI and
checks the pinned skill/library hashes. Its origin is a local bare repository;
the AMD-Ecosystem remote remains a read-only source. No upstream contribution
or organization operation is authorized by this adapter.

One control project covers the actual implementation repository. Its source
checkout is linked to the existing fork checkout, and per-sample work is indexed
by the original 639 catalog IDs. The generated MOAT surface census includes
implementation sources as well as CUDA references; its raw file count is not
the original-entrypoint denominator. Pending surface remains owed. Whole-project
completion and upstream PR readiness are not asserted by a batch qualification.

Linux/gfx1201/ROCm 10.1 is the approved qualification profile. Required upstream
wave64/Windows gates are unchanged and remain unverified. The workspace launcher,
immutable image and PCI/physical-device guard override fleet example recipes.
Public fork documentation intentionally names the selected migration workflow;
this project is not being submitted to NVIDIA as an upstream port.

Support state lives in `migration/samples.yaml`; workflow stage lives in the
control project's status.json. The adapter never writes MOAT locks, waivers,
approval or state fields directly. Use the real library CLI for transitions.

Commands:

```bash
python3 tools/moat/control.py show CUDALibrarySamples_ROCm
python3 tools/moat/progress.py
python3 tools/moat/audit.py
```

Each experiment has an immutable sealed directory, separate process outcome and
independent correctness results. Raw large files stay under artifacts with hashes;
text/JSON evidence is archived under migration/reports/evidence/rewrite. The
initial constructor failure is retained and explicitly recovered as NOT_RUN.
