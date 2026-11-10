"""Independent SciPy/OpenCV-style mathematical image oracles, complete semantic pixels."""
import hashlib,json,pathlib,collections
from validate_blas import np
from scipy import ndimage,signal,sparse
from scipy.sparse.csgraph import breadth_first_order
mask_cache={}
from batches12_15_spec import kind
from catalog import ROOT

def validate(source,case,d):
 k=kind(source);checks=[];inputs={};trace=np.fromfile(d/'trace.bin',np.int32);count=len(trace)//3
 def gate(n,v,**kw):checks.append(dict(check=n,passed=bool(v),**kw))
 def near(n,a,b,tol=2e-5):
  delta=np.abs(a.astype(np.float64)-b);gate(n,a.shape==b.shape and np.isfinite(a).all() and np.all(delta<=tol*np.maximum(1,np.abs(b))),max_abs=float(delta.max(initial=0)))
 def read(i,name,dtype=np.uint8):return np.fromfile(d/f'i{i}_{name}.bin',dtype)
 expected_count=(2 if k=='distance' else 5 if k=='flood' else 1) if case in ['original','repeat'] else 1
 gate('registered-image-count-no-empty-work',trace.size%3==0 and count==expected_count)
 for image in range(count):
  cfg=read(image,'params',np.int32).tolist();W,H,C,stride,rx,ry,w,h,low,high,connect,sx,sy,mode,tw,th,tx,ty=cfg;raw=read(image,'input');img=raw.reshape(H,stride)[:,:W*C].reshape(H,W,C)[ry:ry+h,rx:rx+w];inputs[str(image)]=dict(params=cfg,input=hashlib.sha256(raw.tobytes()).hexdigest());repeat=3 if case=='repeat' else 1;gate('actual-kernel-and-repeat-'+str(image),trace[3*image]>=2*repeat and trace[3*image+2]==repeat)
  if k=='distance':
   sites=img[:,:,0]==0;out=read(image,'output',np.float32).reshape(h,w);trunc=read(image,'truncated',np.uint16).reshape(h,w);vor=read(image,'voronoi',np.int16).reshape(h,w,2)
   if sites.any():
    expected=ndimage.distance_transform_edt(~sites);near('all-exact-Euclidean-distances-'+str(image),out,expected,2e-6);gate('integer-truncation-'+str(image),np.array_equal(trunc,np.floor(expected).astype(np.uint16)));yy,xx=np.indices((h,w));x=xx-vor[:,:,0];y=yy-vor[:,:,1];gate('Voronoi-valid-nearest-site-'+str(image),np.all((x>=0)&(x<w)&(y>=0)&(y<h)) and np.all(sites[y,x]));yy,xx=np.indices((h,w));near('Voronoi-distance-reconstruction-'+str(image),np.sqrt((xx-x)**2+(yy-y)**2),expected,1e-12)
   else:gate('empty-site-declared-behavior',np.isposinf(out).all() and np.all(trunc==65535) and np.all(vor==-32768))
  elif k=='ncc':
   template=read(image,'template').reshape(th,tw);inputs[str(image)]['template']=hashlib.sha256(template.tobytes()).hexdigest();a=img[:,:,0].astype(np.float64);b=template.astype(np.float64);n=tw*th;centered=b-b.mean();numerator=signal.fftconvolve(a,centered[::-1,::-1],mode='valid');sums=signal.convolve2d(a,np.ones((th,tw)),mode='valid') if w*h<10000 else None
   def integral_sum(v):
    s=np.pad(v,((1,0),(1,0))).cumsum(0).cumsum(1);return s[th:,tw:]-s[:-th,tw:]-s[th:,:-tw]+s[:-th,:-tw]
   sums=integral_sum(a);variance=np.maximum(0,integral_sum(a*a)-sums*sums/n);denominator=np.sqrt(variance*np.sum(centered*centered));expected=np.divide(numerator,denominator,out=np.zeros_like(numerator),where=denominator>0);out=read(image,'output',np.float32).reshape(h-th+1,w-tw+1);near('every-NCC-score-'+str(image),out,expected,3e-6);at=int(read(image,'best',np.int32)[0]);gate('GPU-global-argmax-'+str(image),0<=at<out.size and out.ravel()[at]>=float(expected.max())-3e-6)
   if case in ['original','repeat']:gate('original-degraded-template-location-'+str(image),abs(at%(w-tw+1)-tx)<=1 and abs(at//(w-tw+1)-ty)<=1)
  else:
   if k=='canny':
    a=img.astype(np.int32);sxg=ndimage.correlate(a,np.asarray([[-1,0,1],[-2,0,2],[-1,0,1]])[:,:,None],mode='nearest');syg=ndimage.correlate(a,np.asarray([[-1,-2,-1],[0,0,0],[1,2,1]])[:,:,None],mode='nearest');best=np.argmax(sxg*sxg+syg*syg,axis=2);dx=np.take_along_axis(sxg,best[:,:,None],axis=2)[:,:,0];dy=np.take_along_axis(syg,best[:,:,None],axis=2)[:,:,0];gate('all-channel-Sobel-x-'+str(image),np.array_equal(read(image,'gx',np.int32).reshape(h,w),dx));gate('all-channel-Sobel-y-'+str(image),np.array_equal(read(image,'gy',np.int32).reshape(h,w),dy));mag=np.sqrt((dx*dx+dy*dy).astype(np.float32));ax=np.abs(dx);ay=np.abs(dy);vertical=ay.astype(np.float32)>np.float32(2.41421356237)*ax;diagonal=(~vertical)&(ay.astype(np.float32)>np.float32(.41421356237)*ax);ox=np.where(vertical,0,1);oy=np.where(vertical,1,np.where(diagonal,np.where((dx<0)==(dy<0),1,-1),0));yy,xx=np.indices((h,w));forward=mag[np.clip(yy+oy,0,h-1),np.clip(xx+ox,0,w-1)];back=mag[np.clip(yy-oy,0,h-1),np.clip(xx-ox,0,w-1)];keep=(mag>=forward)&(mag>back);allowed=keep&(mag>=low);initial=keep&(mag>=high);visited=ndimage.binary_propagation(initial,mask=allowed,structure=ndimage.generate_binary_structure(2,1 if connect==4 else 2))
   else:
    if mode==0:allowed=np.all(img==img[sy,sx],axis=2)
    elif mode>=3:allowed=np.all((img>=[24,24,62])&(img<=[240,248,251]),axis=2)
    else:allowed=np.ones((h,w),bool)
    key=(hashlib.sha256(img.tobytes()).hexdigest(),w,h,connect,sx,sy,1 if mode in [1,2] else mode)
    if key in mask_cache:visited=mask_cache[key]
    elif mode not in [1,2]:
     seed=np.zeros((h,w),bool);seed[sy,sx]=allowed[sy,sx];visited=ndimage.binary_propagation(seed,mask=allowed,structure=ndimage.generate_binary_structure(2,1 if connect==4 else 2));mask_cache[key]=visited
    else:
     ids=np.arange(w*h).reshape(h,w);edges_from=[];edges_to=[]
     for j in [-1,0,1]:
      for i in [-1,0,1]:
       if not(i or j) or (connect==4 and i and j):continue
       y0,y1=max(0,-j),min(h,h-j);x0,x1=max(0,-i),min(w,w-i);a=img[y0:y1,x0:x1].astype(np.int16);b=img[y0+j:y1+j,x0+i:x1+i].astype(np.int16);good=np.all((b-a>=-52)&(b-a<=3),axis=2);edges_from.append(ids[y0:y1,x0:x1][good]);edges_to.append(ids[y0+j:y1+j,x0+i:x1+i][good])
     fr=np.concatenate(edges_from);to=np.concatenate(edges_to);graph=sparse.csr_matrix((np.ones(len(fr),np.uint8),(fr,to)),shape=(w*h,w*h));reachable=breadth_first_order(graph,sy*w+sx,directed=True,return_predecessors=False);visited=np.zeros(w*h,bool);visited[reachable]=True;visited=visited.reshape(h,w);mask_cache[key]=visited
   gate('eligibility-all-pixels-'+str(image),np.array_equal(read(image,'eligible').reshape(h,w),allowed));gate('full-connected-mask-'+str(image),np.array_equal(read(image,'mask').reshape(h,w),visited));boundary=visited&~ndimage.binary_erosion(visited,structure=np.ones((3,3),bool),border_value=0);ys,xs=np.where(visited);stats=[int(visited.sum()),int(xs.min()) if xs.size else w,int(ys.min()) if ys.size else h,int(xs.max()) if xs.size else -1,int(ys.max()) if ys.size else -1,int(boundary.sum())];gate('GPU-area-bbox-boundary-query-'+str(image),np.array_equal(read(image,'stats',np.int32),stats));channels=1 if k=='canny' else 3;out=read(image,'output').reshape(h,w*channels+5);gate('padded-output-row-canaries-'+str(image),np.all(out[:,w*channels:]==173));expected=(visited.astype(np.uint8)*255)[:,:,None] if k=='canny' else img.copy()
   if k=='flood':
    color=[0,255,0] if mode==3 else [128,64,0] if mode==4 else [255,0,0];expected[visited]=color
    if mode in [2,4]:expected[boundary]=[128,0,255]
   gate('every-output-pixel-'+str(image),np.array_equal(out[:,:w*channels].reshape(h,w,channels),expected));gate('real-convergence-check-'+str(image),trace[3*image+1]>=repeat)
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,input_sha256=hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest(),output_values={},oracle='SciPy Euclidean distance/nearest sites, FP64 FFT-NCC/integral variance, independent Sobel/NMS and queue/ndimage connectivity; full pixels and GPU region statistics/padding')
