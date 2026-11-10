# CUDA Library Samples targeting ROCm

Use `.agents/skills/cuda-library-to-rocm/SKILL.md` for source rewrites, library
selection, shared backend changes, review and validation. Preserve original CUDA
sources, stable catalog IDs and historical evidence. Work only within the scope
authorized by the user; adoption of the existing fork has already been authorized.

The parent workspace ROCm 10.1 environment and physical GPU policy apply. Use the
project launcher and device guard before GPU work. Record every attempt through
`tools/moat/experiment.py`; do not promote samples from a command exit alone.

MOAT role transitions use `tools/moat/control.py`. The control checkout is pinned
by `migration/moat/lock.json`; project state lives there, numerical support state
remains in `migration/samples.yaml`. Whole-project completion requires the full
recorded surface; an individual batch pass does not clear pending samples or
unverified platforms. Original and compatible CUDA baselines remain distinct.

After each completed experiment, failed attempt or stage handoff, update the
experimental index and relevant support reports and the plan in `../doc/`.
Do not discard a prior failure or silently reduce the required contract.
