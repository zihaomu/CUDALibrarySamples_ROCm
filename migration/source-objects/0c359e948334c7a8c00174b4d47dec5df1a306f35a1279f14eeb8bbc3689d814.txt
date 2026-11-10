"""Package only selected B9--B11 observations and locked project dependencies."""
import pathlib,tarfile
from catalog import ROOT
from batches9_11_spec import ALL
files=[ROOT/'build/cuda-observed'/s for s in ALL if (ROOT/'build/cuda-observed'/s).is_file()]
files += [ROOT/'rocm/common'/n for n in ['observe.hpp','binary_observe.hpp','batches_runtime.hpp','batch9_codec.hpp','batch10_jpeg.hpp','batch11_sparse.hpp'] if (ROOT/'rocm/common'/n).exists()]
files += [ROOT/'tools/migration'/n for n in ['catalog.py','run.py','batches9_11_run.py','batches9_11_spec.py','batch10_case.py'] if (ROOT/'tools/migration'/n).exists()]+[ROOT/'migration/roadmap.json']
with tarfile.open(ROOT/'build/batches9_11-cuda.tar','w') as t:
 for p in files:t.add(p,arcname=str(p.relative_to(ROOT)))
 for d in ['build/cpu-codecs','build/cuda-sdk','tests/fixtures/batch10','build/b9-cross-fixtures']:
  if (ROOT/d).exists():t.add(ROOT/d,arcname=d)
 for d in ['nvJPEG/nvJPEG-Decoder/input_images','nvJPEG/Image-Resize-WaterMark/NVLogo.jpg','nvJPEG/nvJPEG-Decoder/tests/test_decoder.py']:
  t.add(ROOT/d,arcname=d)
print('Packaged B9--B11 CUDA observations and project overlays')
