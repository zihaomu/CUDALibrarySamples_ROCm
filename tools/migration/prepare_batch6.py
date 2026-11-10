from catalog import ROOT
from batches4_8_spec import GROUPS,kind
for s in GROUPS['b6']:
 text=(ROOT/s).read_text().split('#include')[0]+'// MIGRATION_BATCH6: original mathematical profile, explicit generic-X/typed dimension bridge.\n#include "batch6_solver.hpp"\nint main(){return migration_batch::solver_main("'+kind(s)+'");}\n'
 for base in ['rocm/ported','build/cuda-observed']:
  p=ROOT/base/s;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
