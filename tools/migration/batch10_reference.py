"""Independent libjpeg/Pillow pixels, full postprocess arrays, geometry and original GPU CLI tests."""
import ctypes,hashlib,json,pathlib,re,sys
from catalog import ROOT
from validate_blas import np
sys.path.insert(0,str(ROOT/'build/python-reference'))
from PIL import Image
from batches9_11_spec import kind
jpeg=ctypes.CDLL(str(ROOT/'build/cpu-codecs/lib/libturbojpeg.so'));jpeg.tjInitDecompress.restype=ctypes.c_void_p;jpeg.tjDestroy.argtypes=[ctypes.c_void_p];jpeg.tjDecompressHeader3.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int)];jpeg.tjDecompressToYUVPlanes.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(ctypes.c_void_p),ctypes.c_int,ctypes.POINTER(ctypes.c_int),ctypes.c_int,ctypes.c_int];cache={}
jpeg.tjPlaneWidth.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_int];jpeg.tjPlaneHeight.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_int];jpeg.tjDecompress2.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int]
def local_source(s):
 p=pathlib.Path(s)
 if p.exists():return p
 for name in ['tests/fixtures/','nvJPEG/']:
  if name in s:return ROOT/(name+s.split(name,1)[1])
 raise ValueError('source not available '+s)
def cpu_yuv(p):
 key=str(p)
 if key in cache:return cache[key]
 data=p.read_bytes();h=jpeg.tjInitDecompress();w=ctypes.c_int();he=ctypes.c_int();sub=ctypes.c_int();color=ctypes.c_int();assert jpeg.tjDecompressHeader3(h,data,len(data),ctypes.byref(w),ctypes.byref(he),ctypes.byref(sub),ctypes.byref(color))==0
 # Standard libjpeg sampling IDs: 444,422,420,GRAY,440,411,441.
 samples={0:(1,1),1:(2,1),2:(2,2),3:(0,0),4:(1,2),5:(4,1),6:(1,4)};sx,sy=samples[sub.value];shapes=[(he.value,w.value)]+([] if sub.value==3 else [((he.value+sy-1)//sy,(w.value+sx-1)//sx)]*2);padded_shapes=[(jpeg.tjPlaneHeight(c,he.value,sub.value),jpeg.tjPlaneWidth(c,w.value,sub.value)) for c in range(len(shapes))];arrays=[np.empty(shape,np.uint8) for shape in padded_shapes];ptrs=(ctypes.c_void_p*3)(*[a.ctypes.data for a in arrays],*([0]*(3-len(arrays))));strides=(ctypes.c_int*3)(*[a.shape[1] for a in arrays],*([0]*(3-len(arrays))));code=jpeg.tjDecompressToYUVPlanes(h,data,len(data),ptrs,w.value,strides,he.value,0);jpeg.tjDestroy(h);assert code==0;arrays=[a[:shape[0],:shape[1]].copy() for a,shape in zip(arrays,shapes)];cache[key]=arrays;return arrays
def cpu_rgb_fast(p):
 key='fast:'+str(p)
 if key in cache:return cache[key]
 size=Image.open(p).size;w,h=size;out=np.empty((h,w,3),np.uint8);data=p.read_bytes();handle=jpeg.tjInitDecompress();code=jpeg.tjDecompress2(handle,data,len(data),out.ctypes.data,w,w*3,h,0,256);jpeg.tjDestroy(handle);assert code==0;cache[key]=out;return out
def scale_box(v,s):
 if s==1:return v.copy()
 h,w=v.shape[:2];extra=v.shape[2:];out=np.empty(((h+s-1)//s,(w+s-1)//s)+extra,np.uint8)
 for y in range(out.shape[0]):
  for x in range(out.shape[1]):
   cell=v[y*s:min(h,(y+1)*s),x*s:min(w,(x+1)*s)].astype(np.uint32);count=cell.shape[0]*cell.shape[1];out[y,x]=(cell.sum(axis=(0,1))+count//2)//count
 return out
def lanczos(v,w,h):
 def axis(src,dst):
  x=(np.arange(dst)+.5)*src/dst-.5;index=np.floor(x).astype(int)[:,None]+np.arange(-2,4);distance=x[:,None]-index;weights=np.sinc(distance)*np.sinc(distance/3);weights/=weights.sum(axis=1)[:,None];return np.clip(index,0,src-1),weights
 ix,wx=axis(v.shape[1],w);iy,wy=axis(v.shape[0],h);temp=(v[:,ix,:].astype(np.float64)*wx[None,:,:,None]).sum(axis=2);result=(temp[iy,:,:]*wy[:,:,None,None]).sum(axis=1);return np.clip(np.floor(result+.5),0,255).astype(np.uint8)
def validate(source,case,d):
 record=json.loads((d/'case.json').read_text());checks=[];fallback=0
 def gate(name,yes,**details):checks.append(dict(check=name,passed=bool(yes),**details))
 def compare(name,a,b,maximum=4,mean=.3):
  a,b=np.asarray(a),np.asarray(b);same=a.shape==b.shape
  delta=np.abs(a.astype(np.float64)-b.astype(np.float64)) if same else np.asarray([1e99]);mx=float(delta.max(initial=0));mae=float(delta.mean()) if delta.size else 0;gate(name,same and np.isfinite(delta).all() and mx<=maximum and mae<=mean,max_abs_error=mx,mean_abs_error=mae,max_bound=maximum,mean_bound=mean,elements=int(a.size))
 gate('real-CLI-status',record['status']=='PASSED' and len(record['calls'])>0)
 for i,c in enumerate(record['calls']):
  log=(d/c['log']).read_text();expected=c['expected_return_code'];gate('CLI-return-code-'+str(i),c['passed'] and c['return_code']==expected);gate('no-false-PASS-'+str(i),'RESULT status=PASS' not in log if expected else ('RESULT status=PASS' in log or 'Usage:' in log or '\nOK\n' in log))
  if c.get('parameters',{}).get('expected_decoded'):gate('exact-output-count',('decoded='+str(c['parameters']['expected_decoded'])) in log and 'instances=2' in log)
 post='/Image-Resize' in source
 for i,item in enumerate(record['outputs']):
  m=item['metadata'];p=local_source(m['source']);v=np.fromfile(d/item['raw'],np.uint8);width,height=m['width'],m['height'];params=item['parameters'];fmt=m['format'];s=m['scale'];rgb=np.asarray(Image.open(p).convert('RGB')) if m['cpu_fallback'] else cpu_rgb_fast(p);rgb=scale_box(rgb,s)
  if params.get('roi'):
   x,y,w,h=params['roi'];rgb=rgb[y:y+h,x:x+w]
  expected_size=params.get('resize',[max(1,rgb.shape[1]//2),max(1,rgb.shape[0]//2)]) if post else [rgb.shape[1],rgb.shape[0]]
  command=record['calls'][int(item['raw'].split('/')[0][4:])]['command'];requested_format=command[command.index('-fmt')+1] if '-fmt' in command else 'rgbi';requested_scale=int(command[command.index('-scale')+1]) if '-scale' in command else 1
  gate('independent-CLI-geometry-and-layout-'+str(i),[width,height]==expected_size and s==requested_scale and fmt==requested_format and bool(m['postprocess'])==post)
  if m['postprocess']:
   pw,ph=m['pre_width'],m['pre_height'];pre=np.fromfile(str(d/item['raw'])+'.pre.bin',np.uint8).reshape(ph,pw,3);compare('independent-preprocess-pixels-'+str(i),pre,rgb);expected=lanczos(pre,width,height)
   if m['watermark']:
    wm=np.fromfile(str(d/item['raw'])+'.watermark.bin',np.uint8).reshape(m['watermark_height'],m['watermark_width'],3);asset=ROOT/'nvJPEG/Image-Resize-WaterMark/NVLogo.jpg';compare('watermark-independent-decode-'+str(i),wm,np.asarray(Image.open(asset).convert('RGB')) if Image.open(asset).info.get('progressive') else cpu_rgb_fast(asset));expected=np.minimum(255,expected.astype(int)+lanczos(wm,width,height).astype(int)*m['alpha']//255).astype(np.uint8)
   compare('full-Lanczos-watermark-'+str(i),v.reshape(height,width,3),expected,1,.05);jpeg_file=(d/item['raw']).parent/p.with_suffix('.jpg').name
   gate('encoded-file-roundtrip-'+str(i),jpeg_file.exists() and Image.open(jpeg_file).size==(width,height))
  elif fmt in ['rgbi','bgri','rgb','bgr']:
   expected=rgb[:,:,::-1] if fmt.startswith('bgr') else rgb
   if fmt in ['rgb','bgr']:expected=expected.transpose(2,0,1)
   compare('full-independent-RGB-'+str(i),v.reshape(expected.shape),expected)
  else:
   planes=[scale_box(a,s) for a in cpu_yuv(p)];ysize=width*height;cw,ch=m['chroma_width'],m['chroma_height']
   if fmt=='nv12':expected=np.concatenate([planes[0].ravel(),np.stack(planes[1:],axis=-1).ravel()])
   elif fmt=='yuy2':
    expected=np.zeros((height,cw,4),np.uint8);expected[:,:,0]=planes[0][:,::2];expected[:,:width//2,2]=planes[0][:,1::2];expected[:,:,1]=planes[1];expected[:,:,3]=planes[2];expected=expected.ravel()
   else:expected=np.concatenate([x.ravel() for x in (planes[:1] if fmt=='y' else planes)])
   compare('full-independent-YUV-'+str(i),v,expected,4,1)
  fallback+=bool(m['cpu_fallback']);gate('output-geometry-'+str(i),width>0 and height>0 and (not params.get('resize') or [width,height]==params['resize']))
 if case=='original-corpus':gate('all-original-inputs',len(record['outputs'])==12)
 if case=='postprocess' and not post:
  bmp=next(d.rglob('*.bmp'));p=ROOT/'tests/fixtures/batch10/444.jpg';compare('BMP-file-full-pixels',np.asarray(Image.open(bmp).convert('RGB')),np.asarray(Image.open(p).convert('RGB')))
 if case=='python-integration' and not post:
  log=(d/'python.log').read_text();gate('original-Python-GPU-integration',re.search(r'Ran 10 tests',log) and '\nOK\n' in log)
 fixture=ROOT/'tests/fixtures/batch10';identity=dict(case=case,fixtures={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(fixture.glob('*.jpg'))},parameters=[c.get('parameters',{}) for c in record['calls']])
 if case in ['original-corpus','batch-multi-instance']:identity['corpus']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'nvJPEG/nvJPEG-Decoder/input_images').glob('*.jpg'))}
 return dict(status='PASSED' if checks and all(x['passed'] for x in checks) else 'FAILED',checks=checks,input_sha256=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest(),output_values={},cpu_fallback_outputs=fallback,oracle='Independent Pillow/libjpeg RGB and libturbojpeg raw YUV; every semantic pixel; independent FP64 Lanczos/watermark and image-file/CLI/original-unittest checks')
