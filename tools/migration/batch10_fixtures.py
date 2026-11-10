"""Deterministic odd-size JPEG/CLI fixtures; original JPEG corpus remains untouched."""
import sys,json,hashlib
from catalog import ROOT
sys.path.insert(0,str(ROOT/'build/python-reference'))
from PIL import Image
root=ROOT/'tests/fixtures/batch10';root.mkdir(parents=True,exist_ok=True);w,h=129,97
rgb=Image.new('RGB',(w,h));rgb.putdata([((x*3)%256,(y*5)%256,(x+y)%256) for y in range(h) for x in range(w)])
for sub,name in [(0,'444'),(1,'422'),(2,'420')]:rgb.save(root/(name+'.jpg'),subsampling=sub,quality=90)
rgb.save(root/'progressive.jpg',progressive=True,quality=90);Image.new('L',(w,h),37).save(root/'gray.jpg');(root/'bad.jpg').write_bytes(b'not a JPEG stream')
(ROOT/'migration/environments/batch10-fixtures.json').write_text(json.dumps(dict(generator_sha256=hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest(),pillow=Image.__version__,files={p.name:dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in root.iterdir() if p.is_file()}),indent=2)+'\n')
