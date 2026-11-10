---
name: cuda-library-to-rocm
description: Rewrite CUDA library samples for ROCm using pinned MOAT roles, explicit backend contracts, independent CPU/CUDA validation and immutable experiment logs. Use for code rewrites, library selection, backend organization, review and validation in this repository.
---

# Project adapter

Read `migration/moat/lock.json`. Resolve its control checkout relative to the
implementation repository. Verify the pinned skill and state-library hashes,
then read the canonical `.claude/skills/cuda-to-rocm/SKILL.md` in that checkout
and the current role under `.claude/agents/`. References resolve relative to
the canonical skill, not this adapter. Never silently substitute another version.

Read the control project's `status.json`, `plan.md`, `notes.md`, and `surface.json`.
Use `python3 tools/moat/control.py` to transition its real MOAT state machine.
Use `migration/moat/tasks.json` for entrypoint coverage and
`migration/samples.yaml` for support conclusions. Parent workspace/user environment
requirements take precedence over upstream fleet recipes. The approved target is
the existing user fork/rocm branch, not the AMD-Ecosystem organization.

Use `tools/moat/experiment.py` to preserve commands, inputs, dependencies,
observed environments, raw stdout/stderr, numerical comparisons and failures.
Follow `migration/moat-rewrite-plan.md` sections 8-11. Freeze contracts and
thresholds before implementation; preserve source and input bytes for all sides.
Review with the canonical `pr-review` skill and validate the exact committed tree.

Do not infer GPU support from headers, symbols, HIPIFY exit, CPU fallback,
empty outputs or a reduced input. Device functions stay inside calling kernels;
distributed contracts require actual distinct GPUs and recorded communication.
Expected FP16 overflow is checked explicitly rather than hidden by input scaling.
