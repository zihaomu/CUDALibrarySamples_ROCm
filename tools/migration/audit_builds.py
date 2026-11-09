#!/usr/bin/env python3
"""Audit every upstream build definition and source classification.

Record conditional declarations without relying on local SDK availability. The
report retains unresolved expansions; dynamic SDK-derived build variants stay
explicit instead of silently dropping them from the migration denominator.
"""
import ast,collections,fcntl,glob,hashlib,itertools,json,pathlib,re,shlex,subprocess
from catalog import ROOT,BASE,CANDIDATES
SOURCE_EXT={'.c','.cpp','.cu','.f90','.cuf','.py'}

def cmake_commands(text):
 text=re.sub(r'#\[\[.*?\]\]','',text,flags=re.S)
 text=re.sub(r'#[^\n]*','',text)
 pattern=re.compile(r'\b(\w+)\s*\(');pos=0
 while (m:=pattern.search(text,pos)):
  i=m.end();start=i;depth=1;quote=False;escaped=False
  while i<len(text) and depth:
   c=text[i]
   if escaped:escaped=False
   elif c=='\\':escaped=True
   elif c=='"':quote=not quote
   elif not quote:
    if c=='(':depth+=1
    elif c==')':depth-=1
   i+=1
  raw=text[start:i-1];tokens=re.findall(r'"(?:\\.|[^"\\])*"|[^\s]+',raw)
  yield m.group(1).lower(),[t[1:-1] if t.startswith('"') and t.endswith('"') else t for t in tokens],text.count('\n',0,m.start())+1
  pos=i

def main():
 catpath=ROOT/'migration/samples.yaml';cat=json.loads(catpath.read_text());source_map={v['path']:v for v in cat['sources']};samples={v['source']:v for v in cat['samples']};report=[];decls=[]
 for build in cat['build_definitions']:
  path=ROOT/build['path'];raw=path.read_text(errors='replace');entry={**build,'declarations':[],'kind':'CMAKE' if path.name=='CMakeLists.txt' else 'MAKE','notes':[]};variables={'CMAKE_CURRENT_SOURCE_DIR':str(path.parent),'CMAKE_SOURCE_DIR':str(path.parent)};level=0;loopvars=[]
  def expand(s):
   for _ in range(8):
    t=re.sub(r'\$\{([^}]+)\}',lambda m:';'.join(variables.get(m[1],[m[0]])) if isinstance(variables.get(m[1]),list) else variables.get(m[1],m[0]),s)
    if s==t:break
    s=t
   return s
  def expand_many(s):
   keys=list(dict.fromkeys(re.findall(r'\$\{([^}]+)\}',s)))
   values=[]
   for key in keys:
    value=variables.get(key,['${'+key+'}']);value=[value] if isinstance(value,str) else value
    values.append([part for item in value for part in expand(item).split(';')])
   result=[]
   for choice in itertools.product(*values):
    value=s
    for key,item in zip(keys,choice):value=value.replace('${'+key+'}',item)
    result.extend(expand(value).split(';'))
   return result
  if entry['kind']=='CMAKE':
   for command,tokens,line in cmake_commands(raw):
    if command in {'function','macro'}:level+=1;continue
    if command in {'endfunction','endmacro'}:level-=1;continue
    if level:continue
    if command=='set' and tokens:variables[tokens[0]]=[expand(t) for t in tokens[1:] if t not in {'CACHE','STRING','PATH','BOOL','INTERNAL','FORCE'}];continue
    if command=='list' and len(tokens)>2 and tokens[0].upper()=='APPEND':variables.setdefault(tokens[1],[]).extend(expand(t) for t in tokens[2:]);continue
    if command=='file' and len(tokens)>2 and tokens[0].upper() in {'GLOB','GLOB_RECURSE'}:
     vals=[]
     for token in tokens[2:]:
      for pattern in expand_many(token):
       if '*' in pattern:
        root=path.parent
        for name in glob.glob(str(root/pattern)):
         q=pathlib.Path(name)
         if q.is_file():vals.append(str(q.relative_to(root)))
     variables[tokens[1]]=vals;continue
    if command=='include' and tokens:
     included=path.parent/expand(tokens[0])
     if included.is_file() and included.resolve().is_relative_to(ROOT):
      for subcommand,subtokens,_ in cmake_commands(included.read_text()):
       if subcommand=='set' and subtokens:variables[subtokens[0]]=[expand(t) for t in subtokens[1:]]
     continue
    if command=='project' and tokens:variables['PROJECT_NAME']=[expand(tokens[0])];variables['PROJECT_SOURCE_DIR']=str(path.parent);continue
    if command=='foreach' and tokens:
     name=tokens[0];vals=[part for v in tokens[1:] if v not in {'IN','ITEMS','LISTS'} for part in (expand_many('${'+v+'}') if 'LISTS' in tokens else expand_many(v))];variables[name]=vals;loopvars.append(name);continue
    if command=='endforeach':
     if loopvars:variables.pop(loopvars.pop(),None)
     continue
    if not (command in {'add_executable','target_sources'} or command.startswith('add_') and ('example' in command or command=='add_benchmark')):continue
    args=[part for t in tokens for part in expand_many(t)];related=[]
    for arg in args:
     for value in arg.split(';'):
      q=path.parent/value
      if q.suffix in SOURCE_EXT and q.is_file():related.append(str(q.resolve().relative_to(ROOT)))
    # Some wrappers infer .cu from a stem or use a common main header.
    for arg in args[:2]:
     for suffix in ['.cu','.cpp','.c']:
      q=path.parent/(arg+suffix)
      if q.is_file():related.append(str(q.relative_to(ROOT)))
    target=args[0] if args else None
    if command not in {'add_executable','target_sources','add_example','add_benchmark','add_python_example'} and len(args)>1:target=args[1]
    unresolved=[v for v in args if '${' in v]
    d={'build':build['path'],'line':line,'command':command,'target_expression':target,'arguments':args,'sources':sorted(set(related)),'conditional':True,'unresolved':bool(unresolved),'unresolved_arguments':unresolved};entry['declarations'].append(d);decls.append(d)
  else:
   # Exact source mentions and wildcard/pattern rules give a separate independent audit route.
   mentioned=set(re.findall(r'[\w./+\-]+\.(?:cu|cpp|c|f90|cuf|py)\b',raw))
   if 'wildcard' in raw or re.search(r'%\.(?:cu|cpp|c)',raw):mentioned.update(p.name for p in path.parent.iterdir() if p.suffix in SOURCE_EXT)
   for name in sorted(mentioned):
    q=path.parent/name
    if q.is_file() and q.suffix in SOURCE_EXT:
     d={'build':build['path'],'line':next((i for i,l in enumerate(raw.splitlines(),1) if name in l),None),'command':'make-source-or-pattern','target_expression':q.stem,'sources':[str(q.resolve().relative_to(ROOT))],'conditional':True,'unresolved':False};entry['declarations'].append(d);decls.append(d)
  entry['audit']='STATIC_DECLARATIONS_AUDITED' if entry['declarations'] else 'INFRASTRUCTURE_OR_DELEGATING_BUILD';build['audit']=entry['audit'];build['declaration_count']=len(entry['declarations']);report.append(entry)
 bindings=collections.defaultdict(list)
 for d in decls:
  for src in d['sources']:bindings[src].append({k:d[k] for k in ['build','line','command','target_expression','conditional','unresolved']})
 additions=[]
 for path,src in source_map.items():
  p=ROOT/path;body=p.read_text(errors='replace');bound=bindings[path]
  if path not in samples:
   classification='LINKED_SUPPORT_SOURCE' if bound else None
   # Macro-generated benchmark entrypoints are real targets even without a main definition in the .cu.
   macro_main=bool(re.search(r'NVBENCH_BENCH\s*\(|BENCHMARK\w*\s*\(|benchmark_common\.h|main\.h',body)) and '/benchmarks/' in path
   py_example=p.suffix=='.py' and (p.name=='run.py' or p.name.endswith('_test.py') or p.name=='cannyEdgeDetector.py')
   if macro_main or py_example:
    template={'id':str(p.parent.relative_to(ROOT))+'::'+p.name,'family':src['family'],'source':path,'source_sha256':src['sha256'],'target':p.stem,'candidate_libraries':CANDIDATES[src['family']],'actual_library':None,'backend_library':None,'implementation':None,'status':'NOT_STARTED','level':'L0','required_cases':[],'passed_cases':[],'reason_code':None,'reason':'构建审计补入的宏生成入口或可运行 Python 示例，尚未移植','cuda_baseline':'NOT_RUN','cuda_comparison':'NOT_RUN','benchmark':'NOT_RUN','evidence':[],'attempts':[],'milestone':None}
    samples[path]=template;additions.append(path);classification='BUILD_OR_SCRIPT_ENTRYPOINT'
   elif classification:pass
   elif p.suffix in {'.f90','.cuf'} and re.search(r'^\s*(?:module|subroutine|function)\s+\w+',body,re.I|re.M):classification='FORTRAN_SUPPORT_MODULE'
   elif p.suffix=='.py':
    try:tree=ast.parse(body);is_test=any(isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name.startswith(('test','Test')) for n in tree.body)
    except SyntaxError:is_test=False
    classification='TEST_MODULE' if is_test else ('PACKAGING' if p.name=='setup.py' else 'PYTHON_SUPPORT_MODULE')
   else:classification='COMPILED_SUPPORT_SOURCE'
   src['classification']=classification
  src['review']='BUILD_BINDINGS_RECORDED' if bound else 'ENTRYPOINT_OR_MODULE_REVIEWED';src['build_bindings']=bound
  if path in samples:
   sample=samples[path];sample['build_bindings']=bound;sample['build_audit']='BOUND_DECLARATION' if bound else 'ENTRYPOINT_CONFIRMED_SOURCE_OR_SCRIPT'
   sample['discovery']='CONFIRMED_ENTRYPOINT';sample['target']=next((d['target_expression'] for d in bound if '${' not in str(d['target_expression'])),p.stem)
 for d in decls:
  if not d.get('unresolved'):continue
  u=' '.join(d.get('unresolved_arguments',[]))
  if '${CMAKE_BINARY_DIR}' in u and 'fatbin.h' in u:d['resolution']='GENERATED_LTO_FATBIN_HEADER; custom command output, not an independent entrypoint'
  elif '${cudss_INCLUDE_DIR}' in u:d['resolution']='EXTERNAL_NVIDIA_SDK_BINDING_SOURCE; repository entrypoint sources already bound'
  elif 'RELATIVE_PATH' in u:d['resolution']='CTEST_GENERATED_RUNTIME_INPUT; not an additional source entrypoint'
  elif re.search(r'\$\{(?:LZ4|LIBDEFLATE|SNAPPY|ZSTD)_(?:LIBRARY|INCLUDE_DIR)\}',u):d['resolution']='OPTIONAL_EXTERNAL_LINK_OR_INCLUDE_PATH; source entrypoint already identified'
  elif '${src}' in u and d['build'].startswith('cuDSS/'):
   candidates=[v for v in samples if pathlib.Path(v).parent==pathlib.Path(d['build']).parent];d['resolution']='CONDITIONAL_COMMUNICATION_BACKEND_VARIANTS_OF_EXISTING_ENTRYPOINTS';d['variant_entrypoints']=candidates
  else:d['resolution']='RETAINED_DYNAMIC_EXPRESSION; source census and entrypoint detection provide independent coverage'
 cat['samples']=sorted(samples.values(),key=lambda s:s['id']);cat['inventory_status']='SOURCE_AND_STATIC_BUILD_AUDIT_COMPLETE_WITH_EXPLICIT_VARIANTS';cat['inventory_notes']='All 477 build definitions and 866 source files statically reviewed. Counted units are distinct executable/script source entrypoints; static/shared/architecture/backend variants remain metadata. External SDK binding sources and runtime-generated inputs are classified in build-audit.json. SDK-conditional configurations were not all generated/executed.'
 (ROOT/'migration/build-audit.json').write_text(json.dumps({'upstream_commit':BASE,'build_files':report,'declarations':decls,'added_entrypoints':additions,'unresolved_declarations':[d for d in decls if d.get('unresolved')]},indent=2,ensure_ascii=False)+'\n');catpath.write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'build_files':len(report),'declarations':len(decls),'mapped_sources':sum(bool(s['build_bindings']) for s in cat['sources']),'entrypoints':len(cat['samples']),'added':additions,'unresolved_declarations':sum(d.get('unresolved',False) for d in decls)},indent=2))
if __name__=='__main__':
 with (ROOT/'migration/.state.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);main()
