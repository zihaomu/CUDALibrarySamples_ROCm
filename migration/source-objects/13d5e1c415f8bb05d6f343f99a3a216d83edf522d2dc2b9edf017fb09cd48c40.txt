from catalog import ROOT
from batches4_8_spec import GROUPS,kind
for s in GROUPS['b7']:
 text=(ROOT/s).read_text().split('#include')[0]+'// MIGRATION_BATCH7: original precision and size; observed actual search and grouped dispatch.\n#include "batch7_gemm.hpp"\nint main(){return migration_batch::gemm7_main("'+kind(s)+'");}\n'
 for base in ['rocm/ported','build/cuda-observed']:
  p=ROOT/base/s;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
