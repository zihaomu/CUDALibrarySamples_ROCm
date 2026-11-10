#!/usr/bin/env python3
"""Carry immutable qualifications forward only for unchanged numerical closures."""
import ast,json,sys,functools,subprocess
from pathlib import Path
from experiment import ROOT,digest,write,OUTCOMES
from audit import check as _check
check=functools.lru_cache(maxsize=None)(_check)
AGGREGATES={
 'sparse-binding':('rewrite-R5-qualification.json','qualified_profiles','bf07dfdf501faf57d882fea468246b51c29cc8b9'),
 'sparse24':('rewrite-R7-qualification.json','qualifications','2320f362cbce73706c5c9819144c9b2209b461dc'),
 'sparse24_advanced':('rewrite-R7-qualification.json','qualifications','2320f362cbce73706c5c9819144c9b2209b461dc')}
# Exactly reviewed logging/build-provenance changes, never a numerical-code or
# oracle exemption. Both old and new contents are content addressed.
METADATA_CHANGES={
 ('tools/moat/experiment.py','50af7dcd42d2ca2392cb05f4a65a9df7f8ab33622c0a9046a482531ad6f3c134','cadfbf5ce11a79ac3bb793e7956f360ac11d0dc6006c281a69f5d3f4f053ff05'):'Add live-container/PID recovery identity and terminal-outcome guard; command argv and numerical execution unchanged',
 ('tools/moat/build_extensions.py','e3d4079e2db9492be3bbf7099b936bdc750d1098c82d1c3d83924e1fcb3fa78d','b29b4076981e73b029ab4b3d94b397790dd922393890233704109b7a1cddf82e'):'Seal compiled-dependencies/build-result and reject source drift; compiler argv unchanged'}

@functools.lru_cache(maxsize=None)
def published(path,commit):
    return subprocess.check_output(['git','show',commit+':'+str(path)],cwd=ROOT)

@functools.lru_cache(maxsize=None)
def publication(directory):
    path=str(directory.relative_to(ROOT)/'sealed.json')
    commits=subprocess.check_output(['git','log','--reverse','--diff-filter=A','--format=%H','--',path],cwd=ROOT,text=True).splitlines()
    if not commits:raise ValueError('Qualification has not been published in Git')
    return commits[0]

def anchored_seal(directory,commit,qualification=False):
    path=directory.relative_to(ROOT)/'sealed.json'
    if (directory/'sealed.json').read_bytes()!=published(path,commit):return False
    seal=json.loads((directory/'sealed.json').read_text())['files']
    required={'manifest.json','source.json','validation.json'}|({'qualification.json'} if qualification else set())
    return required<=set(seal) and not check(directory)

def recorder_guard_only(old,new):
    """Recognize the sole historical recorder change, not arbitrary exclusions."""
    a=ast.parse(old);b=ast.parse(new)
    assignments=[n for n in b.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='OUTCOMES' for t in n.targets)]
    if len(assignments)!=1:return False
    if len(assignments[0].targets)!=1 or not isinstance(assignments[0].targets[0],ast.Name):return False
    value=assignments[0].value
    if not isinstance(value,ast.Call) or not isinstance(value.func,ast.Name) or value.func.id!='frozenset' or value.keywords or len(value.args)!=1 or not isinstance(value.args[0],ast.List):return False
    items=value.args[0].elts
    if not all(isinstance(v,ast.Constant) and isinstance(v.value,str) for v in items) or len(items)!=len(OUTCOMES) or {v.value for v in items}!=OUTCOMES:return False
    b.body.remove(assignments[0]);removed=0
    for n in ast.walk(b):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='finish':
            for stmt in list(n.body):
                if isinstance(stmt,ast.If) and ast.unparse(stmt.test)=="outcome not in OUTCOMES or outcome == 'RUNNING'":
                    expected=ast.parse("if outcome not in OUTCOMES or outcome=='RUNNING':\n raise ValueError('unknown or nonterminal experiment outcome: '+outcome)").body[0]
                    if ast.dump(stmt,include_attributes=False)!=ast.dump(expected,include_attributes=False):return False
                    n.body.remove(stmt);removed+=1
    return removed==1 and ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)

def inspect(sample):
    q=sample['selected_validation'];errors=[];annotations=[]
    def require(ok,why):
        if not ok:errors.append(why)
    path=ROOT/q['evidence'];commit=publication(path)
    require(anchored_seal(path,commit,qualification=True),'qualification seal and mandatory members bound to first Git publication')
    m=json.loads((path/'manifest.json').read_text());sealed=json.loads((path/'qualification.json').read_text())
    require(m['sample_id']==sample['id'] and m['experiment_id']==q['qualification_id'] and m['experiment_outcome']=='PASSED','qualification identity/outcome')
    require(all(k in q and q[k]==v for k,v in sealed.items()),'selected fields differ from sealed qualification')
    require(q['status']=='PASSED' and bool(q['checks']) and all(c.get('passed') is True for c in q['checks']),'qualification checks')
    require(q['sample_id']==sample['id'] and q['implementation']==sample['implementation'],'selected implementation')
    require(digest(ROOT/q['implementation'])==q['implementation_sha256'],'current implementation')
    require(bool(q['dependencies']) and sample['implementation'] in q['dependencies'],'nonempty dependency closure')
    for n,h in q['dependencies'].items():require((ROOT/n).is_file() and digest(ROOT/n)==h,'current compiled dependency '+n)
    def current_closure(directory):
        src=json.loads((directory/'source.json').read_text())
        for n,h in src['dependencies'].items():
            current=digest(ROOT/n) if (ROOT/n).is_file() else None
            if current==h:continue
            obj=ROOT/src['source_objects'][n]
            if n=='migration/rewrite/first-eight.json' and json.loads(obj.read_text())==json.loads((ROOT/n).read_text()):
                annotations.append('First-eight JSON formatting only; complete JSON equality checked')
            elif n=='tools/moat/experiment.py' and recorder_guard_only(obj.read_text(),(ROOT/n).read_text()):
                annotations.append('Recorder adds exact terminal-outcome validation only; remaining AST identical')
            elif (n,h,current) in METADATA_CHANGES:annotations.append(METADATA_CHANGES[(n,h,current)])
            else:require(False,'transitive current oracle/spec/compiled dependency '+n)
    current_closure(path)
    refs=set(q.get('evidence_references',[]))
    if q['kind'] in AGGREGATES:
        name,key,anchor=AGGREGATES[q['kind']];relative=Path('migration/reports')/name;report=ROOT/relative
        require(report.read_bytes()==published(relative,anchor),'aggregate exact immutable publication')
        group=json.loads(published(relative,anchor));profiles=group[key]
        require(group['status']=='PASSED' and q in profiles,'aggregate qualification matches selected profile')
        refs.update(group.get('evidence_references',[]))
    require(bool(refs),'nonempty evidence references')
    for ref in refs:
        directory=ROOT/ref
        require(anchored_seal(directory,commit),'referenced immutable seal '+ref)
        current_closure(directory)
    require(q.get('case_count',0)>0 and q['case_count']==len(q.get('case_ids',[])),'case contract')
    devices=q.get('devices',[]);require(bool(devices) and all(d['physical_id']!=3 for d in devices),'physical device identity')
    return dict(sample_id=sample['id'],status='PASSED' if not errors else 'FAILED',errors=errors,annotations=sorted(set(annotations)),qualification=q['evidence'],source_commit=q['source_commit'],publication_commit=commit,transitive_evidence_records=len(refs),dependencies=q['dependencies'])

def main():
    samples=json.loads((ROOT/'migration/samples.yaml').read_text())['samples'];rows=[inspect(s) for s in samples if s.get('reason_code')=='VALIDATED_MOAT_REWRITE' and s['status']=='PASSED']
    result=dict(status='PASSED' if rows and all(r['status']=='PASSED' for r in rows) else 'FAILED',qualified_samples=len(rows),scope='Current compiled numerical dependencies and immutable selected qualifications; historical attempts remain historical',rows=rows)
    write(ROOT/'migration/reports/rewrite-selected-proof-audit.json',result);print(json.dumps({k:v for k,v in result.items() if k!='rows'}));return int(result['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
