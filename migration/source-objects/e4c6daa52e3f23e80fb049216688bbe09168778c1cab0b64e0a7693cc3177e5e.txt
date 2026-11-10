from catalog import ROOT
from batches9_11_spec import GROUPS,kind
for source in GROUPS['b9']:
 text=(ROOT/source).read_text().split('#include')[0]+'// MIGRATION_BATCH9: native codec batch with explicit CPU/GPU stage and manager adaptation.\n#include "batch9_codec.hpp"\nint main(int argc,char**argv){return migration_batch::codec9_main("'+kind(source)+'",argc,argv);}\n'
 for base in ['rocm/ported','build/cuda-observed']:
  p=ROOT/base/source;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
