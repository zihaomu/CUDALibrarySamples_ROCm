from catalog import ROOT
from batches9_11_spec import GROUPS,kind
for source in GROUPS['b11']:
 text=(ROOT/source).read_text().split('#include')[0]+'// MIGRATION_BATCH11: sparse CPU symbolic analysis and actual GPU numerical factorization/solve.\n#include "batch11_sparse.hpp"\nint main(){return migration_batch::sparse11_main("'+kind(source)+'");}\n'
 for base in ['rocm/ported','build/cuda-observed']:
  p=ROOT/base/source;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
