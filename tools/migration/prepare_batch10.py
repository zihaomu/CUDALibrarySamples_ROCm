from catalog import ROOT
from batches9_11_spec import GROUPS,kind
for source in GROUPS['b10']:
 if source.endswith('.py'):

  for base in ['rocm/ported','build/cuda-observed']:
   p=ROOT/base/source;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('# GPU CLI integration: retain every original assertion.\n'+(ROOT/source).read_text())
  continue
 text=(ROOT/source).read_text().split('#include')[0]+'// MIGRATION_BATCH10: rocJPEG hardware / explicit CPU fallback, GPU layout and postprocess.\n#include "batch10_jpeg.hpp"\nint main(int argc,const char**argv){return migration_batch::image10_main("'+kind(source)+'",argc,argv);}\n'
 for base in ['rocm/ported','build/cuda-observed']:
  p=ROOT/base/source;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
