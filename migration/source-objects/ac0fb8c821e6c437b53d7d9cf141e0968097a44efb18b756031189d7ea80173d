#!/usr/bin/env python3
"""Independent NumPy CPU oracle for the original fixed-input BLAS examples.
Unsupported parsing/semantics stay pending; no success from process exit alone.
"""
import ast,collections,hashlib,json,math,pathlib,re,sys
from catalog import ROOT
sys.path.insert(0,str(ROOT/'build/python-reference'))
import numpy as np

ENUMS={'CUBLAS_OP_N':'N','CUBLAS_OP_T':'T','CUBLAS_OP_C':'C','CUBLAS_FILL_MODE_UPPER':'U','CUBLAS_FILL_MODE_LOWER':'L','CUBLAS_SIDE_LEFT':'L','CUBLAS_SIDE_RIGHT':'R','CUBLAS_DIAG_UNIT':'U','CUBLAS_DIAG_NON_UNIT':'N'}
def expression(s,env):
 s=s.strip().replace('std::','');s=re.sub(r'(?<=\d)[fFuUlL]+\b','',s);s=re.sub(r'(\w+)\.size\(\)',r'len(\1)',s);s=re.sub(r'make_cu(?:Double|Float)?Complex','complex',s);s=s.replace('{','[').replace('}',']')
 tree=ast.parse(s,mode='eval')
 for n in ast.walk(tree):
  if not isinstance(n,(ast.Expression,ast.Constant,ast.Name,ast.Load,ast.List,ast.Tuple,ast.UnaryOp,ast.USub,ast.UAdd,ast.BinOp,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Mod,ast.Call)):raise ValueError('unsupported expression '+s)
  if isinstance(n,ast.Call) and (not isinstance(n.func,ast.Name) or n.func.id not in {'complex','len','int','float'}):raise ValueError('unsupported call '+s)
 return eval(compile(tree,'<C++ literal>','eval'),{'__builtins__':{},'complex':complex,'len':len,'int':int,'float':float},env)

def literals(source):
 s=re.sub(r'/\*.*?\*/|//[^\n]*','',source,flags=re.S);s=s[s.index('int main'):];env=dict(ENUMS);vectors={};events=[]
 ctype=re.search(r'using\s+data_type\s*=\s*([^;]+);',source);complex_type=bool(ctype and 'Complex' in ctype[1])
 for m in re.finditer(r'(?:const\s+)?std::vector<([^>]+)>\s+(\w+)\s*(?:=\s*(\{.*?\})|\((.*?)\))\s*;',s,re.S):
  if '*' not in m[1]:events.append((m.start(),'vector',m[2],m[3],m[4],m[1]))
 for m in re.finditer(r'(?:const\s+)?(?:int(?:64_t)?|long long int|data_type|double|float|cublas(?:Operation|FillMode|SideMode|DiagType)_t)\s+(\w+)\s*=\s*([^;]+);',s):events.append((m.start(),'scalar',m[1],m[2],None,None))
 pending=sorted(events)
 for _ in range(8):
  rest=[]
  for item in pending:
   _,kind,name,init,args,typ=item
   try:
    if kind=='scalar':
     value=expression(init,env)
     if complex_type and isinstance(value,list) and len(value)==2:value=complex(*value)
     env[name]=value
    else:
     if init is not None:
      value=expression(init,env)
      if complex_type and 'int' not in typ:value=[complex(*v) if isinstance(v,list) and len(v)==2 else v for v in value]
      value=np.asarray(value,dtype=complex if complex_type and 'int' not in typ else float)
     else:
      arglist=args.split(',');count=int(expression(arglist[0],env));fill=expression(arglist[1],env) if len(arglist)>1 else 0;value=np.full(count,fill,dtype=complex if complex_type and 'int' not in typ else float)
     vectors[name]=value;env[name]=value
   except (ValueError,NameError,SyntaxError,TypeError,IndexError):rest.append(item)
  if len(rest)==len(pending):break
  pending=rest
 if 'AP' in vectors:vectors['A']=vectors['AP'].copy()
 return env,vectors

def observed(path):
 result={}
 for line in path.read_text(errors='replace').splitlines():
  if line.startswith('{"observe"'):
   x=json.loads(line);v=x['values'];result[x['observe']]=np.array([complex(*z) if isinstance(z,list) else z for z in v])
 return result

def reference(source,env,v):
 e=env;out={};get=lambda key,default=None:e.get(key,default)
 op=lambda a,t:a if t=='N' else a.T if t=='T' else a.conj().T
 def mat(name,rows,cols,ld):return v[name][:ld*cols].reshape((ld,cols),order='F')[:rows,:].copy()
 def tri(a,u='U',unit=False):
  a=np.triu(a) if u=='U' else np.tril(a)
  if unit:np.fill_diagonal(a,1)
  return a
 def sym(a,u='U',hermitian=False):
  t=np.triu(a) if u=='U' else np.tril(a);z=t+(t.conj().T if hermitian else t.T);np.fill_diagonal(z,np.diag(t).real if hermitian else np.diag(t));return z
 def packed(a,n,u='U'):
  out=np.zeros((n,n),dtype=a.dtype);q=0
  for j in range(n):
   for i in (range(j+1) if u=='U' else range(j,n)):out[i,j]=a[q];q+=1
  return out
 def pack(a,u='U'):return np.asarray([a[i,j] for j in range(a.shape[1]) for i in (range(j+1) if u=='U' else range(j,a.shape[0]))])
 def store(name,a,ld=None):
  dst=v[name].copy();ld=int(ld or a.shape[0]);flat=dst.reshape((ld,-1),order='F');flat[:a.shape[0],:a.shape[1]]=a;out[name]=flat.flatten(order='F')
 calls=re.findall(r'cublas([SDCZ]?(?:[a-zA-Z0-9]+))\s*\(',source)
 calls=[c for c in calls if c not in {'Create','Destroy','SetStream','SetPointerMode','SetMathMode','GetMathMode'}]
 name=next(iter(calls),None)
 if name is None:raise ValueError('no supported BLAS operation')
 extensions={'AxpyEx','DotEx','DotcEx','Nrm2Ex','RotEx','ScalEx','GemmEx','GemmBatchedEx','GemmStridedBatchedEx','GemmGroupedBatchedEx'}
 operation=(name if name in extensions else re.sub(r'^[SDCZ]','',name)).lower();
 if operation in {'axpyex','dotex','dotcex','nrm2ex','rotex','scalex'}:operation=operation[:-2];operation=re.sub(r'^i[sdcz]','i',operation)
 alpha=get('alpha',1);beta=get('beta',0);u=get('uplo','U');ta=get('transa','N');tb=get('transb','N');side=get('side','L');unit=get('diag','N')=='U'
 n=int(get('n',len(v.get('A',[]))));m=int(get('m',n));k=int(get('k',n));lda=int(get('lda',m));ldb=int(get('ldb',k));ldc=int(get('ldc',m));ix=int(get('incx',1));iy=int(get('incy',1));xname='x' if 'x' in v else 'A';yname='y' if 'y' in v else 'B'
 if operation in {'amax','amin','iamax','iamin','asum','axpy','copy','dot','dotc','nrm2','rot','scal','swap'} or operation.startswith('i'):
  x=v[xname][::ix];y=v.get(yname,np.zeros(len(x)))[::iy];n=min(len(x),int(get('n',len(x))));x=x[:n];y=y[:n]
  if operation.endswith('amax'):out['result']=np.array([np.argmax(abs(x.real)+abs(x.imag) if np.iscomplexobj(x) else abs(x))+1])
  elif operation.endswith('amin'):out['result']=np.array([np.argmin(abs(x.real)+abs(x.imag) if np.iscomplexobj(x) else abs(x))+1])
  elif operation=='asum':out['result']=np.array([np.sum(abs(x.real)+abs(x.imag) if np.iscomplexobj(x) else abs(x))])
  elif operation=='nrm2':out['result']=np.array([np.linalg.norm(x)])
  elif operation in {'dot','dotc'}:out['result']=np.array([np.vdot(x,y) if operation=='dotc' else np.dot(x,y)])
  elif operation in {'axpy','copy'}:
   z=v[yname].copy();z[::iy][:n]=alpha*x+y if operation=='axpy' else x;out[yname]=z
  elif operation=='scal':z=v[xname].copy();z[::ix][:n]=alpha*x;out[xname]=z
  elif operation=='swap':out[xname]=v[yname].copy();out[yname]=v[xname].copy()
  elif operation=='rot':
   c=get('c');ss=get('s');a=v[xname].copy();b=v[yname].copy();a[::ix][:n]=c*x+ss*y;b[::iy][:n]=c*y-np.conj(ss)*x;out[xname]=a;out[yname]=b
  else:raise ValueError('unsupported vector '+operation)
 elif operation in {'gemm','gemmex','gemmstridedbatched','gemmstridedbatchedex','gemmbatched','gemmbatchedex','gemmgroupedbatched','gemmgroupedbatchedex','gemm3m'}:
  batches=int(get('batch_count',get('batchCount',1)));sa=int(get('strideA',lda*(m if ta!='N' else k)));sb=int(get('strideB',ldb*(k if tb!='N' else n)));sc=int(get('strideC',ldc*n));z=v['C'].copy()
  for batch in range(batches):
   a=v['A'][batch*sa:batch*sa+lda*(m if ta!='N' else k)].reshape((lda,-1),order='F')[:(k if ta!='N' else m),:];b=v['B'][batch*sb:batch*sb+ldb*(k if tb!='N' else n)].reshape((ldb,-1),order='F')[:(n if tb!='N' else k),:];c=z[batch*sc:batch*sc+ldc*n].reshape((ldc,n),order='F');c[:m,:]=alpha*(op(a,ta)@op(b,tb))+beta*c[:m,:]
  out['C']=z
 elif operation=='gemv':a=mat('A',m,n,lda);z=v['y'].copy();z[::iy][:op(a,ta).shape[0]]=alpha*op(a,ta)@v['x'][::ix][:op(a,ta).shape[1]]+beta*z[::iy][:op(a,ta).shape[0]];out['y']=z
 elif operation in {'symm','hemm'}:
  dim=m if side=='L' else n;a=sym(mat('A',dim,dim,lda),u,operation=='hemm');b=mat('B',m,n,ldb);c=mat('C',m,n,ldc);store('C',alpha*(a@b if side=='L' else b@a)+beta*c,ldc)
 elif operation in {'syrk','herk','syrkx','her2k','syr2k','herkx'}:
  a=op(mat('A',n if ta=='N' else k,k if ta=='N' else n,lda),ta);c=mat('C',n,n,ldc);herm=operation.startswith('her');ah=a.conj().T if herm else a.T
  if operation in {'syrk','herk'}:calc=alpha*a@ah+beta*c
  else:
   b=op(mat('B',n if ta=='N' else k,k if ta=='N' else n,ldb),ta);bh=b.conj().T if herm else b.T;calc=alpha*a@bh+beta*c
   if '2' in operation:calc+=(np.conj(alpha) if herm else alpha)*b@ah
  ids=np.triu_indices(n) if u=='U' else np.tril_indices(n);c[ids]=calc[ids]
  if herm:np.fill_diagonal(c,np.diag(c).real)
  store('C',c,ldc)
 elif operation in {'trmm','trsm'}:
  dim=m if side=='L' else n;a=op(tri(mat('A',dim,dim,lda),u,unit),ta);b=mat('B',m,n,ldb)
  if operation=='trsm':calc=np.linalg.solve(a,alpha*b) if side=='L' else np.linalg.solve(a.T,(alpha*b).T).T;store('B',calc,ldb)
  else:store('C',alpha*(a@b if side=='L' else b@a),ldc)
 elif operation in {'symv','hemv','spmv','hpmv','trmv','trsv','tpmv','tpsv','sbmv','hbmv','tbmv','tbsv','gbmv'}:
  packed_mode=operation in {'spmv','hpmv','tpmv','tpsv'};a=packed(v['A'],n,u) if packed_mode else (np.empty((n,n)) if operation in {'sbmv','hbmv','tbmv','tbsv','gbmv'} else mat('A',n,n,lda))
  if operation in {'sbmv','hbmv','tbmv','tbsv','gbmv'}:
   cols=n;rows=m if operation=='gbmv' else n;a=np.zeros((rows,cols),dtype=v['A'].dtype);ab=v['A'].reshape((lda,cols),order='F')
   for j in range(cols):
    for i in range(rows):
     slot=int(get('ku',k))+i-j if operation=='gbmv' or u=='U' else i-j
     lo=int(get('kl',k)) if operation=='gbmv' else k
     if 0<=slot<lda and ((-int(get('ku',k))<=i-j<=lo) if operation=='gbmv' else ((i<=j and j-i<=k) if u=='U' else (i>=j and i-j<=k))):a[i,j]=ab[slot,j]
  if operation in {'symv','hemv','spmv','hpmv','sbmv','hbmv'}:a=sym(a,u,operation.startswith('h'))
  elif operation!='gbmv':a=tri(a,u,unit)
  a=op(a,ta);x=v['x'][::ix][:a.shape[1]]
  if operation in {'trsv','tpsv','tbsv'}:z=v['x'].copy();z[::ix][:n]=np.linalg.solve(a,x);out['x']=z
  elif operation in {'trmv','tpmv','tbmv'}:z=v['x'].copy();z[::ix][:n]=a@x;out['x']=z
  else:z=v['y'].copy();z[::iy][:a.shape[0]]=alpha*a@x+beta*z[::iy][:a.shape[0]];out['y']=z
 elif operation in {'ger','syr','syr2','her','her2','spr','spr2','hpr','hpr2'}:
  packed_mode=operation.startswith(('spr','hpr'));a=packed(v['A'],n,u) if packed_mode else mat('A',m if operation=='ger' else n,n,lda);x=v['x'][::ix][:a.shape[0]];y=v.get('y',v['x'])[::iy][:a.shape[1]];herm=operation.startswith(('her','hpr'));xx=np.conj(x) if herm else x;yy=np.conj(y) if herm else y
  calc=a+alpha*np.outer(x,yy if operation in {'ger','syr2','her2','spr2','hpr2'} else xx)
  if operation.endswith('2'):calc+=(np.conj(alpha) if herm else alpha)*np.outer(y,xx)
  if operation=='ger':store('A',calc,lda)
  else:
   ids=np.triu_indices(n) if u=='U' else np.tril_indices(n);a[ids]=calc[ids]
   if herm:np.fill_diagonal(a,np.diag(a).real)
   if packed_mode:out['AP' if 'AP' in v else 'A']=pack(a,u)
   else:store('A',a,lda)
 elif operation=='geam':a=op(mat('A',m if ta=='N' else n,n if ta=='N' else m,lda),ta);b=op(mat('B',m if tb=='N' else n,n if tb=='N' else m,ldb),tb);store('C',alpha*a+beta*b,ldc)
 elif operation=='dgmm':a=mat('A',m,n,lda);d=v['x'][::ix];store('C',(d[:m,None]*a if side=='L' else a*d[None,:n]),ldc)
 else:raise ValueError('no CPU reference for '+operation)
 return operation,out

def main():
 catpath=ROOT/'migration/samples.yaml';cat=json.loads(catpath.read_text());results=[]
 for sample in cat['samples']:
  if sample['family']!='cuBLAS' or not sample.get('original_port'):continue
  a=sample['original_port'];result={'id':sample['id'],'evidence':a['evidence'],'status':'PENDING'}
  if a['return_code']!=0:result['reason']='build/run pending';results.append(result);continue
  try:
   source=(ROOT/sample['source']).read_text();env,v=literals(source);obs=observed(ROOT/a['evidence']/'run.log');operation,expected=reference(source,env,v)
   if not expected:raise ValueError('no expected result buffers')
   checks=[]
   for name,ref in expected.items():
    if name not in obs:raise ValueError('result not observed: '+name)
    actual=obs[name];ref=np.asarray(ref).reshape(-1)
    if actual.shape!=ref.shape:raise ValueError('result shape mismatch '+name)
    atol=1e-5 if 'cuComplex' in source or 'using data_type = float' in source else 1e-10;passed=bool(np.all(np.isfinite(actual)) and np.allclose(actual,ref,atol=atol,rtol=atol));checks.append({'buffer':name,'passed':passed,'max_abs_error':float(np.max(abs(actual-ref))), 'atol':atol,'rtol':atol})
   result.update(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',operation=operation,checks=checks,oracle='NumPy CPU mathematical reference; original fixed literals independently parsed',source_sha256=sample['source_sha256'])
  except Exception as e:result['reason']=str(e)
  results.append(result)
 (ROOT/'migration/reports/blas-original-cpu.json').write_text(json.dumps(results,indent=2)+'\n');print(collections.Counter(r['status'] for r in results))
if __name__=='__main__':main()
